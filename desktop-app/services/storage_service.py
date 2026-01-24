"""
Storage Service - S3-like object storage management with IAM integration
"""

import os
import shutil
import json
from pathlib import Path
from typing import List, Optional
from models.bucket import Bucket, S3Object
from core.region import get_current_region
from core.iam import IAMManager, Action
from core.events import EventBus, EventType, emit_event
from core.metering import record_storage_usage
from utils.data_path import get_data_dir


class StorageService:
    """Service for managing S3-like storage buckets and objects
    
    *** SHARED LOCAL STORAGE ***
    Uses: data/buckets/ and data/bucket_metadata.json (single namespace)
    """
    
    def __init__(self):
        """Initialize storage service with IAM integration"""
        # Shared storage: data/buckets/
        data_dir = get_data_dir()
        self.storage_root = data_dir / "buckets"
        self.storage_root.mkdir(parents=True, exist_ok=True)
        # Shared metadata: data/bucket_metadata.json
        self.metadata_file = data_dir / "bucket_metadata.json"
        self._buckets = {}
        self._load_buckets()
        
        # Initialize core systems
        self.iam = IAMManager()
        self.event_bus = EventBus()
    
    def _check_permission(self, action: str, resource_arn: str):
        """Check IAM permission and raise PermissionError if denied"""
        if not self.iam.check_permission(action, resource_arn):
            username = "local-user"
            raise PermissionError(
                f"User '{username}' does not have permission to perform action '{action}' on resource '{resource_arn}'"
            )
    
    def _load_buckets(self):
        """Load bucket metadata from storage"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    for bucket_data in data:
                        bucket = Bucket.from_dict(bucket_data)
                        self._buckets[bucket.name] = bucket
            except (json.JSONDecodeError, IOError):
                pass
        
        # Sync with actual folders
        self._sync_buckets()
    
    def _sync_buckets(self):
        """Sync bucket metadata with actual folders"""
        # Remove buckets that don't have folders
        to_remove = []
        for name in self._buckets:
            bucket_path = self.storage_root / name
            if not bucket_path.exists():
                to_remove.append(name)
        
        for name in to_remove:
            del self._buckets[name]
        
        # Add folders that don't have metadata
        for item in self.storage_root.iterdir():
            if item.is_dir() and item.name not in self._buckets:
                bucket = Bucket.create_new(item.name)
                self._update_bucket_stats(bucket)
                self._buckets[bucket.name] = bucket
        
        self._save_buckets()
    
    def _save_buckets(self):
        """Save bucket metadata to storage"""
        data = [bucket.to_dict() for bucket in self._buckets.values()]
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving bucket metadata: {e}")
    
    def _update_bucket_stats(self, bucket: Bucket):
        """Update bucket object count and size"""
        bucket_path = self.storage_root / bucket.name
        if not bucket_path.exists():
            bucket.object_count = 0
            bucket.total_size = 0
            return
        
        count = 0
        total_size = 0
        
        for item in bucket_path.rglob('*'):
            if item.is_file() and item.name != '.metadata.json':
                count += 1
                total_size += item.stat().st_size
        
        bucket.object_count = count
        bucket.total_size = total_size
    
    def create_bucket(self, name: str, region: Optional[str] = None, tags: Optional[dict] = None) -> Bucket:
        """
        Create a new storage bucket with IAM checks
        
        Args:
            name: Bucket name (must be lowercase, alphanumeric with dashes)
            region: Region for bucket (defaults to current region)
            tags: Optional tags for the bucket
            
        Returns:
            Created bucket
            
        Raises:
            ValueError: If bucket name is invalid or already exists
            PermissionError: If user lacks storage:CreateBucket permission
        """
        region = region or get_current_region()
        resource_arn = f"arn:cloudsim:storage:{region}:bucket/{name}"
        
        # IAM permission check
        self._check_permission(Action.STORAGE_CREATE_BUCKET.value, resource_arn)
        
        # Validate bucket name (S3-like rules)
        if not name:
            raise ValueError("Bucket name cannot be empty")
        
        if not name.islower() or not all(c.isalnum() or c == '-' for c in name):
            raise ValueError("Bucket name must be lowercase alphanumeric with dashes only")
        
        if len(name) < 3 or len(name) > 63:
            raise ValueError("Bucket name must be between 3 and 63 characters")
        
        if name in self._buckets:
            raise ValueError(f"Bucket '{name}' already exists")
        
        # Create bucket folder
        bucket_path = self.storage_root / name
        bucket_path.mkdir(exist_ok=True)
        
        # Create bucket metadata with region and owner
        bucket = Bucket.create_new(name)
        bucket.region = region
        bucket.tags = tags or {}
        bucket.owner = "local-user"
        
        self._buckets[name] = bucket
        self._save_buckets()
        
        # Emit event
        emit_event(
            EventType.BUCKET_CREATED,
            source="storage",
            region=region,
            resource_id=name,
            resource_arn=resource_arn,
            details={"tags": tags or {}}
        )
        
        return bucket
    
    def delete_bucket(self, name: str, force: bool = False) -> bool:
        """
        Delete a storage bucket with IAM checks
        
        Args:
            name: Bucket name
            force: If True, delete even if bucket has objects
            
        Returns:
            True if deleted successfully
            
        Raises:
            ValueError: If bucket doesn't exist or has objects (without force)
            PermissionError: If user lacks storage:DeleteBucket permission
        """
        if name not in self._buckets:
            raise ValueError(f"Bucket '{name}' does not exist")
        
        bucket = self._buckets[name]
        region = getattr(bucket, 'region', get_current_region())
        resource_arn = f"arn:cloudsim:storage:{region}:bucket/{name}"
        
        # IAM permission check
        self._check_permission(Action.STORAGE_DELETE_BUCKET.value, resource_arn)
        
        self._update_bucket_stats(bucket)
        
        if bucket.object_count > 0 and not force:
            raise ValueError(f"Bucket '{name}' is not empty. Use force=True to delete anyway")
        
        # Delete bucket folder
        bucket_path = self.storage_root / name
        if bucket_path.exists():
            shutil.rmtree(bucket_path)
        
        # Remove from metadata
        del self._buckets[name]
        self._save_buckets()
        
        # Emit event
        emit_event(
            EventType.BUCKET_DELETED,
            source="storage",
            region=region,
            resource_id=name,
            resource_arn=resource_arn,
            details={}
        )
        
        return True
    
    def list_buckets(self, region: Optional[str] = None) -> List[Bucket]:
        """
        Get all buckets with IAM checks and optional region filtering
        
        Args:
            region: Optional region filter
        
        Returns:
            List of buckets with updated stats
            
        Raises:
            PermissionError: If user lacks storage:ListBuckets permission
        """
        # IAM permission check
        self._check_permission(Action.STORAGE_LIST_BUCKETS.value, "arn:cloudsim:storage:*:bucket/*")
        
        # Update stats for all buckets
        for bucket in self._buckets.values():
            self._update_bucket_stats(bucket)
        
        self._save_buckets()
        
        # Filter by region if specified
        buckets = list(self._buckets.values())
        if region:
            buckets = [b for b in buckets if getattr(b, 'region', None) == region]
        
        return buckets
    
    def get_bucket(self, name: str) -> Optional[Bucket]:
        """
        Get bucket by name
        
        Args:
            name: Bucket name
            
        Returns:
            Bucket or None if not found
        """
        bucket = self._buckets.get(name)
        if bucket:
            self._update_bucket_stats(bucket)
        return bucket
    
    def upload_object(self, bucket_name: str, file_path: str, object_key: Optional[str] = None) -> S3Object:
        """
        Upload a file to a bucket with IAM checks
        
        Args:
            bucket_name: Bucket name
            file_path: Local file path to upload
            object_key: Object name in bucket (defaults to filename)
            
        Returns:
            Created S3Object metadata
            
        Raises:
            ValueError: If bucket doesn't exist or file doesn't exist
            PermissionError: If user lacks storage:PutObject permission
        """
        if bucket_name not in self._buckets:
            raise ValueError(f"Bucket '{bucket_name}' does not exist")
        
        bucket = self._buckets[bucket_name]
        region = getattr(bucket, 'region', get_current_region())
        resource_arn = f"arn:cloudsim:storage:{region}:bucket/{bucket_name}/*"
        
        # IAM permission check
        self._check_permission(Action.STORAGE_PUT_OBJECT.value, resource_arn)
        
        source_path = Path(file_path)
        if not source_path.exists():
            raise ValueError(f"File '{file_path}' does not exist")
        
        # Use filename as key if not provided
        if object_key is None:
            object_key = source_path.name
        
        # Copy file to bucket
        bucket_path = self.storage_root / bucket_name
        dest_path = bucket_path / object_key
        
        # Create parent directories if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(source_path, dest_path)
        
        # Create object metadata
        file_size = dest_path.stat().st_size
        obj = S3Object.create_new(object_key, file_size, bucket_name)
        
        # Record storage usage
        record_storage_usage(resource_arn, file_size / (1024**3), region)  # Convert to GB
        
        # Emit event
        emit_event(
            EventType.OBJECT_CREATED,
            source="storage",
            region=region,
            resource_id=object_key,
            resource_arn=f"{resource_arn.rstrip('/*')}/{object_key}",
            details={"bucket": bucket_name, "size": file_size}
        )
        
        # Update bucket stats
        self._update_bucket_stats(self._buckets[bucket_name])
        self._save_buckets()
        
        return obj
    
    def download_object(self, bucket_name: str, object_key: str, dest_path: str):
        """
        Download an object from a bucket
        
        Args:
            bucket_name: Bucket name
            object_key: Object key in bucket
            dest_path: Local destination path
            
        Raises:
            ValueError: If bucket or object doesn't exist
        """
        if bucket_name not in self._buckets:
            raise ValueError(f"Bucket '{bucket_name}' does not exist")
        
        source_path = self.storage_root / bucket_name / object_key
        if not source_path.exists():
            raise ValueError(f"Object '{object_key}' does not exist in bucket '{bucket_name}'")
        
        shutil.copy2(source_path, dest_path)
    
    def delete_object(self, bucket_name: str, object_key: str) -> bool:
        """
        Delete an object from a bucket
        
        Args:
            bucket_name: Bucket name
            object_key: Object key to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            ValueError: If bucket or object doesn't exist
        """
        if bucket_name not in self._buckets:
            raise ValueError(f"Bucket '{bucket_name}' does not exist")
        
        object_path = self.storage_root / bucket_name / object_key
        if not object_path.exists():
            raise ValueError(f"Object '{object_key}' does not exist in bucket '{bucket_name}'")
        
        object_path.unlink()
        
        # Update bucket stats
        self._update_bucket_stats(self._buckets[bucket_name])
        self._save_buckets()
        
        return True
    
    def list_objects(self, bucket_name: str) -> List[S3Object]:
        """
        List all objects in a bucket
        
        Args:
            bucket_name: Bucket name
            
        Returns:
            List of S3Object metadata
            
        Raises:
            ValueError: If bucket doesn't exist
        """
        if bucket_name not in self._buckets:
            raise ValueError(f"Bucket '{bucket_name}' does not exist")
        
        bucket_path = self.storage_root / bucket_name
        objects = []
        
        for item in bucket_path.rglob('*'):
            if item.is_file():
                relative_path = item.relative_to(bucket_path)
                object_key = str(relative_path).replace('\\', '/')
                file_size = item.stat().st_size
                
                obj = S3Object.create_new(object_key, file_size, bucket_name)
                objects.append(obj)
        
        return objects
