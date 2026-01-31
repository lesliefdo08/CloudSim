"""
RDS Schemas
Request/response models for RDS APIs
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


# ==================== DB Instances ====================

class CreateDBInstanceRequest(BaseModel):
    """Request to create a DB instance."""
    db_instance_identifier: str = Field(..., min_length=1, max_length=63)
    db_instance_class: str = Field(..., description="db.t2.micro, db.t2.small, etc.")
    engine: str = Field(..., description="mysql or postgres")
    master_username: str = Field(..., min_length=1, max_length=63)
    master_user_password: str = Field(..., min_length=8)
    allocated_storage: int = Field(20, ge=20, le=65536, description="Storage in GB")
    engine_version: Optional[str] = None
    db_name: Optional[str] = Field(None, max_length=64)
    port: Optional[int] = None
    backup_retention_period: int = Field(7, ge=0, le=35)
    publicly_accessible: bool = False
    multi_az: bool = False
    storage_type: str = Field("gp2", description="gp2, io1, etc.")
    tags: Optional[Dict[str, str]] = None


class DBInstanceEndpoint(BaseModel):
    """DB instance endpoint."""
    address: str
    port: int


class DBInstanceInfo(BaseModel):
    """DB instance information."""
    db_instance_identifier: str
    db_instance_arn: str
    db_instance_class: str
    engine: str
    engine_version: str
    db_instance_status: str
    master_username: str
    db_name: Optional[str]
    endpoint: Optional[DBInstanceEndpoint]
    allocated_storage: int
    storage_type: str
    publicly_accessible: bool
    backup_retention_period: int
    availability_zone: Optional[str]
    multi_az: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreateDBInstanceResponse(BaseModel):
    """Response from creating a DB instance."""
    db_instance: DBInstanceInfo


class DescribeDBInstancesRequest(BaseModel):
    """Request to describe DB instances."""
    db_instance_identifier: Optional[str] = None


class DescribeDBInstancesResponse(BaseModel):
    """Response from describing DB instances."""
    db_instances: List[DBInstanceInfo]


class DeleteDBInstanceRequest(BaseModel):
    """Request to delete a DB instance."""
    db_instance_identifier: str
    skip_final_snapshot: bool = False
    final_db_snapshot_identifier: Optional[str] = None


class DeleteDBInstanceResponse(BaseModel):
    """Response from deleting a DB instance."""
    db_instance: DBInstanceInfo


class StartDBInstanceRequest(BaseModel):
    """Request to start a DB instance."""
    db_instance_identifier: str


class StopDBInstanceRequest(BaseModel):
    """Request to stop a DB instance."""
    db_instance_identifier: str


# ==================== DB Snapshots ====================

class CreateDBSnapshotRequest(BaseModel):
    """Request to create a DB snapshot."""
    db_snapshot_identifier: str = Field(..., min_length=1, max_length=255)
    db_instance_identifier: str = Field(..., min_length=1, max_length=63)
    tags: Optional[Dict[str, str]] = None


class DBSnapshotInfo(BaseModel):
    """DB snapshot information."""
    db_snapshot_identifier: str
    db_snapshot_arn: str
    db_instance_identifier: str
    engine: str
    engine_version: str
    snapshot_type: str
    status: str
    allocated_storage: int
    storage_type: str
    port: int
    master_username: str
    availability_zone: Optional[str]
    snapshot_create_time: datetime
    percent_progress: int
    
    class Config:
        from_attributes = True


class CreateDBSnapshotResponse(BaseModel):
    """Response from creating a DB snapshot."""
    db_snapshot: DBSnapshotInfo


class DescribeDBSnapshotsRequest(BaseModel):
    """Request to describe DB snapshots."""
    db_snapshot_identifier: Optional[str] = None
    db_instance_identifier: Optional[str] = None


class DescribeDBSnapshotsResponse(BaseModel):
    """Response from describing DB snapshots."""
    db_snapshots: List[DBSnapshotInfo]


class DeleteDBSnapshotRequest(BaseModel):
    """Request to delete a DB snapshot."""
    db_snapshot_identifier: str


class DeleteDBSnapshotResponse(BaseModel):
    """Response from deleting a DB snapshot."""
    db_snapshot: DBSnapshotInfo


class RestoreDBInstanceFromSnapshotRequest(BaseModel):
    """Request to restore a DB instance from snapshot."""
    db_instance_identifier: str = Field(..., min_length=1, max_length=63)
    db_snapshot_identifier: str = Field(..., min_length=1, max_length=255)
    db_instance_class: Optional[str] = None
    publicly_accessible: Optional[bool] = None


class RestoreDBInstanceFromSnapshotResponse(BaseModel):
    """Response from restoring a DB instance."""
    db_instance: DBInstanceInfo
