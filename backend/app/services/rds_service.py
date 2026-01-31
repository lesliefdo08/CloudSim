"""
RDS Service
Manages MySQL and PostgreSQL database instances via Docker
"""
import json
import secrets
import string
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
import docker

from app.models.db_instance import DBInstance
from app.models.db_snapshot import DBSnapshot
from app.core.exceptions import ValidationError, ResourceNotFoundError
from app.core.resource_ids import generate_id, ResourceType


class RDSService:
    """Service for RDS operations."""
    
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
        except Exception:
            self.docker_client = None
        self.network_name = "cloudsim-rds-network"
        if self.docker_client:
            self._ensure_network()
    
    def _ensure_network(self):
        """Ensure RDS Docker network exists."""
        if not self.docker_client:
            return
        try:
            self.docker_client.networks.get(self.network_name)
        except docker.errors.NotFound:
            self.docker_client.networks.create(
                self.network_name,
                driver="bridge"
            )
    
    # ==================== DB Instance Operations ====================
    
    def create_db_instance(
        self,
        db: Session,
        account_id: str,
        db_instance_identifier: str,
        db_instance_class: str,
        engine: str,
        master_username: str,
        master_user_password: str,
        allocated_storage: int = 20,
        engine_version: Optional[str] = None,
        db_name: Optional[str] = None,
        port: Optional[int] = None,
        backup_retention_period: int = 7,
        publicly_accessible: bool = False,
        multi_az: bool = False,
        storage_type: str = "gp2",
        tags: Optional[Dict[str, str]] = None
    ) -> DBInstance:
        """
        Create a new RDS DB instance.
        
        Args:
            db: Database session
            account_id: Account ID
            db_instance_identifier: Unique identifier
            db_instance_class: Instance class (db.t2.micro, etc.)
            engine: Database engine (mysql, postgres)
            master_username: Master user
            master_user_password: Master password
            allocated_storage: Storage in GB
            engine_version: Engine version
            db_name: Initial database name
            port: Port number
            backup_retention_period: Days to retain backups
            publicly_accessible: Whether publicly accessible
            multi_az: Multi-AZ deployment
            storage_type: Storage type
            tags: Resource tags
        
        Returns:
            Created DB instance
        """
        # Validate
        if len(db_instance_identifier) < 1 or len(db_instance_identifier) > 63:
            raise ValidationError("DB instance identifier must be 1-63 characters")
        
        # Check if exists
        existing = db.query(DBInstance).filter(
            DBInstance.db_instance_identifier == db_instance_identifier,
            DBInstance.account_id == account_id
        ).first()
        
        if existing:
            raise ValidationError(f"DB instance '{db_instance_identifier}' already exists")
        
        # Validate engine
        valid_engines = ["mysql", "postgres"]
        if engine not in valid_engines:
            raise ValidationError(f"Invalid engine: {engine}. Must be one of {valid_engines}")
        
        # Set defaults
        if not engine_version:
            engine_version = "8.0" if engine == "mysql" else "15"
        
        if not port:
            port = 3306 if engine == "mysql" else 5432
        
        if not db_name:
            db_name = "mydb"
        
        # Validate instance class
        valid_classes = ["db.t2.micro", "db.t2.small", "db.t2.medium", "db.t3.micro", "db.t3.small"]
        if db_instance_class not in valid_classes:
            raise ValidationError(f"Invalid instance class: {db_instance_class}")
        
        # Create Docker container
        container_name = f"rds-{db_instance_identifier}"
        
        try:
            # Determine Docker image
            if engine == "mysql":
                image = f"mysql:{engine_version}"
                env_vars = {
                    "MYSQL_ROOT_PASSWORD": master_user_password,
                    "MYSQL_DATABASE": db_name,
                    "MYSQL_USER": master_username if master_username != "root" else "admin",
                    "MYSQL_PASSWORD": master_user_password
                }
            else:  # postgres
                image = f"postgres:{engine_version}"
                env_vars = {
                    "POSTGRES_USER": master_username,
                    "POSTGRES_PASSWORD": master_user_password,
                    "POSTGRES_DB": db_name
                }
            
            # Create volume for persistent storage
            volume_name = f"rds-{db_instance_identifier}-data"
            try:
                self.docker_client.volumes.create(name=volume_name)
            except docker.errors.APIError:
                pass  # Volume might already exist
            
            # Mount path based on engine
            mount_path = "/var/lib/mysql" if engine == "mysql" else "/var/lib/postgresql/data"
            
            # Create container
            container = self.docker_client.containers.run(
                image,
                name=container_name,
                environment=env_vars,
                volumes={volume_name: {"bind": mount_path, "mode": "rw"}},
                network=self.network_name,
                detach=True,
                ports={f"{port}/tcp": port} if publicly_accessible else None
            )
            
            # Get endpoint
            if publicly_accessible:
                endpoint_address = "localhost"
                endpoint_port = port
            else:
                endpoint_address = container_name
                endpoint_port = port
            
        except Exception as e:
            raise ValidationError(f"Failed to create DB instance: {str(e)}")
        
        # Create DB instance record
        db_instance_arn = f"arn:aws:rds:us-east-1:{account_id}:db:{db_instance_identifier}"
        
        db_instance = DBInstance(
            db_instance_identifier=db_instance_identifier,
            db_instance_arn=db_instance_arn,
            account_id=account_id,
            engine=engine,
            engine_version=engine_version,
            db_instance_class=db_instance_class,
            master_username=master_username,
            master_user_password=master_user_password,
            db_name=db_name,
            port=port,
            allocated_storage=allocated_storage,
            storage_type=storage_type,
            publicly_accessible=publicly_accessible,
            endpoint_address=endpoint_address,
            endpoint_port=endpoint_port,
            backup_retention_period=backup_retention_period,
            db_instance_status="creating",
            container_id=container.id,
            container_name=container_name,
            multi_az=multi_az,
            availability_zone="us-east-1a",
            tags=json.dumps(tags) if tags else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_instance)
        db.commit()
        db.refresh(db_instance)
        
        # Update status to available after container is running
        try:
            container.reload()
            if container.status == "running":
                db_instance.db_instance_status = "available"
                db.commit()
        except:
            pass
        
        return db_instance
    
    def describe_db_instances(
        self,
        db: Session,
        account_id: str,
        db_instance_identifier: Optional[str] = None
    ) -> List[DBInstance]:
        """List DB instances."""
        query = db.query(DBInstance).filter(
            DBInstance.account_id == account_id,
            DBInstance.db_instance_status != "deleted"
        )
        
        if db_instance_identifier:
            query = query.filter(DBInstance.db_instance_identifier == db_instance_identifier)
        
        return query.all()
    
    def delete_db_instance(
        self,
        db: Session,
        account_id: str,
        db_instance_identifier: str,
        skip_final_snapshot: bool = False,
        final_db_snapshot_identifier: Optional[str] = None
    ) -> DBInstance:
        """
        Delete a DB instance.
        
        Args:
            db: Database session
            account_id: Account ID
            db_instance_identifier: Instance identifier
            skip_final_snapshot: Whether to skip final snapshot
            final_db_snapshot_identifier: Final snapshot name
        
        Returns:
            Deleted DB instance
        """
        db_instance = db.query(DBInstance).filter(
            DBInstance.db_instance_identifier == db_instance_identifier,
            DBInstance.account_id == account_id
        ).first()
        
        if not db_instance:
            raise ResourceNotFoundError(f"DB instance '{db_instance_identifier}' not found")
        
        if db_instance.deletion_protection:
            raise ValidationError("Cannot delete instance with deletion protection enabled")
        
        # Create final snapshot if requested
        if not skip_final_snapshot:
            if not final_db_snapshot_identifier:
                final_db_snapshot_identifier = f"{db_instance_identifier}-final-{int(datetime.utcnow().timestamp())}"
            
            self.create_db_snapshot(
                db,
                account_id,
                final_db_snapshot_identifier,
                db_instance_identifier
            )
        
        # Stop and remove Docker container
        try:
            container = self.docker_client.containers.get(db_instance.container_id)
            container.stop()
            container.remove()
        except docker.errors.NotFound:
            pass
        except Exception as e:
            print(f"Error removing container: {str(e)}")
        
        # Update status
        db_instance.db_instance_status = "deleted"
        db_instance.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_instance)
        
        return db_instance
    
    def start_db_instance(
        self,
        db: Session,
        account_id: str,
        db_instance_identifier: str
    ) -> DBInstance:
        """Start a stopped DB instance."""
        db_instance = db.query(DBInstance).filter(
            DBInstance.db_instance_identifier == db_instance_identifier,
            DBInstance.account_id == account_id
        ).first()
        
        if not db_instance:
            raise ResourceNotFoundError(f"DB instance '{db_instance_identifier}' not found")
        
        if db_instance.db_instance_status != "stopped":
            raise ValidationError(f"Cannot start instance in state: {db_instance.db_instance_status}")
        
        try:
            container = self.docker_client.containers.get(db_instance.container_id)
            container.start()
            
            db_instance.db_instance_status = "available"
            db_instance.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_instance)
        except docker.errors.NotFound:
            raise ResourceNotFoundError("Container not found")
        
        return db_instance
    
    def stop_db_instance(
        self,
        db: Session,
        account_id: str,
        db_instance_identifier: str
    ) -> DBInstance:
        """Stop a running DB instance."""
        db_instance = db.query(DBInstance).filter(
            DBInstance.db_instance_identifier == db_instance_identifier,
            DBInstance.account_id == account_id
        ).first()
        
        if not db_instance:
            raise ResourceNotFoundError(f"DB instance '{db_instance_identifier}' not found")
        
        if db_instance.db_instance_status != "available":
            raise ValidationError(f"Cannot stop instance in state: {db_instance.db_instance_status}")
        
        try:
            container = self.docker_client.containers.get(db_instance.container_id)
            container.stop()
            
            db_instance.db_instance_status = "stopped"
            db_instance.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_instance)
        except docker.errors.NotFound:
            raise ResourceNotFoundError("Container not found")
        
        return db_instance
    
    # ==================== Snapshot Operations ====================
    
    def create_db_snapshot(
        self,
        db: Session,
        account_id: str,
        db_snapshot_identifier: str,
        db_instance_identifier: str,
        tags: Optional[Dict[str, str]] = None
    ) -> DBSnapshot:
        """
        Create a manual snapshot of a DB instance.
        
        Args:
            db: Database session
            account_id: Account ID
            db_snapshot_identifier: Snapshot identifier
            db_instance_identifier: Source instance identifier
            tags: Resource tags
        
        Returns:
            Created snapshot
        """
        # Get source instance
        db_instance = db.query(DBInstance).filter(
            DBInstance.db_instance_identifier == db_instance_identifier,
            DBInstance.account_id == account_id
        ).first()
        
        if not db_instance:
            raise ResourceNotFoundError(f"DB instance '{db_instance_identifier}' not found")
        
        # Check if snapshot exists
        existing = db.query(DBSnapshot).filter(
            DBSnapshot.db_snapshot_identifier == db_snapshot_identifier,
            DBSnapshot.account_id == account_id
        ).first()
        
        if existing:
            raise ValidationError(f"Snapshot '{db_snapshot_identifier}' already exists")
        
        # Create snapshot volume (copy of data volume)
        volume_name = f"rds-snapshot-{db_snapshot_identifier}"
        
        try:
            # In real AWS, this would be a proper snapshot
            # In CloudSim, we create a new volume as a "snapshot"
            self.docker_client.volumes.create(name=volume_name)
            
            # Copy data from instance volume (simplified)
            # In production, would use Docker volume copy or database dump
            
        except Exception as e:
            raise ValidationError(f"Failed to create snapshot: {str(e)}")
        
        # Create snapshot record
        snapshot_arn = f"arn:aws:rds:us-east-1:{account_id}:snapshot:{db_snapshot_identifier}"
        
        snapshot = DBSnapshot(
            db_snapshot_identifier=db_snapshot_identifier,
            db_snapshot_arn=snapshot_arn,
            account_id=account_id,
            db_instance_identifier=db_instance_identifier,
            engine=db_instance.engine,
            engine_version=db_instance.engine_version,
            snapshot_type="manual",
            status="creating",
            allocated_storage=db_instance.allocated_storage,
            storage_type=db_instance.storage_type,
            port=db_instance.port,
            master_username=db_instance.master_username,
            availability_zone=db_instance.availability_zone,
            vpc_id=db_instance.vpc_id,
            volume_name=volume_name,
            tags=json.dumps(tags) if tags else None,
            snapshot_create_time=datetime.utcnow(),
            percent_progress=100
        )
        
        snapshot.status = "available"
        
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        
        return snapshot
    
    def describe_db_snapshots(
        self,
        db: Session,
        account_id: str,
        db_snapshot_identifier: Optional[str] = None,
        db_instance_identifier: Optional[str] = None
    ) -> List[DBSnapshot]:
        """List DB snapshots."""
        query = db.query(DBSnapshot).filter(
            DBSnapshot.account_id == account_id
        )
        
        if db_snapshot_identifier:
            query = query.filter(DBSnapshot.db_snapshot_identifier == db_snapshot_identifier)
        
        if db_instance_identifier:
            query = query.filter(DBSnapshot.db_instance_identifier == db_instance_identifier)
        
        return query.all()
    
    def delete_db_snapshot(
        self,
        db: Session,
        account_id: str,
        db_snapshot_identifier: str
    ) -> DBSnapshot:
        """Delete a DB snapshot."""
        snapshot = db.query(DBSnapshot).filter(
            DBSnapshot.db_snapshot_identifier == db_snapshot_identifier,
            DBSnapshot.account_id == account_id
        ).first()
        
        if not snapshot:
            raise ResourceNotFoundError(f"Snapshot '{db_snapshot_identifier}' not found")
        
        # Remove Docker volume
        try:
            volume = self.docker_client.volumes.get(snapshot.volume_name)
            volume.remove()
        except docker.errors.NotFound:
            pass
        except Exception as e:
            print(f"Error removing volume: {str(e)}")
        
        # Delete snapshot record
        db.delete(snapshot)
        db.commit()
        
        return snapshot
    
    def restore_db_instance_from_snapshot(
        self,
        db: Session,
        account_id: str,
        db_instance_identifier: str,
        db_snapshot_identifier: str,
        db_instance_class: Optional[str] = None,
        publicly_accessible: Optional[bool] = None
    ) -> DBInstance:
        """
        Restore a DB instance from a snapshot.
        
        Args:
            db: Database session
            account_id: Account ID
            db_instance_identifier: New instance identifier
            db_snapshot_identifier: Source snapshot identifier
            db_instance_class: Instance class (optional)
            publicly_accessible: Whether publicly accessible (optional)
        
        Returns:
            Restored DB instance
        """
        # Get source snapshot
        snapshot = db.query(DBSnapshot).filter(
            DBSnapshot.db_snapshot_identifier == db_snapshot_identifier,
            DBSnapshot.account_id == account_id
        ).first()
        
        if not snapshot:
            raise ResourceNotFoundError(f"Snapshot '{db_snapshot_identifier}' not found")
        
        # Get original instance for defaults
        source_instance = db.query(DBInstance).filter(
            DBInstance.db_instance_identifier == snapshot.db_instance_identifier
        ).first()
        
        # Use snapshot/source values
        engine = snapshot.engine
        engine_version = snapshot.engine_version
        port = snapshot.port
        allocated_storage = snapshot.allocated_storage
        storage_type = snapshot.storage_type
        master_username = snapshot.master_username
        
        if not db_instance_class and source_instance:
            db_instance_class = source_instance.db_instance_class
        elif not db_instance_class:
            db_instance_class = "db.t2.micro"
        
        if publicly_accessible is None and source_instance:
            publicly_accessible = source_instance.publicly_accessible
        elif publicly_accessible is None:
            publicly_accessible = False
        
        # Generate temporary password
        master_user_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        
        # Create new instance (reusing create logic)
        return self.create_db_instance(
            db,
            account_id,
            db_instance_identifier,
            db_instance_class,
            engine,
            master_username,
            master_user_password,
            allocated_storage=allocated_storage,
            engine_version=engine_version,
            port=port,
            publicly_accessible=publicly_accessible,
            storage_type=storage_type
        )


