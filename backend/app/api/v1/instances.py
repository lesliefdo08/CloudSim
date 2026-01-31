"""
EC2 Instance API Routes

IAM-protected routes for managing EC2 instances.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.middleware.authorization import RequirePermission
from app.middleware.auth import get_current_user
from app.models.iam_user import User
from app.models.instance import Instance
from app.services.instance_service import InstanceService
from app.schemas.instance import (
    RunInstancesRequest,
    InstanceActionRequest,
    RunInstancesResponse,
    DescribeInstancesResponse,
    InstanceResponse,
    InstanceActionResponse,
    InstanceStateChangeResponse
)


router = APIRouter(prefix="/instances", tags=["EC2 Instances"])


@router.post(
    "",
    response_model=RunInstancesResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermission("ec2:RunInstances"))]
)
async def run_instances(
    request: RunInstancesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Launch EC2 instances.
    
    **Required Permission**: `ec2:RunInstances`
    
    **Example**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/instances \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "image_id": "ubuntu:22.04",
        "instance_type": "t2.micro",
        "subnet_id": "subnet-abc123",
        "security_group_ids": ["sg-xyz789"],
        "min_count": 1,
        "max_count": 1,
        "tags": {"Name": "web-server-1", "Environment": "Production"}
      }'
    ```
    """
    service = InstanceService()
    
    instances = await service.run_instances(
        db=db,
        account_id=current_user.account_id,
        image_id=request.image_id,        ami_id=request.ami_id,        instance_type=request.instance_type,
        subnet_id=request.subnet_id,
        security_group_ids=request.security_group_ids,
        key_name=request.key_name,
        user_data=request.user_data,
        tags=request.tags,
        min_count=request.min_count,
        max_count=request.max_count
    )
    
    return RunInstancesResponse(
        instances=[InstanceResponse.model_validate(i) for i in instances]
    )


@router.get(
    "",
    response_model=DescribeInstancesResponse,
    dependencies=[Depends(RequirePermission("ec2:DescribeInstances"))]
)
async def describe_instances(
    instance_ids: str = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List EC2 instances.
    
    **Required Permission**: `ec2:DescribeInstances`
    
    **Example**:
    ```bash
    # List all instances
    curl http://localhost:8000/api/v1/instances \\
      -H "Authorization: Bearer $TOKEN"
    
    # Get specific instances
    curl "http://localhost:8000/api/v1/instances?instance_ids=i-abc123,i-def456" \\
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    service = InstanceService()
    
    # Parse comma-separated instance IDs
    instance_id_list = None
    if instance_ids:
        instance_id_list = [id.strip() for id in instance_ids.split(",")]
    
    instances = await service.describe_instances(
        db=db,
        account_id=current_user.account_id,
        instance_ids=instance_id_list,
        limit=limit,
        offset=offset
    )
    
    # Count total
    query = select(func.count()).select_from(Instance).where(
        Instance.account_id == current_user.account_id
    )
    if instance_id_list:
        query = query.where(Instance.instance_id.in_(instance_id_list))
    
    result = await db.execute(query)
    total = result.scalar_one()
    
    return DescribeInstancesResponse(
        instances=[InstanceResponse.model_validate(i) for i in instances],
        total=total
    )


@router.get(
    "/{instance_id}",
    response_model=InstanceResponse,
    dependencies=[Depends(RequirePermission("ec2:DescribeInstances"))]
)
async def get_instance(
    instance_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get instance details.
    
    **Required Permission**: `ec2:DescribeInstances`
    
    **Example**:
    ```bash
    curl http://localhost:8000/api/v1/instances/i-abc123def456 \\
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    service = InstanceService()
    
    instance = await service.get_instance(
        db=db,
        instance_id=instance_id,
        account_id=current_user.account_id
    )
    
    return InstanceResponse.model_validate(instance)


@router.post(
    "/start",
    response_model=InstanceActionResponse,
    dependencies=[Depends(RequirePermission("ec2:StartInstances"))]
)
async def start_instances(
    request: InstanceActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start stopped instances.
    
    **Required Permission**: `ec2:StartInstances`
    
    **Example**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/instances/start \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "instance_ids": ["i-abc123", "i-def456"]
      }'
    ```
    """
    service = InstanceService()
    
    # Get previous states
    previous_states = {}
    for instance_id in request.instance_ids:
        instance = await service.get_instance(db, instance_id, current_user.account_id)
        previous_states[instance_id] = instance.state
    
    # Start instances
    instances = await service.start_instances(
        db=db,
        instance_ids=request.instance_ids,
        account_id=current_user.account_id
    )
    
    return InstanceActionResponse(
        starting_instances=[
            InstanceStateChangeResponse(
                instance_id=i.instance_id,
                current_state=i.state,
                previous_state=previous_states.get(i.instance_id)
            )
            for i in instances
        ]
    )


@router.post(
    "/stop",
    response_model=InstanceActionResponse,
    dependencies=[Depends(RequirePermission("ec2:StopInstances"))]
)
async def stop_instances(
    request: InstanceActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Stop running instances.
    
    **Required Permission**: `ec2:StopInstances`
    
    **Example**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/instances/stop \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "instance_ids": ["i-abc123", "i-def456"]
      }'
    ```
    """
    service = InstanceService()
    
    # Get previous states
    previous_states = {}
    for instance_id in request.instance_ids:
        instance = await service.get_instance(db, instance_id, current_user.account_id)
        previous_states[instance_id] = instance.state
    
    # Stop instances
    instances = await service.stop_instances(
        db=db,
        instance_ids=request.instance_ids,
        account_id=current_user.account_id
    )
    
    return InstanceActionResponse(
        stopping_instances=[
            InstanceStateChangeResponse(
                instance_id=i.instance_id,
                current_state=i.state,
                previous_state=previous_states.get(i.instance_id)
            )
            for i in instances
        ]
    )


@router.post(
    "/terminate",
    response_model=InstanceActionResponse,
    dependencies=[Depends(RequirePermission("ec2:TerminateInstances"))]
)
async def terminate_instances(
    request: InstanceActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Terminate instances.
    
    **Required Permission**: `ec2:TerminateInstances`
    
    **Example**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/instances/terminate \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "instance_ids": ["i-abc123", "i-def456"]
      }'
    ```
    """
    service = InstanceService()
    
    # Get previous states
    previous_states = {}
    for instance_id in request.instance_ids:
        instance = await service.get_instance(db, instance_id, current_user.account_id)
        previous_states[instance_id] = instance.state
    
    # Terminate instances
    instances = await service.terminate_instances(
        db=db,
        instance_ids=request.instance_ids,
        account_id=current_user.account_id
    )
    
    return InstanceActionResponse(
        terminating_instances=[
            InstanceStateChangeResponse(
                instance_id=i.instance_id,
                current_state=i.state,
                previous_state=previous_states.get(i.instance_id)
            )
            for i in instances
        ]
    )

