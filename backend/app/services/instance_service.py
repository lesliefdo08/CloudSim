"""
Instance Service

Business logic for EC2 instance lifecycle management with Docker integration.
"""

from typing import Optional, List
import docker
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.instance import Instance
from app.models.subnet import Subnet
from app.models.vpc import VPC
from app.models.security_group import SecurityGroup
from app.models.security_group_rule import SecurityGroupRule
from app.models.ami import AMI
from app.core.resource_ids import generate_id, ResourceType
from app.core.exceptions import ResourceNotFoundError, ValidationError, ConflictError
from app.utils.instance_state import (
    InstanceState,
    can_transition,
    can_start,
    can_stop,
    can_terminate,
    is_valid_instance_type
)
import logging

logger = logging.getLogger(__name__)


class InstanceService:
    """Service for managing EC2 instances with Docker containers"""
    
    def __init__(self):
        """Initialize Docker client"""
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            # Docker not available
            logger.error(f"Failed to initialize Docker client: {e}")
            self.docker_client = None
    
    async def run_instances(
        self,
        db: AsyncSession,
        account_id: str,
        image_id: Optional[str] = None,
        ami_id: Optional[str] = None,
        instance_type: str = "t2.micro",
        subnet_id: Optional[str] = None,
        security_group_ids: Optional[List[str]] = None,
        key_name: Optional[str] = None,
        user_data: Optional[str] = None,
        tags: Optional[dict] = None,
        min_count: int = 1,
        max_count: int = 1
    ) -> List[Instance]:
        """
        Launch new EC2 instances.
        
        Args:
            db: Database session
            account_id: Account ID
            image_id: Docker image (e.g., ubuntu:22.04)
            ami_id: Custom AMI ID to launch from
            instance_type: Instance type (e.g., t2.micro)
            subnet_id: Subnet ID
            security_group_ids: List of security group IDs
            key_name: SSH key pair name
            user_data: User data script (base64 encoded)
            tags: Tags dictionary
            min_count: Minimum instances to launch
            max_count: Maximum instances to launch
        
        Returns:
            List of created Instance objects
        
        Raises:
            ResourceNotFoundError: Subnet, security group, or AMI not found
            ValidationError: Invalid parameters
        """
        # Validate that either image_id or ami_id is provided
        if not image_id and not ami_id:
            raise ValidationError(
                message="Either image_id or ami_id must be specified"
            )
        
        if image_id and ami_id:
            raise ValidationError(
                message="Cannot specify both image_id and ami_id"
            )
        
        # If ami_id provided, get AMI and use its Docker image
        docker_image = image_id
        if ami_id:
            result = await db.execute(
                select(AMI).where(
                    AMI.ami_id == ami_id,
                    AMI.account_id == account_id
                )
            )
            ami = result.scalar_one_or_none()
            
            if not ami:
                raise ResourceNotFoundError(
                    resource_type="AMI",
                    resource_id=ami_id,
                    message=f"AMI {ami_id} not found"
                )
            
            if ami.state != "available":
                raise ValidationError(
                    message=f"AMI {ami_id} is not available (state: {ami.state})"
                )
            
            # Use AMI's Docker image
            docker_image = f"cloudsim-ami:{ami_id}"
            # Store original AMI ID in image_id field for reference
            image_id = ami_id
        
        # Validate instance type
        if not is_valid_instance_type(instance_type):
            raise ValidationError(
                message=f"Invalid instance type: {instance_type}"
            )
        
        # Verify subnet exists and get VPC
        result = await db.execute(
            select(Subnet).where(Subnet.subnet_id == subnet_id, Subnet.account_id == account_id)
        )
        subnet = result.scalar_one_or_none()
        
        if not subnet:
            raise ResourceNotFoundError(
                resource_type="Subnet",
                resource_id=subnet_id,
                message=f"Subnet {subnet_id} not found"
            )
        
        # Get VPC for Docker network
        result = await db.execute(
            select(VPC).where(VPC.vpc_id == subnet.vpc_id)
        )
        vpc = result.scalar_one_or_none()
        
        if not vpc:
            raise ResourceNotFoundError(
                resource_type="VPC",
                resource_id=subnet.vpc_id,
                message=f"VPC {subnet.vpc_id} not found"
            )
        
        # Verify security groups exist
        if security_group_ids:
            for sg_id in security_group_ids:
                result = await db.execute(
                    select(SecurityGroup).where(
                        SecurityGroup.group_id == sg_id,
                        SecurityGroup.account_id == account_id
                    )
                )
                sg = result.scalar_one_or_none()
                if not sg:
                    raise ResourceNotFoundError(
                        resource_type="SecurityGroup",
                        resource_id=sg_id,
                        message=f"Security group {sg_id} not found"
                    )
        
        # Launch instances
        instances = []
        for i in range(max_count):
            instance = await self._launch_single_instance(
                db=db,
                account_id=account_id,
                subnet=subnet,
                vpc=vpc,
                docker_image=docker_image,
                image_id=image_id,
                instance_type=instance_type,
                security_group_ids=security_group_ids,
                key_name=key_name,
                user_data=user_data,
                tags=tags
            )
            instances.append(instance)
        
        return instances
    
    async def _launch_single_instance(
        self,
        db: AsyncSession,
        account_id: str,
        subnet: Subnet,
        vpc: VPC,
        docker_image: str,
        image_id: str,
        instance_type: str,
        security_group_ids: Optional[List[str]],
        key_name: Optional[str],
        user_data: Optional[str],
        tags: Optional[dict]
    ) -> Instance:
        """Launch a single instance with optional user data execution"""
        # Generate instance ID
        instance_id = generate_id(ResourceType.INSTANCE)
        
        # Create instance record in pending state
        instance = Instance(
            instance_id=instance_id,
            subnet_id=subnet.subnet_id,
            account_id=account_id,
            instance_type=instance_type,
            image_id=image_id,
            state=InstanceState.PENDING.value,
            security_group_ids=",".join(security_group_ids) if security_group_ids else None,
            key_name=key_name,
            user_data=user_data,
            tags=str(tags) if tags else None
        )
        
        db.add(instance)
        await db.flush()  # Get instance_id
        
        # Create Docker container
        if self.docker_client:
            try:
                container_name = f"cloudsim-instance-{instance_id}"
                
                # Get Docker network
                docker_network = None
                if vpc.docker_network_id:
                    try:
                        docker_network = self.docker_client.networks.get(vpc.docker_network_id)
                    except docker.errors.NotFound:
                        logger.warning(f"Docker network {vpc.docker_network_id} not found")
                
                # Get port mappings from security group rules
                port_bindings = {}
                if security_group_ids:
                    port_bindings = await self._get_port_bindings(db, security_group_ids)
                
                # Prepare container command
                container_command = "/bin/sh -c 'tail -f /dev/null'"
                if user_data:
                    # If user data provided, execute it and capture output
                    import base64
                    # Decode user data (assuming it's base64 encoded)
                    try:
                        user_data_decoded = base64.b64decode(user_data).decode('utf-8')
                    except:
                        user_data_decoded = user_data
                    
                    # Create startup script that executes user data and logs output
                    startup_script = f"""
                    mkdir -p /var/log
                    cat > /tmp/user-data.sh << 'EOF'
{user_data_decoded}
EOF
                    chmod +x /tmp/user-data.sh
                    bash /tmp/user-data.sh > /var/log/cloud-init-output.log 2>&1
                    tail -f /dev/null
                    """
                    container_command = f"/bin/sh -c '{startup_script}'"
                
                # Create container
                container = self.docker_client.containers.create(
                    image=docker_image,
                    name=container_name,
                    detach=True,
                    ports=port_bindings if port_bindings else None,
                    labels={
                        "cloudsim.instance_id": instance_id,
                        "cloudsim.account_id": account_id,
                        "cloudsim.subnet_id": subnet.subnet_id,
                        "cloudsim.vpc_id": vpc.vpc_id
                    },
                    # Keep container running
                    command="/bin/sh -c 'tail -f /dev/null'",
                    tty=True
                )
                
                # Connect to VPC network
                if docker_network:
                    docker_network.connect(container)
                
                # Start container
                container.start()
                container.reload()
                
                # Get private IP from container
                private_ip = None
                if docker_network:
                    network_settings = container.attrs.get("NetworkSettings", {})
                    networks = network_settings.get("Networks", {})
                    vpc_network_name = vpc.docker_network_name
                    if vpc_network_name in networks:
                        private_ip = networks[vpc_network_name].get("IPAddress")
                
                # Update instance with Docker details
                instance.docker_container_id = container.id
                instance.docker_container_name = container_name
                instance.private_ip_address = private_ip
                instance.state = InstanceState.RUNNING.value
                
                logger.info(f"Launched instance {instance_id} with container {container.id}")
                
            except docker.errors.ImageNotFound:
                instance.state = InstanceState.TERMINATED.value
                instance.state_reason = f"Image {image_id} not found"
                logger.error(f"Failed to launch instance {instance_id}: Image not found")
            except docker.errors.DockerException as e:
                instance.state = InstanceState.TERMINATED.value
                instance.state_reason = f"Docker error: {str(e)}"
                logger.error(f"Failed to launch instance {instance_id}: {e}")
        else:
            # No Docker client, set to running anyway (for testing)
            instance.state = InstanceState.RUNNING.value
            instance.state_reason = "Docker not available"
        
        await db.commit()
        await db.refresh(instance)
        
        return instance
    
    async def _get_port_bindings(self, db: AsyncSession, security_group_ids: List[str]) -> dict:
        """Get port bindings from security group ingress rules"""
        port_bindings = {}
        
        for sg_id in security_group_ids:
            result = await db.execute(
                select(SecurityGroupRule).where(
                    SecurityGroupRule.group_id == sg_id,
                    SecurityGroupRule.rule_type == "ingress",
                    SecurityGroupRule.ip_protocol == "tcp"
                )
            )
            rules = result.scalars().all()
            
            for rule in rules:
                if rule.from_port and rule.to_port:
                    # Expose port range
                    for port in range(rule.from_port, rule.to_port + 1):
                        port_bindings[f"{port}/tcp"] = port
        
        return port_bindings
    
    async def get_instance(
        self,
        db: AsyncSession,
        instance_id: str,
        account_id: str
    ) -> Instance:
        """
        Get instance by ID.
        
        Args:
            db: Database session
            instance_id: Instance ID
            account_id: Account ID
        
        Returns:
            Instance
        
        Raises:
            ResourceNotFoundError: Instance not found
        """
        result = await db.execute(
            select(Instance).where(
                Instance.instance_id == instance_id,
                Instance.account_id == account_id
            )
        )
        instance = result.scalar_one_or_none()
        
        if not instance:
            raise ResourceNotFoundError(
                resource_type="Instance",
                resource_id=instance_id,
                message=f"Instance {instance_id} not found"
            )
        
        return instance
    
    async def describe_instances(
        self,
        db: AsyncSession,
        account_id: str,
        instance_ids: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Instance]:
        """
        List instances.
        
        Args:
            db: Database session
            account_id: Account ID
            instance_ids: Optional list of instance IDs to filter
            limit: Maximum results
            offset: Offset for pagination
        
        Returns:
            List of Instance
        """
        query = select(Instance).where(Instance.account_id == account_id)
        
        if instance_ids:
            query = query.where(Instance.instance_id.in_(instance_ids))
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def start_instances(
        self,
        db: AsyncSession,
        instance_ids: List[str],
        account_id: str
    ) -> List[Instance]:
        """
        Start stopped instances.
        
        Args:
            db: Database session
            instance_ids: List of instance IDs
            account_id: Account ID
        
        Returns:
            List of started Instance objects
        
        Raises:
            ValidationError: Instance cannot be started
        """
        instances = []
        
        for instance_id in instance_ids:
            instance = await self.get_instance(db, instance_id, account_id)
            
            if not can_start(instance.state):
                raise ValidationError(
                    message=f"Instance {instance_id} cannot be started from state {instance.state}"
                )
            
            # Start Docker container
            if self.docker_client and instance.docker_container_id:
                try:
                    container = self.docker_client.containers.get(instance.docker_container_id)
                    container.start()
                    instance.state = InstanceState.RUNNING.value
                    logger.info(f"Started instance {instance_id}")
                except docker.errors.NotFound:
                    instance.state = InstanceState.TERMINATED.value
                    instance.state_reason = "Container not found"
                except docker.errors.DockerException as e:
                    raise ValidationError(message=f"Failed to start instance: {str(e)}")
            else:
                instance.state = InstanceState.RUNNING.value
            
            instances.append(instance)
        
        await db.commit()
        
        return instances
    
    async def stop_instances(
        self,
        db: AsyncSession,
        instance_ids: List[str],
        account_id: str
    ) -> List[Instance]:
        """
        Stop running instances.
        
        Args:
            db: Database session
            instance_ids: List of instance IDs
            account_id: Account ID
        
        Returns:
            List of stopped Instance objects
        
        Raises:
            ValidationError: Instance cannot be stopped
        """
        instances = []
        
        for instance_id in instance_ids:
            instance = await self.get_instance(db, instance_id, account_id)
            
            if not can_stop(instance.state):
                raise ValidationError(
                    message=f"Instance {instance_id} cannot be stopped from state {instance.state}"
                )
            
            # Stop Docker container
            if self.docker_client and instance.docker_container_id:
                try:
                    container = self.docker_client.containers.get(instance.docker_container_id)
                    container.stop(timeout=10)
                    instance.state = InstanceState.STOPPED.value
                    logger.info(f"Stopped instance {instance_id}")
                except docker.errors.NotFound:
                    instance.state = InstanceState.TERMINATED.value
                    instance.state_reason = "Container not found"
                except docker.errors.DockerException as e:
                    raise ValidationError(message=f"Failed to stop instance: {str(e)}")
            else:
                instance.state = InstanceState.STOPPED.value
            
            instances.append(instance)
        
        await db.commit()
        
        return instances
    
    async def terminate_instances(
        self,
        db: AsyncSession,
        instance_ids: List[str],
        account_id: str
    ) -> List[Instance]:
        """
        Terminate instances.
        
        Args:
            db: Database session
            instance_ids: List of instance IDs
            account_id: Account ID
        
        Returns:
            List of terminated Instance objects
        
        Raises:
            ValidationError: Instance cannot be terminated
        """
        instances = []
        
        for instance_id in instance_ids:
            instance = await self.get_instance(db, instance_id, account_id)
            
            if not can_terminate(instance.state):
                raise ValidationError(
                    message=f"Instance {instance_id} cannot be terminated from state {instance.state}"
                )
            
            # Remove Docker container
            if self.docker_client and instance.docker_container_id:
                try:
                    container = self.docker_client.containers.get(instance.docker_container_id)
                    container.remove(force=True)
                    logger.info(f"Removed container for instance {instance_id}")
                except docker.errors.NotFound:
                    logger.warning(f"Container for instance {instance_id} already removed")
                except docker.errors.DockerException as e:
                    logger.error(f"Failed to remove container: {e}")
            
            instance.state = InstanceState.TERMINATED.value
            instances.append(instance)
        
        await db.commit()
        
        return instances



