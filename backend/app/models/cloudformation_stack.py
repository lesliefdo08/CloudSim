"""
CloudFormation Stack Model
Represents an infrastructure stack created from templates
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class CloudFormationStack(Base):
    """CloudFormation Stack model."""
    
    __tablename__ = "cloudformation_stacks"
    
    # Stack identification
    stack_name = Column(String(128), primary_key=True)
    stack_id = Column(String(255), unique=True, nullable=False)
    account_id = Column(String(12), ForeignKey("iam_accounts.account_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Template
    template_body = Column(Text, nullable=False)  # Original template (JSON or YAML)
    template_format = Column(String(10), nullable=False)  # JSON or YAML
    
    # Stack status
    stack_status = Column(String(50), nullable=False)  # CREATE_IN_PROGRESS, CREATE_COMPLETE, CREATE_FAILED, etc.
    stack_status_reason = Column(Text, nullable=True)
    
    # Rollback configuration
    disable_rollback = Column(Boolean, nullable=False, default=False)
    rollback_configuration = Column(Text, nullable=True)  # JSON
    
    # Parameters
    parameters = Column(Text, nullable=True)  # JSON: {param_name: param_value}
    
    # Capabilities
    capabilities = Column(Text, nullable=True)  # JSON: list of capabilities (e.g., CAPABILITY_IAM)
    
    # Tags
    tags = Column(Text, nullable=True)  # JSON
    
    # Stack outputs
    outputs = Column(Text, nullable=True)  # JSON: {output_name: {value, description}}
    
    # Drift detection
    drift_status = Column(String(50), nullable=True)  # NOT_CHECKED, IN_SYNC, DRIFTED
    last_drift_check_timestamp = Column(DateTime, nullable=True)
    
    # Notifications
    notification_arns = Column(Text, nullable=True)  # JSON: list of SNS topic ARNs
    
    # Timeout
    timeout_in_minutes = Column(Integer, nullable=True)
    
    # Metadata
    creation_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated_time = Column(DateTime, nullable=True)
    deletion_time = Column(DateTime, nullable=True)
    
    # Parent stack (for nested stacks)
    parent_stack_id = Column(String(255), nullable=True)
    root_stack_id = Column(String(255), nullable=True)
    
    # Relationships
    resources = relationship("CloudFormationStackResource", back_populates="stack", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )


class CloudFormationStackResource(Base):
    """CloudFormation Stack Resource model."""
    
    __tablename__ = "cloudformation_stack_resources"
    
    # Resource identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    stack_name = Column(String(128), ForeignKey("cloudformation_stacks.stack_name", ondelete="CASCADE"), nullable=False, index=True)
    logical_resource_id = Column(String(255), nullable=False, index=True)
    physical_resource_id = Column(String(255), nullable=True)
    
    # Resource type
    resource_type = Column(String(255), nullable=False)  # AWS::EC2::Instance, AWS::S3::Bucket, etc.
    
    # Resource status
    resource_status = Column(String(50), nullable=False)  # CREATE_IN_PROGRESS, CREATE_COMPLETE, CREATE_FAILED, etc.
    resource_status_reason = Column(Text, nullable=True)
    
    # Resource properties
    resource_properties = Column(Text, nullable=True)  # JSON: original properties from template
    
    # Metadata
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated_timestamp = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    
    # Drift detection
    drift_status = Column(String(50), nullable=True)  # NOT_CHECKED, IN_SYNC, DRIFTED
    
    # Relationships
    stack = relationship("CloudFormationStack", back_populates="resources")
    
    # Unique constraint on logical resource ID within a stack
    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )
