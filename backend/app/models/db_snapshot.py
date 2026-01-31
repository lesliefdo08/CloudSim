"""
RDS DB Snapshot Model
Represents a database backup snapshot
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class DBSnapshot(Base):
    """RDS Database Snapshot model."""
    
    __tablename__ = "db_snapshots"
    
    # Snapshot identification
    db_snapshot_identifier = Column(String(255), primary_key=True)
    db_snapshot_arn = Column(String(255), unique=True, nullable=False)
    account_id = Column(String(12), ForeignKey("iam_accounts.account_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Source instance
    db_instance_identifier = Column(String(63), ForeignKey("db_instances.db_instance_identifier", ondelete="CASCADE"), nullable=False, index=True)
    
    # Engine information
    engine = Column(String(50), nullable=False)
    engine_version = Column(String(50), nullable=False)
    
    # Snapshot configuration
    snapshot_type = Column(String(50), nullable=False)  # manual, automated
    status = Column(String(50), nullable=False, default="creating")
    # States: creating, available, copying, deleting
    
    # Storage
    allocated_storage = Column(Integer, nullable=False)  # GB
    storage_type = Column(String(50), nullable=False)
    
    # Port
    port = Column(Integer, nullable=False)
    
    # Backup details
    master_username = Column(String(63), nullable=False)
    availability_zone = Column(String(50), nullable=True)
    vpc_id = Column(String(21), nullable=True)
    
    # Snapshot metadata
    snapshot_create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    percent_progress = Column(Integer, nullable=False, default=0)
    
    # Docker volume information
    volume_name = Column(String(255), nullable=True)  # Docker volume for snapshot data
    
    # Tags
    tags = Column(Text, nullable=True)  # JSON
    
    # Relationships
    db_instance = relationship("DBInstance", back_populates="snapshots")
    
    # Indexes
    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )
