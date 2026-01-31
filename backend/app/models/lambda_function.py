"""
Lambda Function Model
Represents a serverless function with runtime isolation
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Boolean
from datetime import datetime

from app.core.database import Base


class LambdaFunction(Base):
    """Lambda Function model."""
    
    __tablename__ = "lambda_functions"
    
    # Function identification
    function_name = Column(String(64), primary_key=True)
    function_arn = Column(String(255), unique=True, nullable=False)
    account_id = Column(String(12), ForeignKey("iam_accounts.account_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Runtime configuration
    runtime = Column(String(50), nullable=False)  # python3.9, python3.10, python3.11, nodejs18.x, nodejs20.x
    handler = Column(String(128), nullable=False)  # module.function_name (e.g., index.handler)
    
    # Code storage
    code_storage_location = Column(String(255), nullable=False)  # Path to code ZIP or directory
    code_sha256 = Column(String(64), nullable=False)  # SHA256 hash of code
    code_size = Column(Integer, nullable=False)  # Bytes
    
    # Function configuration
    description = Column(Text, nullable=True)
    timeout = Column(Integer, nullable=False, default=3)  # Seconds (1-900)
    memory_size = Column(Integer, nullable=False, default=128)  # MB (128-10240)
    
    # Environment
    environment_variables = Column(Text, nullable=True)  # JSON
    
    # Execution role (IAM)
    role = Column(String(255), nullable=False)  # ARN of execution role
    
    # Networking (VPC)
    vpc_config = Column(Text, nullable=True)  # JSON: {subnet_ids, security_group_ids}
    
    # State
    state = Column(String(50), nullable=False, default="Active")  # Active, Pending, Inactive, Failed
    state_reason = Column(Text, nullable=True)
    state_reason_code = Column(String(50), nullable=True)
    
    # Last update
    last_modified = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_update_status = Column(String(50), nullable=False, default="Successful")
    
    # Versioning
    version = Column(String(10), nullable=False, default="$LATEST")
    
    # Layers (not fully implemented)
    layers = Column(Text, nullable=True)  # JSON array of layer ARNs
    
    # Container information (for runtime isolation)
    container_image = Column(String(255), nullable=True)  # Docker image for runtime
    
    # Metrics
    invocations = Column(Integer, nullable=False, default=0)  # Total invocations
    errors = Column(Integer, nullable=False, default=0)  # Total errors
    
    # Tags
    tags = Column(Text, nullable=True)  # JSON
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )
