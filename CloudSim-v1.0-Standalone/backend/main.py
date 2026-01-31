"""CloudSim Backend - Instance Control Plane
Handles instance metadata and Docker container lifecycle
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import time
import random
import json
from pathlib import Path
from datetime import datetime
import docker
from docker.errors import DockerException, ImageNotFound, APIError

app = FastAPI(title="CloudSim Backend", version="1.0")

# CORS for local UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Docker client
try:
    docker_client = docker.from_env()
    docker_client.ping()
    print("[CONTROL] Docker client initialized successfully")
except DockerException as e:
    print(f"[ERROR] Docker not available: {e}")
    docker_client = None

# Data persistence
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
INSTANCES_FILE = DATA_DIR / "instances.json"


# Models
class InstanceCreate(BaseModel):
    name: str
    cpu: int = 1
    memory: int = 512
    image: str = "ubuntu:22.04"


class InstanceResponse(BaseModel):
    id: str
    name: str
    state: str
    image: str
    cpu: int
    memory: int
    created_at: str
    container_id: Optional[str] = None


class ExecCommand(BaseModel):
    command: str


# Storage functions
def load_instances() -> List[dict]:
    """Load instances from JSON file"""
    if INSTANCES_FILE.exists():
        return json.loads(INSTANCES_FILE.read_text())
    return []


def save_instances(instances: List[dict]):
    """Save instances to JSON file"""
    INSTANCES_FILE.write_text(json.dumps(instances, indent=2))


def get_instance_by_id(instance_id: str) -> Optional[dict]:
    """Get instance by ID"""
    instances = load_instances()
    return next((i for i in instances if i["id"] == instance_id), None)


# API Endpoints
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "CloudSim Backend", "version": "1.0"}


@app.post("/api/instances", response_model=InstanceResponse)
def create_instance(data: InstanceCreate):
    """Create new EC2 instance (metadata only, STOPPED state)"""
    # Simulate AWS delay
    time.sleep(random.uniform(1.5, 2.5))
    
    instance_id = f"i-{random.randint(100000, 999999):06x}"
    
    print(f"[CONTROL] Instance created {instance_id}")
    
    instance = {
        "id": instance_id,
        "name": data.name,
        "state": "STOPPED",
        "image": data.image,
        "cpu": data.cpu,
        "memory": data.memory,
        "created_at": datetime.now().isoformat(),
        "container_id": None
    }
    
    instances = load_instances()
    instances.append(instance)
    save_instances(instances)
    
    print(f"[CONTROL] Instance persisted: {instance_id} (state=STOPPED)")
    
    return instance


@app.get("/api/instances", response_model=List[InstanceResponse])
def list_instances():
    """List all instances with automatic reconciliation"""
    instances = load_instances()
    print(f"[CONTROL] Listing instances: {len(instances)}")
    
    # Automatic reconciliation: silently sync metadata with Docker reality
    metadata_updated = False
    
    for instance in instances:
        container_id = instance.get("container_id")
        stored_state = instance["state"]
        
        # Query Docker for reality
        if container_id and docker_client:
            try:
                container = docker_client.containers.get(container_id)
                docker_state = container.status
                
                # Reconcile: running → RUNNING
                if docker_state == "running" and stored_state != "RUNNING":
                    instance["state"] = "RUNNING"
                    metadata_updated = True
                    print(f"[RECONCILE] Auto-corrected {instance['id']}: {stored_state} → RUNNING")
                
                # Reconcile: exited → STOPPED
                elif docker_state == "exited" and stored_state != "STOPPED":
                    instance["state"] = "STOPPED"
                    metadata_updated = True
                    print(f"[RECONCILE] Auto-corrected {instance['id']}: {stored_state} → STOPPED")
                    
            except docker.errors.NotFound:
                # Container missing → STOPPED, clear container_id
                if stored_state != "STOPPED" or container_id is not None:
                    instance["state"] = "STOPPED"
                    instance["container_id"] = None
                    metadata_updated = True
                    print(f"[RECONCILE] Auto-corrected {instance['id']}: container missing, set STOPPED")
                    
            except Exception as e:
                # Docker query failed, skip reconciliation for this instance
                print(f"[WARNING] Failed to reconcile {instance['id']}: {e}")
        
        # No container → ensure STOPPED
        elif not container_id and stored_state != "STOPPED":
            instance["state"] = "STOPPED"
            metadata_updated = True
            print(f"[RECONCILE] Auto-corrected {instance['id']}: no container, set STOPPED")
    
    # Persist corrected metadata
    if metadata_updated:
        save_instances(instances)
        print(f"[CONTROL] Reconciled metadata persisted")
    
    return instances


@app.get("/api/instances/{instance_id}", response_model=InstanceResponse)
def get_instance(instance_id: str):
    """Get instance by ID"""
    instance = get_instance_by_id(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    return instance


@app.get("/api/instances/{instance_id}/status")
def get_instance_status(instance_id: str):
    """Get instance status with real-time Docker container state"""
    instance = get_instance_by_id(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    print(f"[CONTROL] Checking status for instance {instance_id}")
    
    # Get stored state
    stored_state = instance["state"]
    docker_state = None
    docker_status = None
    
    # Query Docker if container exists
    container_id = instance.get("container_id")
    if container_id and docker_client:
        try:
            container = docker_client.containers.get(container_id)
            docker_state = container.status  # running, exited, paused, etc.
            docker_status = "found"
            print(f"[CONTROL] Container {container_id[:12]} status: {docker_state}")
        except docker.errors.NotFound:
            docker_state = "not_found"
            docker_status = "not_found"
            print(f"[CONTROL] Container {container_id[:12]} not found in Docker")
        except Exception as e:
            docker_state = "error"
            docker_status = f"error: {str(e)}"
            print(f"[ERROR] Failed to query container {container_id[:12]}: {e}")
    else:
        if not container_id:
            docker_state = "no_container"
            docker_status = "no_container"
            print(f"[CONTROL] Instance {instance_id} has no container")
        else:
            docker_state = "docker_unavailable"
            docker_status = "docker_unavailable"
            print(f"[CONTROL] Docker client not available")
    
    # Detect drift
    drift_detected = False
    if docker_state == "running" and stored_state != "RUNNING":
        drift_detected = True
        print(f"[WARNING] Drift detected: stored={stored_state}, docker={docker_state}")
    elif docker_state == "exited" and stored_state == "RUNNING":
        drift_detected = True
        print(f"[WARNING] Drift detected: stored={stored_state}, docker={docker_state}")
    
    return {
        "id": instance["id"],
        "name": instance["name"],
        "state": stored_state,
        "docker_state": docker_state,
        "docker_status": docker_status,
        "container_id": container_id,
        "drift_detected": drift_detected,
        "image": instance["image"],
        "cpu": instance["cpu"],
        "memory": instance["memory"],
        "created_at": instance["created_at"]
    }


@app.post("/api/instances/{instance_id}/reconcile")
def reconcile_instance(instance_id: str):
    """Reconcile instance metadata with Docker reality - NO container mutations"""
    instance = get_instance_by_id(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    print(f"[CONTROL] Reconciling instance {instance_id}")
    
    # Get current states
    stored_state = instance["state"]
    previous_state = stored_state
    corrected_state = stored_state
    action_taken = "no_change"
    container_id = instance.get("container_id")
    
    # Query Docker for reality
    docker_state = None
    if container_id and docker_client:
        try:
            container = docker_client.containers.get(container_id)
            docker_state = container.status
            print(f"[CONTROL] Docker reports: {docker_state}")
        except docker.errors.NotFound:
            docker_state = "not_found"
            print(f"[CONTROL] Container {container_id[:12]} not found")
        except Exception as e:
            print(f"[ERROR] Docker query failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to query Docker: {str(e)}")
    
    # Reconciliation logic
    if docker_state == "not_found":
        # Container missing → set STOPPED and clear container_id
        if stored_state != "STOPPED" or container_id is not None:
            corrected_state = "STOPPED"
            instance["state"] = "STOPPED"
            instance["container_id"] = None
            action_taken = "updated"
            print(f"[RECONCILE] Container missing: {previous_state} → {corrected_state}, cleared container_id")
    elif docker_state == "running":
        # Docker says running → metadata should be RUNNING
        if stored_state != "RUNNING":
            corrected_state = "RUNNING"
            instance["state"] = "RUNNING"
            action_taken = "updated"
            print(f"[RECONCILE] Corrected drift: {previous_state} → {corrected_state}")
    elif docker_state == "exited":
        # Docker says exited → metadata should be STOPPED
        if stored_state != "STOPPED":
            corrected_state = "STOPPED"
            instance["state"] = "STOPPED"
            action_taken = "updated"
            print(f"[RECONCILE] Corrected drift: {previous_state} → {corrected_state}")
    elif docker_state is None and not container_id:
        # No container at all → ensure STOPPED
        if stored_state != "STOPPED":
            corrected_state = "STOPPED"
            instance["state"] = "STOPPED"
            action_taken = "updated"
            print(f"[RECONCILE] No container: {previous_state} → {corrected_state}")
    
    # Persist changes if any
    if action_taken == "updated":
        instances = load_instances()
        for i, inst in enumerate(instances):
            if inst["id"] == instance_id:
                instances[i] = instance
                break
        save_instances(instances)
        print(f"[CONTROL] Metadata persisted: {previous_state} → {corrected_state}")
    else:
        print(f"[CONTROL] No reconciliation needed, state already correct")
    
    return {
        "id": instance_id,
        "previous_state": previous_state,
        "corrected_state": corrected_state,
        "action_taken": action_taken
    }


@app.post("/api/instances/{instance_id}/start")
def start_instance(instance_id: str):
    """Start instance - reuses existing container or creates new one"""
    print(f"[DOCKER] Starting instance {instance_id}")
    
    # Validate Docker is available
    if not docker_client:
        print(f"[ERROR] Docker not available for {instance_id}")
        raise HTTPException(status_code=503, detail="Docker not available")
    
    # Get instance
    instance = get_instance_by_id(instance_id)
    if not instance:
        print(f"[ERROR] Instance {instance_id} not found")
        raise HTTPException(status_code=404, detail="Instance not found")
    
    print(f"[DOCKER] Instance {instance_id} current state: {instance['state']}")
    
    # Refuse if already running
    if instance["state"] == "RUNNING":
        print(f"[ERROR] Instance {instance_id} already RUNNING")
        raise HTTPException(status_code=400, detail="Instance already running")
    
    # Check if container already exists (restart scenario)
    existing_container_id = instance.get("container_id")
    
    try:
        if existing_container_id:
            # Reuse existing container
            print(f"[DOCKER] Reusing existing container {existing_container_id[:12]}")
            try:
                container = docker_client.containers.get(existing_container_id)
                print(f"[DOCKER] Container found, restarting...")
                container.start()
                print(f"[DOCKER] Container restarted: {existing_container_id[:12]}")
                
                # Update instance state
                instance["state"] = "RUNNING"
                
                # Persist to storage
                instances = load_instances()
                for i, inst in enumerate(instances):
                    if inst["id"] == instance_id:
                        instances[i] = instance
                        break
                save_instances(instances)
                
                print(f"[DOCKER] Instance {instance_id} state updated: RUNNING (reused container)")
                return instance
                
            except docker.errors.NotFound:
                print(f"[DOCKER] Container {existing_container_id[:12]} not found, creating new one")
                # Container was deleted, fall through to create new one
                instance["container_id"] = None
        
        # Create new Docker container
        container_name = f"cloudsim-{instance_id}"
        image = instance["image"]
        
        print(f"[DOCKER] Creating new Docker container: {container_name}")
        print(f"[DOCKER] Using image: {image}")
        print(f"[DOCKER] Container config: tty=True, stdin_open=True, detach=True")
        
        # Pull image if not exists
        print(f"[DOCKER] Checking for image {image}...")
        try:
            docker_client.images.get(image)
            print(f"[DOCKER] Image {image} found locally")
        except ImageNotFound:
            print(f"[DOCKER] Pulling image {image}...")
            docker_client.images.pull(image)
            print(f"[DOCKER] Image {image} pulled successfully")
        
        # Create and start container
        container = docker_client.containers.run(
            image=image,
            name=container_name,
            command="/bin/bash",
            tty=True,
            stdin_open=True,
            detach=True,
            remove=False
        )
        
        container_id = container.id
        print(f"[DOCKER] Container created: {container_id[:12]}")
        print(f"[DOCKER] Container name: {container_name}")
        print(f"[DOCKER] Container status: {container.status}")
        
        # Update instance state
        instance["state"] = "RUNNING"
        instance["container_id"] = container_id
        
        # Persist to storage
        instances = load_instances()
        for i, inst in enumerate(instances):
            if inst["id"] == instance_id:
                instances[i] = instance
                break
        save_instances(instances)
        
        print(f"[DOCKER] Instance {instance_id} state updated: RUNNING")
        print(f"[DOCKER] Instance {instance_id} persisted with container_id: {container_id[:12]}")
        
        return instance
        
    except ImageNotFound as e:
        print(f"[ERROR] Image {image} not found: {e}")
        raise HTTPException(status_code=400, detail=f"Image {image} not found")
    except APIError as e:
        print(f"[ERROR] Docker API error for {instance_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Docker API error: {str(e)}")
    except Exception as e:
        print(f"[ERROR] Failed to start instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start instance: {str(e)}")


@app.post("/api/instances/{instance_id}/stop")
def stop_instance(instance_id: str):
    """Stop instance - stops Docker container but keeps it for restart"""
    print(f"[DOCKER] Stopping instance {instance_id}")
    
    # Validate Docker is available
    if not docker_client:
        print(f"[ERROR] Docker not available for {instance_id}")
        raise HTTPException(status_code=503, detail="Docker not available")
    
    # Get instance
    instance = get_instance_by_id(instance_id)
    if not instance:
        print(f"[ERROR] Instance {instance_id} not found")
        raise HTTPException(status_code=404, detail="Instance not found")
    
    print(f"[DOCKER] Instance {instance_id} current state: {instance['state']}")
    
    # Validate instance is RUNNING
    if instance["state"] != "RUNNING":
        print(f"[ERROR] Instance {instance_id} not running (state={instance['state']})")
        raise HTTPException(status_code=400, detail=f"Instance not running (state: {instance['state']})")
    
    # Get container
    container_id = instance.get("container_id")
    if not container_id:
        print(f"[ERROR] Instance {instance_id} has no container_id")
        raise HTTPException(status_code=500, detail="Instance has no associated container")
    
    try:
        # Get container object
        container = docker_client.containers.get(container_id)
        print(f"[DOCKER] Stopping container {container_id[:12]}")
        
        # Stop the container (but don't remove it)
        container.stop()
        print(f"[DOCKER] Container stopped: {container_id[:12]}")
        
        # Update instance state to STOPPED (keep container_id for restart)
        instance["state"] = "STOPPED"
        
        # Persist to storage
        instances = load_instances()
        for i, inst in enumerate(instances):
            if inst["id"] == instance_id:
                instances[i] = instance
                break
        save_instances(instances)
        
        print(f"[DOCKER] Instance {instance_id} state updated: STOPPED")
        print(f"[DOCKER] Container preserved for restart: {container_id[:12]}")
        
        return instance
        
    except docker.errors.NotFound:
        print(f"[ERROR] Container {container_id[:12]} not found")
        raise HTTPException(status_code=500, detail="Container not found in Docker")
    except Exception as e:
        print(f"[ERROR] Failed to stop instance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop instance: {str(e)}")


@app.post("/api/instances/{instance_id}/reboot")
def reboot_instance(instance_id: str):
    """Reboot instance - restarts Docker container keeping state RUNNING"""
    print(f"[DOCKER] Rebooting instance {instance_id}")
    
    # Validate Docker is available
    if not docker_client:
        print(f"[ERROR] Docker not available for {instance_id}")
        raise HTTPException(status_code=503, detail="Docker not available")
    
    # Get instance
    instance = get_instance_by_id(instance_id)
    if not instance:
        print(f"[ERROR] Instance {instance_id} not found")
        raise HTTPException(status_code=404, detail="Instance not found")
    
    print(f"[DOCKER] Instance {instance_id} current state: {instance['state']}")
    
    # Validate instance is RUNNING
    if instance["state"] != "RUNNING":
        print(f"[ERROR] Instance {instance_id} not running (state={instance['state']})")
        raise HTTPException(status_code=400, detail=f"Instance not running (state: {instance['state']})")
    
    # Get container
    container_id = instance.get("container_id")
    if not container_id:
        print(f"[ERROR] Instance {instance_id} has no container_id")
        raise HTTPException(status_code=500, detail="Instance has no associated container")
    
    try:
        # Get container object
        container = docker_client.containers.get(container_id)
        print(f"[DOCKER] Restarting container {container_id[:12]}")
        
        # Restart the container (keeps filesystem and state)
        container.restart()
        print(f"[DOCKER] Container restarted: {container_id[:12]}")
        
        # State remains RUNNING, container_id unchanged
        # Just persist to ensure consistency
        instances = load_instances()
        for i, inst in enumerate(instances):
            if inst["id"] == instance_id:
                instances[i] = instance
                break
        save_instances(instances)
        
        print(f"[DOCKER] Instance {instance_id} rebooted successfully (state: RUNNING)")
        
        return instance
        
    except docker.errors.NotFound:
        print(f"[ERROR] Container {container_id[:12]} not found")
        raise HTTPException(status_code=500, detail="Container not found in Docker")
    except Exception as e:
        print(f"[ERROR] Failed to reboot instance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reboot instance: {str(e)}")


@app.post("/api/instances/{instance_id}/exec")
def exec_command(instance_id: str, exec_data: ExecCommand):
    """Execute command in instance container"""
    command = exec_data.command
    print(f"[DOCKER] Exec on {instance_id}: {command}")
    
    # Validate Docker is available
    if not docker_client:
        print(f"[ERROR] Docker not available for {instance_id}")
        raise HTTPException(status_code=503, detail="Docker not available")
    
    # Get instance
    instance = get_instance_by_id(instance_id)
    if not instance:
        print(f"[ERROR] Instance {instance_id} not found")
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Validate instance is RUNNING
    if instance["state"] != "RUNNING":
        print(f"[ERROR] Instance {instance_id} not running (state={instance['state']})")
        raise HTTPException(status_code=400, detail=f"Instance not running (state: {instance['state']})")
    
    # Get container
    container_id = instance.get("container_id")
    if not container_id:
        print(f"[ERROR] Instance {instance_id} has no container_id")
        raise HTTPException(status_code=500, detail="Instance has no associated container")
    
    try:
        # Get container object
        container = docker_client.containers.get(container_id)
        print(f"[DOCKER] Executing in container {container_id[:12]}: {command}")
        
        # Execute command
        result = container.exec_run(
            cmd=command,
            stdout=True,
            stderr=True,
            stdin=True,
            tty=True
        )
        
        # Decode output
        output = result.output.decode('utf-8') if result.output else ""
        exit_code = result.exit_code
        
        print(f"[DOCKER] Command completed with exit code {exit_code}")
        print(f"[DOCKER] Output length: {len(output)} bytes")
        
        return {"output": output, "exit_code": exit_code}
        
    except docker.errors.NotFound:
        print(f"[ERROR] Container {container_id[:12]} not found")
        raise HTTPException(status_code=500, detail="Container not found in Docker")
    except Exception as e:
        print(f"[ERROR] Failed to execute command: {e}")
        raise HTTPException(status_code=500, detail=f"Command execution failed: {str(e)}")


@app.delete("/api/instances/{instance_id}")
def terminate_instance(instance_id: str):
    """Terminate instance - removes Docker container and metadata"""
    instance = get_instance_by_id(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    print(f"[DOCKER] Terminating instance {instance_id}")
    
    # Remove Docker container if it exists
    container_id = instance.get("container_id")
    if container_id:
        if docker_client:
            try:
                print(f"[DOCKER] Fetching container {container_id[:12]}")
                container = docker_client.containers.get(container_id)
                
                # Remove container (force=True removes even if running)
                print(f"[DOCKER] Removing container {container_id[:12]}")
                container.remove(force=True)
                print(f"[DOCKER] Container removed: {container_id[:12]}")
                
            except docker.errors.NotFound:
                print(f"[DOCKER] Container {container_id[:12]} not found (already removed)")
            except Exception as e:
                print(f"[ERROR] Failed to remove container {container_id[:12]}: {e}")
                # Continue with metadata removal even if container removal fails
        else:
            print(f"[DOCKER] Docker not available, skipping container removal")
    else:
        print(f"[DOCKER] No container associated with instance {instance_id}")
    
    # Remove instance metadata from storage
    instances = load_instances()
    instances = [i for i in instances if i["id"] != instance_id]
    save_instances(instances)
    
    print(f"[DOCKER] Instance {instance_id} terminated (metadata removed)")
    
    return {"message": "Instance terminated"}


if __name__ == "__main__":
    import uvicorn
    print("[CONTROL] Starting CloudSim Backend (with Docker support)")
    uvicorn.run(app, host="127.0.0.1", port=8000)
