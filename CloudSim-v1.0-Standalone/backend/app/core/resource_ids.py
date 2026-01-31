"""
AWS Resource ID Generation
Follows AWS naming conventions for all resource types
"""

import secrets
import string
from enum import Enum


class ResourceType(str, Enum):
    """AWS resource type prefixes"""
    
    # EC2
    INSTANCE = "i"
    AMI = "ami"
    SNAPSHOT = "snap"
    VOLUME = "vol"
    SECURITY_GROUP = "sg"
    SECURITY_GROUP_RULE = "sgr"
    KEY_PAIR = "key"
    NETWORK_INTERFACE = "eni"
    ELASTIC_IP = "eipalloc"
    PLACEMENT_GROUP = "pg"
    
    # VPC
    VPC = "vpc"
    SUBNET = "subnet"
    ROUTE_TABLE = "rtb"
    INTERNET_GATEWAY = "igw"
    NAT_GATEWAY = "nat"
    VPC_PEERING = "pcx"
    NETWORK_ACL = "acl"
    VPC_ENDPOINT = "vpce"
    DHCP_OPTIONS = "dopt"
    
    # ELB
    LOAD_BALANCER = "lb"
    TARGET_GROUP = "tg"
    LISTENER = "lsnr"
    
    # IAM (no prefix, just names)
    USER = "user"
    GROUP = "group"
    ROLE = "role"
    POLICY = "policy"
    ACCESS_KEY = "AKIA"  # Access Key ID prefix
    
    # Lambda
    LAMBDA_FUNCTION = "lambda"
    LAYER = "layer"
    
    # RDS
    DB_INSTANCE = "db"
    DB_SNAPSHOT = "rds"
    DB_CLUSTER = "cluster"
    
    # S3 (bucket names are user-defined)
    BUCKET = "bucket"
    S3_OBJECT = "obj"
    
    # CloudWatch
    ALARM = "alarm"
    LOG_GROUP = "lg"
    LOG_STREAM = "ls"
    CLOUDWATCH_METRIC = "cwm"


def generate_resource_id(resource_type: ResourceType, length: int = 17) -> str:
    """
    Generate AWS-style resource ID
    
    Format: {prefix}-{random_hex}
    Example: i-0f1ac123456789a, vpc-1a2b3c4d5e6f7
    
    Args:
        resource_type: Type of resource (determines prefix)
        length: Length of random portion (default 17 for EC2)
    
    Returns:
        Formatted resource ID
    """
    # Special case: Access keys use uppercase alphanumeric
    if resource_type == ResourceType.ACCESS_KEY:
        random_part = ''.join(
            secrets.choice(string.ascii_uppercase + string.digits)
            for _ in range(16)
        )
        return f"{resource_type.value}{random_part}"
    
    # Standard format: prefix-randomhex
    random_hex = secrets.token_hex(length // 2)[:length]
    return f"{resource_type.value}-{random_hex}"


def generate_instance_id() -> str:
    """Generate EC2 instance ID: i-0123456789abcdef0"""
    return generate_resource_id(ResourceType.INSTANCE, 17)


def generate_volume_id() -> str:
    """Generate EBS volume ID: vol-0123456789abcdef"""
    return generate_resource_id(ResourceType.VOLUME, 17)


def generate_vpc_id() -> str:
    """Generate VPC ID: vpc-1a2b3c4d"""
    return generate_resource_id(ResourceType.VPC, 8)


def generate_subnet_id() -> str:
    """Generate subnet ID: subnet-1a2b3c4d"""
    return generate_resource_id(ResourceType.SUBNET, 8)


def generate_security_group_id() -> str:
    """Generate security group ID: sg-0123456789abcdef"""
    return generate_resource_id(ResourceType.SECURITY_GROUP, 17)


def generate_ami_id() -> str:
    """Generate AMI ID: ami-0123456789abcdef"""
    return generate_resource_id(ResourceType.AMI, 17)


def generate_snapshot_id() -> str:
    """Generate snapshot ID: snap-0123456789abcdef"""
    return generate_resource_id(ResourceType.SNAPSHOT, 17)


def generate_access_key_id() -> str:
    """Generate IAM access key ID: AKIAIOSFODNN7EXAMPLE"""
    return generate_resource_id(ResourceType.ACCESS_KEY, 16)


def generate_secret_access_key() -> str:
    """Generate IAM secret access key: 40 character random string"""
    return secrets.token_urlsafe(30)  # 40 chars base64


def validate_resource_id(resource_id: str, resource_type: ResourceType) -> bool:
    """
    Validate resource ID format
    
    Args:
        resource_id: ID to validate
        resource_type: Expected resource type
    
    Returns:
        True if valid, False otherwise
    """
    if not resource_id:
        return False
    
    # Special case: Access keys
    if resource_type == ResourceType.ACCESS_KEY:
        return resource_id.startswith("AKIA") and len(resource_id) == 20
    
    # Standard validation
    parts = resource_id.split("-", 1)
    if len(parts) != 2:
        return False
    
    prefix, random_part = parts
    return (
        prefix == resource_type.value and
        len(random_part) > 0 and
        all(c in string.hexdigits for c in random_part)
    )


# Aliases for backward compatibility
generate_id = generate_resource_id
generate_access_key = generate_access_key_id
