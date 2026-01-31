"""
Example Protected Endpoint
Demonstrates how to protect routes with IAM authorization
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.authorization import RequirePermission
from app.schemas.iam_auth import AuthenticatedUser


router = APIRouter(prefix="/examples", tags=["Examples"])


@router.get(
    "/ec2/instances",
    summary="Example: List EC2 instances (protected)",
    dependencies=[Depends(RequirePermission("ec2:DescribeInstances", "*"))]
)
async def list_instances_example(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Example protected endpoint
    
    **Required Permission:** `ec2:DescribeInstances` on resource `*`
    
    This endpoint demonstrates IAM authorization:
    - User must be authenticated
    - User must have permission to perform `ec2:DescribeInstances`
    - If permission denied, returns 403 AccessDenied error
    
    **Example Policy (allow access):**
    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "ec2:DescribeInstances",
                "Resource": "*"
            }
        ]
    }
    ```
    
    **Example Usage:**
    ```bash
    # 1. Login
    TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \\
      -H "Content-Type: application/json" \\
      -d '{"username": "alice", "password": "password"}' | jq -r '.access_token')
    
    # 2. Call protected endpoint
    curl http://localhost:8000/api/v1/examples/ec2/instances \\
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    return {
        "instances": [
            {"instance_id": "i-abc123", "state": "running"},
            {"instance_id": "i-def456", "state": "stopped"}
        ],
        "authorized_user": current_user.username,
        "message": "Access granted! You have permission to view EC2 instances."
    }


@router.post(
    "/ec2/instances/{instance_id}/start",
    summary="Example: Start EC2 instance (protected)",
    dependencies=[Depends(RequirePermission("ec2:StartInstances", "*"))]
)
async def start_instance_example(
    instance_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Example protected endpoint with write permission
    
    **Required Permission:** `ec2:StartInstances` on resource `*`
    
    **Example Policy (allow access):**
    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "ec2:StartInstances",
                "Resource": "arn:aws:ec2:*:*:instance/*"
            }
        ]
    }
    ```
    
    **Example Policy (deny terminate but allow start):**
    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["ec2:StartInstances", "ec2:StopInstances"],
                "Resource": "*"
            },
            {
                "Effect": "Deny",
                "Action": "ec2:TerminateInstances",
                "Resource": "*"
            }
        ]
    }
    ```
    """
    return {
        "instance_id": instance_id,
        "action": "start",
        "status": "success",
        "authorized_user": current_user.username,
        "message": f"Instance {instance_id} started successfully"
    }


@router.delete(
    "/ec2/instances/{instance_id}",
    summary="Example: Terminate EC2 instance (protected)",
    dependencies=[Depends(RequirePermission("ec2:TerminateInstances", "*"))]
)
async def terminate_instance_example(
    instance_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Example protected endpoint with destructive permission
    
    **Required Permission:** `ec2:TerminateInstances` on resource `*`
    
    Test with explicit deny:
    
    **Policy 1 (Allow all EC2):**
    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "ec2:*",
                "Resource": "*"
            }
        ]
    }
    ```
    
    **Policy 2 (Explicit Deny Terminate):**
    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Deny",
                "Action": "ec2:TerminateInstances",
                "Resource": "*"
            }
        ]
    }
    ```
    
    Result: Access DENIED (Deny wins over Allow)
    """
    return {
        "instance_id": instance_id,
        "action": "terminate",
        "status": "success",
        "authorized_user": current_user.username,
        "message": f"Instance {instance_id} terminated successfully"
    }


@router.get(
    "/s3/buckets",
    summary="Example: List S3 buckets (protected)",
    dependencies=[Depends(RequirePermission("s3:ListAllMyBuckets", "*"))]
)
async def list_buckets_example(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Example S3 protected endpoint
    
    **Required Permission:** `s3:ListAllMyBuckets` on resource `*`
    """
    return {
        "buckets": [
            {"name": "my-bucket-1", "created": "2026-01-15"},
            {"name": "my-bucket-2", "created": "2026-01-20"}
        ],
        "authorized_user": current_user.username
    }

