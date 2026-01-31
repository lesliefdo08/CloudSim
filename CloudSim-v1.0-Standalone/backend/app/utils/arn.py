"""
Amazon Resource Name (ARN) Utilities
Generate and parse AWS ARNs

ARN Format: arn:partition:service:region:account-id:resource-type/resource-id
Example: arn:aws:ec2:us-east-1:123456789012:instance/i-0123456789abcdef
"""

from dataclasses import dataclass
from typing import Optional
from app.config import settings


@dataclass
class ARN:
    """
    Parsed ARN components
    
    Format: arn:partition:service:region:account-id:resource-type/resource-id
    """
    partition: str  # aws, aws-cn, aws-us-gov
    service: str    # ec2, s3, iam, rds, etc.
    region: str     # us-east-1, us-west-2, etc. (empty for global services)
    account_id: str # 12-digit account number
    resource_type: str  # instance, volume, bucket, etc.
    resource_id: str    # Actual resource identifier
    
    def __str__(self) -> str:
        """Convert ARN back to string format"""
        if self.resource_type:
            resource = f"{self.resource_type}/{self.resource_id}"
        else:
            resource = self.resource_id
        
        return f"arn:{self.partition}:{self.service}:{self.region}:{self.account_id}:{resource}"


def build_arn(
    service: str,
    resource_type: str,
    resource_id: str,
    region: Optional[str] = None,
    account_id: Optional[str] = None,
    partition: str = "aws"
) -> str:
    """
    Build ARN string from components
    
    Args:
        service: AWS service name (ec2, s3, iam, etc.)
        resource_type: Type of resource (instance, volume, bucket, etc.)
        resource_id: Unique resource identifier
        region: AWS region (optional, empty for global services like IAM)
        account_id: AWS account ID (defaults to configured account)
        partition: AWS partition (default: aws)
    
    Returns:
        Formatted ARN string
    
    Examples:
        build_arn("ec2", "instance", "i-0123456789")
        # arn:aws:ec2:us-east-1:123456789012:instance/i-0123456789
        
        build_arn("s3", "", "my-bucket")
        # arn:aws:s3:::my-bucket
        
        build_arn("iam", "user", "alice", region="")
        # arn:aws:iam::123456789012:user/alice
    """
    region = region if region is not None else settings.DEFAULT_REGION
    account_id = account_id or settings.DEFAULT_ACCOUNT_ID
    
    if resource_type:
        resource = f"{resource_type}/{resource_id}"
    else:
        resource = resource_id
    
    return f"arn:{partition}:{service}:{region}:{account_id}:{resource}"


def parse_arn(arn_string: str) -> ARN:
    """
    Parse ARN string into components
    
    Args:
        arn_string: ARN to parse
    
    Returns:
        ARN dataclass with parsed components
    
    Raises:
        ValueError: If ARN format is invalid
    
    Example:
        arn = parse_arn("arn:aws:ec2:us-east-1:123456789012:instance/i-0123456789")
        print(arn.service)  # ec2
        print(arn.resource_id)  # i-0123456789
    """
    parts = arn_string.split(":", 5)
    
    if len(parts) != 6 or parts[0] != "arn":
        raise ValueError(f"Invalid ARN format: {arn_string}")
    
    partition, service, region, account_id, resource = parts[1:]
    
    # Parse resource type and ID
    if "/" in resource:
        resource_type, resource_id = resource.split("/", 1)
    else:
        resource_type = ""
        resource_id = resource
    
    return ARN(
        partition=partition,
        service=service,
        region=region,
        account_id=account_id,
        resource_type=resource_type,
        resource_id=resource_id
    )


# Service-specific ARN builders

def build_instance_arn(instance_id: str, region: Optional[str] = None) -> str:
    """Build EC2 instance ARN"""
    return build_arn("ec2", "instance", instance_id, region)


def build_volume_arn(volume_id: str, region: Optional[str] = None) -> str:
    """Build EBS volume ARN"""
    return build_arn("ec2", "volume", volume_id, region)


def build_vpc_arn(vpc_id: str, region: Optional[str] = None) -> str:
    """Build VPC ARN"""
    return build_arn("ec2", "vpc", vpc_id, region)


def build_security_group_arn(sg_id: str, region: Optional[str] = None) -> str:
    """Build security group ARN"""
    return build_arn("ec2", "security-group", sg_id, region)


def build_s3_bucket_arn(bucket_name: str) -> str:
    """
    Build S3 bucket ARN
    Note: S3 is global, no region or account in ARN
    """
    return f"arn:aws:s3:::{bucket_name}"


def build_s3_object_arn(bucket_name: str, object_key: str) -> str:
    """Build S3 object ARN"""
    return f"arn:aws:s3:::{bucket_name}/{object_key}"


def build_iam_user_arn(username: str) -> str:
    """Build IAM user ARN (IAM is global)"""
    return build_arn("iam", "user", username, region="")


def build_iam_role_arn(role_name: str) -> str:
    """Build IAM role ARN (IAM is global)"""
    return build_arn("iam", "role", role_name, region="")


def build_iam_policy_arn(policy_name: str) -> str:
    """Build IAM policy ARN (IAM is global)"""
    return build_arn("iam", "policy", policy_name, region="")


def build_rds_instance_arn(db_instance_id: str, region: Optional[str] = None) -> str:
    """Build RDS DB instance ARN"""
    return build_arn("rds", "db", db_instance_id, region)


def build_lambda_function_arn(function_name: str, region: Optional[str] = None) -> str:
    """Build Lambda function ARN"""
    return build_arn("lambda", "function", function_name, region)
