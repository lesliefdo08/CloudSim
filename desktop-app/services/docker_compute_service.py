"""
Docker Compute Service - Container-backed EC2 simulation
Maps each compute instance to a real Docker container for realistic cloud experience
"""

import docker
import time
import random
from typing import Optional, List, Dict, Any
from pathlib import Path


class DockerComputeService:
    """Service for managing Docker containers as compute instances"""
    
    # Supported OS images
    SUPPORTED_IMAGES = {
        "ubuntu:22.04": "Ubuntu 22.04 LTS",
        "ubuntu:20.04": "Ubuntu 20.04 LTS",
        "amazonlinux:2": "Amazon Linux 2",
        "debian:latest": "Debian Latest"
    }
    
    def __init__(self):
        """Initialize Docker client"""
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            self._docker_available = True
        except Exception as e:
            print(f"WARNING: Docker not available: {e}")
            self._docker_available = False
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Docker is available"""
        return self._docker_available
    
    def pull_image_if_needed(self, image: str) -> bool:
        """
        Pull Docker image if not present locally
        
        Args:
            image: Image name (e.g. "ubuntu:22.04")
            
        Returns:
            True if image is available, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            # Check if image exists locally
            self.client.images.get(image)
            return True
        except docker.errors.ImageNotFound:
            # Pull image
            print(f"Pulling Docker image: {image}")
            try:
                self.client.images.pull(image)
                return True
            except Exception as e:
                print(f"Failed to pull image {image}: {e}")
                return False
    
    def create_container(self, instance_id: str, instance_name: str, image: str) -> Optional[str]:
        """
        Create a new Docker container for an instance
        
        Args:
            instance_id: CloudSim instance ID
            instance_name: Instance name
            image: Docker image to use
            
        Returns:
            Container ID if successful, None otherwise
        """
        if not self.is_available():
            return None
        
        # Ensure image is available
        if not self.pull_image_if_needed(image):
            return None
        
        try:
            # Create container with infinite sleep to keep it running
            container = self.client.containers.create(
                image=image,
                name=f"cloudsim-{instance_id}",
                command="/bin/sh -c 'while true; do sleep 3600; done'",
                detach=True,
                labels={
                    "cloudsim.instance_id": instance_id,
                    "cloudsim.instance_name": instance_name
                },
                stdin_open=True,
                tty=True
            )
            
            return container.id
        except Exception as e:
            print(f"Failed to create container: {e}")
            return None
    
    def start_container(self, container_id: str) -> bool:
        """
        Start a Docker container
        
        Args:
            container_id: Docker container ID
            
        Returns:
            True if started successfully
        """
        if not self.is_available():
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.start()
            # Simulate realistic startup delay
            time.sleep(random.uniform(1.5, 3.0))
            return True
        except Exception as e:
            print(f"Failed to start container: {e}")
            return False
    
    def stop_container(self, container_id: str) -> bool:
        """
        Stop a Docker container
        
        Args:
            container_id: Docker container ID
            
        Returns:
            True if stopped successfully
        """
        if not self.is_available():
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
            # Simulate realistic shutdown delay
            time.sleep(random.uniform(0.8, 2.0))
            return True
        except Exception as e:
            print(f"Failed to stop container: {e}")
            return False
    
    def remove_container(self, container_id: str) -> bool:
        """
        Remove a Docker container (terminate instance)
        
        Args:
            container_id: Docker container ID
            
        Returns:
            True if removed successfully
        """
        if not self.is_available():
            return False
        
        try:
            container = self.client.containers.get(container_id)
            # Stop first if running
            if container.status == 'running':
                container.stop(timeout=5)
            container.remove()
            return True
        except Exception as e:
            print(f"Failed to remove container: {e}")
            return False
    
    def get_container_status(self, container_id: str) -> str:
        """
        Get Docker container status
        
        Args:
            container_id: Docker container ID
            
        Returns:
            Status string ('running', 'exited', 'created', etc.)
        """
        if not self.is_available():
            return "unavailable"
        
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except Exception:
            return "not_found"
    
    def execute_command(self, container_id: str, command: str) -> Dict[str, Any]:
        """
        Execute a command inside a running container
        
        Args:
            container_id: Docker container ID
            command: Shell command to execute
            
        Returns:
            Dictionary with 'output', 'exit_code', 'error'
        """
        if not self.is_available():
            return {
                "output": "Docker not available",
                "exit_code": 1,
                "error": "Docker service not running"
            }
        
        try:
            container = self.client.containers.get(container_id)
            
            if container.status != 'running':
                return {
                    "output": "",
                    "exit_code": 1,
                    "error": "Container is not running"
                }
            
            # Simulate realistic network latency
            time.sleep(random.uniform(0.3, 0.8))
            
            # Execute command
            exit_code, output = container.exec_run(
                f'/bin/sh -c "{command}"',
                demux=True
            )
            
            # Process output
            stdout = output[0].decode('utf-8') if output[0] else ""
            stderr = output[1].decode('utf-8') if output[1] else ""
            
            return {
                "output": stdout,
                "exit_code": exit_code,
                "error": stderr
            }
        except Exception as e:
            return {
                "output": "",
                "exit_code": 1,
                "error": str(e)
            }
    
    def list_containers(self) -> List[Dict[str, str]]:
        """
        List all CloudSim containers
        
        Returns:
            List of container info dictionaries
        """
        if not self.is_available():
            return []
        
        try:
            containers = self.client.containers.list(
                all=True,
                filters={"label": "cloudsim.instance_id"}
            )
            
            return [{
                "container_id": c.id,
                "instance_id": c.labels.get("cloudsim.instance_id"),
                "instance_name": c.labels.get("cloudsim.instance_name"),
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else "unknown"
            } for c in containers]
        except Exception as e:
            print(f"Failed to list containers: {e}")
            return []
    
    def reconnect_to_container(self, container_id: str) -> bool:
        """
        Verify container exists and is accessible after app restart
        
        Args:
            container_id: Docker container ID
            
        Returns:
            True if container is accessible
        """
        if not self.is_available():
            return False
        
        try:
            container = self.client.containers.get(container_id)
            return True
        except Exception:
            return False


# Global instance
docker_service = DockerComputeService()
