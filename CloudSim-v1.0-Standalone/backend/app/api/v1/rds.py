"""
RDS API Routes
IAM-protected endpoints for RDS database instances and snapshots
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.iam_user import User
from app.services.rds_service import RDSService
from app.schemas.rds import *
from app.core.exceptions import ValidationError, ResourceNotFoundError
from app.api.v1.auth import get_current_user


router = APIRouter()
rds_service = RDSService()


# ==================== DB Instances ====================

@router.post("/rds/instances", response_model=CreateDBInstanceResponse)
def create_db_instance(
    request: CreateDBInstanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new RDS DB instance.
    Required IAM permission: rds:CreateDBInstance
    """
    try:
        db_instance = rds_service.create_db_instance(
            db,
            current_user.account_id,
            request.db_instance_identifier,
            request.db_instance_class,
            request.engine,
            request.master_username,
            request.master_user_password,
            request.allocated_storage,
            request.engine_version,
            request.db_name,
            request.port,
            request.backup_retention_period,
            request.publicly_accessible,
            request.multi_az,
            request.storage_type,
            request.tags
        )
        
        # Build response
        endpoint = None
        if db_instance.endpoint_address:
            endpoint = DBInstanceEndpoint(
                address=db_instance.endpoint_address,
                port=db_instance.endpoint_port
            )
        
        instance_info = DBInstanceInfo(
            db_instance_identifier=db_instance.db_instance_identifier,
            db_instance_arn=db_instance.db_instance_arn,
            db_instance_class=db_instance.db_instance_class,
            engine=db_instance.engine,
            engine_version=db_instance.engine_version,
            db_instance_status=db_instance.db_instance_status,
            master_username=db_instance.master_username,
            db_name=db_instance.db_name,
            endpoint=endpoint,
            allocated_storage=db_instance.allocated_storage,
            storage_type=db_instance.storage_type,
            publicly_accessible=db_instance.publicly_accessible,
            backup_retention_period=db_instance.backup_retention_period,
            availability_zone=db_instance.availability_zone,
            multi_az=db_instance.multi_az,
            created_at=db_instance.created_at
        )
        
        return CreateDBInstanceResponse(db_instance=instance_info)
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rds/instances/describe", response_model=DescribeDBInstancesResponse)
def describe_db_instances(
    request: DescribeDBInstancesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Describe RDS DB instances.
    Required IAM permission: rds:DescribeDBInstances
    """
    try:
        instances = rds_service.describe_db_instances(
            db,
            current_user.account_id,
            request.db_instance_identifier
        )
        
        instance_infos = []
        for inst in instances:
            endpoint = None
            if inst.endpoint_address:
                endpoint = DBInstanceEndpoint(
                    address=inst.endpoint_address,
                    port=inst.endpoint_port
                )
            
            instance_infos.append(DBInstanceInfo(
                db_instance_identifier=inst.db_instance_identifier,
                db_instance_arn=inst.db_instance_arn,
                db_instance_class=inst.db_instance_class,
                engine=inst.engine,
                engine_version=inst.engine_version,
                db_instance_status=inst.db_instance_status,
                master_username=inst.master_username,
                db_name=inst.db_name,
                endpoint=endpoint,
                allocated_storage=inst.allocated_storage,
                storage_type=inst.storage_type,
                publicly_accessible=inst.publicly_accessible,
                backup_retention_period=inst.backup_retention_period,
                availability_zone=inst.availability_zone,
                multi_az=inst.multi_az,
                created_at=inst.created_at
            ))
        
        return DescribeDBInstancesResponse(db_instances=instance_infos)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rds/instances", response_model=DeleteDBInstanceResponse)
def delete_db_instance(
    request: DeleteDBInstanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an RDS DB instance.
    Required IAM permission: rds:DeleteDBInstance
    """
    try:
        db_instance = rds_service.delete_db_instance(
            db,
            current_user.account_id,
            request.db_instance_identifier,
            request.skip_final_snapshot,
            request.final_db_snapshot_identifier
        )
        
        endpoint = None
        if db_instance.endpoint_address:
            endpoint = DBInstanceEndpoint(
                address=db_instance.endpoint_address,
                port=db_instance.endpoint_port
            )
        
        instance_info = DBInstanceInfo(
            db_instance_identifier=db_instance.db_instance_identifier,
            db_instance_arn=db_instance.db_instance_arn,
            db_instance_class=db_instance.db_instance_class,
            engine=db_instance.engine,
            engine_version=db_instance.engine_version,
            db_instance_status=db_instance.db_instance_status,
            master_username=db_instance.master_username,
            db_name=db_instance.db_name,
            endpoint=endpoint,
            allocated_storage=db_instance.allocated_storage,
            storage_type=db_instance.storage_type,
            publicly_accessible=db_instance.publicly_accessible,
            backup_retention_period=db_instance.backup_retention_period,
            availability_zone=db_instance.availability_zone,
            multi_az=db_instance.multi_az,
            created_at=db_instance.created_at
        )
        
        return DeleteDBInstanceResponse(db_instance=instance_info)
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rds/instances/start")
def start_db_instance(
    request: StartDBInstanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a stopped DB instance.
    Required IAM permission: rds:StartDBInstance
    """
    try:
        db_instance = rds_service.start_db_instance(
            db,
            current_user.account_id,
            request.db_instance_identifier
        )
        
        return {"message": f"DB instance '{request.db_instance_identifier}' started"}
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rds/instances/stop")
def stop_db_instance(
    request: StopDBInstanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stop a running DB instance.
    Required IAM permission: rds:StopDBInstance
    """
    try:
        db_instance = rds_service.stop_db_instance(
            db,
            current_user.account_id,
            request.db_instance_identifier
        )
        
        return {"message": f"DB instance '{request.db_instance_identifier}' stopped"}
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DB Snapshots ====================

@router.post("/rds/snapshots", response_model=CreateDBSnapshotResponse)
def create_db_snapshot(
    request: CreateDBSnapshotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a manual DB snapshot.
    Required IAM permission: rds:CreateDBSnapshot
    """
    try:
        snapshot = rds_service.create_db_snapshot(
            db,
            current_user.account_id,
            request.db_snapshot_identifier,
            request.db_instance_identifier,
            request.tags
        )
        
        snapshot_info = DBSnapshotInfo(
            db_snapshot_identifier=snapshot.db_snapshot_identifier,
            db_snapshot_arn=snapshot.db_snapshot_arn,
            db_instance_identifier=snapshot.db_instance_identifier,
            engine=snapshot.engine,
            engine_version=snapshot.engine_version,
            snapshot_type=snapshot.snapshot_type,
            status=snapshot.status,
            allocated_storage=snapshot.allocated_storage,
            storage_type=snapshot.storage_type,
            port=snapshot.port,
            master_username=snapshot.master_username,
            availability_zone=snapshot.availability_zone,
            snapshot_create_time=snapshot.snapshot_create_time,
            percent_progress=snapshot.percent_progress
        )
        
        return CreateDBSnapshotResponse(db_snapshot=snapshot_info)
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rds/snapshots/describe", response_model=DescribeDBSnapshotsResponse)
def describe_db_snapshots(
    request: DescribeDBSnapshotsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Describe DB snapshots.
    Required IAM permission: rds:DescribeDBSnapshots
    """
    try:
        snapshots = rds_service.describe_db_snapshots(
            db,
            current_user.account_id,
            request.db_snapshot_identifier,
            request.db_instance_identifier
        )
        
        snapshot_infos = []
        for snap in snapshots:
            snapshot_infos.append(DBSnapshotInfo(
                db_snapshot_identifier=snap.db_snapshot_identifier,
                db_snapshot_arn=snap.db_snapshot_arn,
                db_instance_identifier=snap.db_instance_identifier,
                engine=snap.engine,
                engine_version=snap.engine_version,
                snapshot_type=snap.snapshot_type,
                status=snap.status,
                allocated_storage=snap.allocated_storage,
                storage_type=snap.storage_type,
                port=snap.port,
                master_username=snap.master_username,
                availability_zone=snap.availability_zone,
                snapshot_create_time=snap.snapshot_create_time,
                percent_progress=snap.percent_progress
            ))
        
        return DescribeDBSnapshotsResponse(db_snapshots=snapshot_infos)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rds/snapshots", response_model=DeleteDBSnapshotResponse)
def delete_db_snapshot(
    request: DeleteDBSnapshotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a DB snapshot.
    Required IAM permission: rds:DeleteDBSnapshot
    """
    try:
        snapshot = rds_service.delete_db_snapshot(
            db,
            current_user.account_id,
            request.db_snapshot_identifier
        )
        
        snapshot_info = DBSnapshotInfo(
            db_snapshot_identifier=snapshot.db_snapshot_identifier,
            db_snapshot_arn=snapshot.db_snapshot_arn,
            db_instance_identifier=snapshot.db_instance_identifier,
            engine=snapshot.engine,
            engine_version=snapshot.engine_version,
            snapshot_type=snapshot.snapshot_type,
            status=snapshot.status,
            allocated_storage=snapshot.allocated_storage,
            storage_type=snapshot.storage_type,
            port=snapshot.port,
            master_username=snapshot.master_username,
            availability_zone=snapshot.availability_zone,
            snapshot_create_time=snapshot.snapshot_create_time,
            percent_progress=snapshot.percent_progress
        )
        
        return DeleteDBSnapshotResponse(db_snapshot=snapshot_info)
    
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rds/instances/restore", response_model=RestoreDBInstanceFromSnapshotResponse)
def restore_db_instance_from_snapshot(
    request: RestoreDBInstanceFromSnapshotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Restore a DB instance from a snapshot.
    Required IAM permission: rds:RestoreDBInstanceFromDBSnapshot
    """
    try:
        db_instance = rds_service.restore_db_instance_from_snapshot(
            db,
            current_user.account_id,
            request.db_instance_identifier,
            request.db_snapshot_identifier,
            request.db_instance_class,
            request.publicly_accessible
        )
        
        endpoint = None
        if db_instance.endpoint_address:
            endpoint = DBInstanceEndpoint(
                address=db_instance.endpoint_address,
                port=db_instance.endpoint_port
            )
        
        instance_info = DBInstanceInfo(
            db_instance_identifier=db_instance.db_instance_identifier,
            db_instance_arn=db_instance.db_instance_arn,
            db_instance_class=db_instance.db_instance_class,
            engine=db_instance.engine,
            engine_version=db_instance.engine_version,
            db_instance_status=db_instance.db_instance_status,
            master_username=db_instance.master_username,
            db_name=db_instance.db_name,
            endpoint=endpoint,
            allocated_storage=db_instance.allocated_storage,
            storage_type=db_instance.storage_type,
            publicly_accessible=db_instance.publicly_accessible,
            backup_retention_period=db_instance.backup_retention_period,
            availability_zone=db_instance.availability_zone,
            multi_az=db_instance.multi_az,
            created_at=db_instance.created_at
        )
        
        return RestoreDBInstanceFromSnapshotResponse(db_instance=instance_info)
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

