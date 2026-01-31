"""
RDS DB Instance Model
Represents a managed database instance (MySQL/PostgreSQL)
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class DBInstance(Base):
    """RDS Database Instance model."""
    
    __tablename__ = "db_instances"
    
    # Instance identification
    db_instance_identifier = Column(String(63), primary_key=True)
    db_instance_arn = Column(String(255), unique=True, nullable=False)
    account_id = Column(String(12), ForeignKey("iam_accounts.account_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Engine configuration
    engine = Column(String(50), nullable=False)  # mysql, postgres
    engine_version = Column(String(50), nullable=False)
    db_instance_class = Column(String(50), nullable=False)  # db.t2.micro, db.t2.small, etc.
    
    # Database configuration
    master_username = Column(String(63), nullable=False)
    master_user_password = Column(String(255), nullable=False)  # Encrypted in real AWS
    db_name = Column(String(64), nullable=True)  # Initial database name
    port = Column(Integer, nullable=False)
    
    # Storage
    allocated_storage = Column(Integer, nullable=False)  # GB
    storage_type = Column(String(50), nullable=False, default="gp2")  # gp2, io1, etc.
    storage_encrypted = Column(Boolean, nullable=False, default=False)
    
    # Networking
    vpc_id = Column(String(21), nullable=True)
    subnet_group = Column(String(255), nullable=True)
    publicly_accessible = Column(Boolean, nullable=False, default=False)
    endpoint_address = Column(String(255), nullable=True)
    endpoint_port = Column(Integer, nullable=True)
    
    # Backup configuration
    backup_retention_period = Column(Integer, nullable=False, default=7)  # Days
    preferred_backup_window = Column(String(50), nullable=True)  # HH:MM-HH:MM
    preferred_maintenance_window = Column(String(50), nullable=True)
    
    # State
    db_instance_status = Column(String(50), nullable=False, default="creating")
    # States: creating, available, modifying, deleting, deleted, failed, backing-up, restoring
    
    # Container information
    container_id = Column(String(64), nullable=True)
    container_name = Column(String(255), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deletion_protection = Column(Boolean, nullable=False, default=False)
    
    # Multi-AZ (simplified in CloudSim)
    multi_az = Column(Boolean, nullable=False, default=False)
    availability_zone = Column(String(50), nullable=True)
    
    # Monitoring
    enhanced_monitoring_arn = Column(String(255), nullable=True)
    performance_insights_enabled = Column(Boolean, nullable=False, default=False)
    
    # Tags
    tags = Column(Text, nullable=True)  # JSON
    
    # Relationships
    snapshots = relationship("DBSnapshot", back_populates="db_instance", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )
