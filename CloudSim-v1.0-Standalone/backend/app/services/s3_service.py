"""
S3 Service

Provides S3-like object storage operations with filesystem backing.
Handles bucket and object CRUD operations, file uploads/downloads, and IAM integration.
"""

import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, BinaryIO
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.bucket import Bucket
from app.models.s3_object import S3Object
from app.core.resource_ids import generate_id, ResourceType
from app.core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    ConflictError,
    StorageError
)


class S3Service:
    """
    S3 Storage Service
    
    Provides S3-like object storage with filesystem backing.
    
    Storage structure:
        /var/cloudsim/s3/{account_id}/{bucket_name}/{object_key}
    
    Features:
        - Bucket CRUD operations
        - Object upload/download/delete
        - Filesystem storage backend
        - MD5 checksums (ETags)
        - Content type detection
        - Metadata and tags
    
    Example:
        service = S3Service("/var/cloudsim/s3")
        
        # Create bucket
        bucket = service.create_bucket(
            account_id="acc_abc123",
            bucket_name="my-data-bucket",
            region="us-east-1"
        )
        
        # Upload object
        with open("report.pdf", "rb") as f:
            obj = service.put_object(
                account_id="acc_abc123",
                bucket_name="my-data-bucket",
                object_key="reports/2026/report.pdf",
                content=f,
                content_type="application/pdf"
            )
        
        # Download object
        content = service.get_object(
            account_id="acc_abc123",
            bucket_name="my-data-bucket",
            object_key="reports/2026/report.pdf"
        )
    """
    
    def __init__(self, base_path: str = "/var/cloudsim/s3"):
        """
        Initialize S3 service.
        
        Args:
            base_path: Root directory for S3 storage
        """
        self.base_path = Path(base_path)
        self._ensure_base_directory()
    
    def _ensure_base_directory(self):
        """Create base storage directory if it doesn't exist."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(f"Failed to create storage directory: {str(e)}")
    
    def _validate_bucket_name(self, bucket_name: str):
        """
        Validate bucket name according to S3 rules.
        
        Rules:
            - 3-63 characters
            - Lowercase letters, numbers, hyphens
            - Start and end with letter or number
            - No consecutive hyphens
            - No IP address format
        
        Args:
            bucket_name: Bucket name to validate
        
        Raises:
            ValidationError: If bucket name is invalid
        """
        if len(bucket_name) < 3 or len(bucket_name) > 63:
            raise ValidationError("Bucket name must be 3-63 characters")
        
        if not bucket_name[0].isalnum() or not bucket_name[-1].isalnum():
            raise ValidationError("Bucket name must start and end with letter or number")
        
        if not all(c.islower() or c.isdigit() or c == '-' for c in bucket_name):
            raise ValidationError("Bucket name must contain only lowercase letters, numbers, and hyphens")
        
        if '--' in bucket_name:
            raise ValidationError("Bucket name cannot contain consecutive hyphens")
        
        # Check if it looks like an IP address
        parts = bucket_name.split('.')
        if len(parts) == 4 and all(p.isdigit() for p in parts):
            raise ValidationError("Bucket name cannot be formatted as an IP address")
    
    def _get_bucket_path(self, account_id: str, bucket_name: str) -> Path:
        """Get filesystem path for bucket."""
        return self.base_path / account_id / bucket_name
    
    def _get_object_path(self, account_id: str, bucket_name: str, object_key: str) -> Path:
        """Get filesystem path for object."""
        return self._get_bucket_path(account_id, bucket_name) / object_key
    
    def _calculate_etag(self, file_path: Path) -> str:
        """Calculate MD5 hash (ETag) for file."""
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def _detect_content_type(self, object_key: str, content_type: Optional[str] = None) -> str:
        """Detect or validate content type."""
        if content_type:
            return content_type
        
        # Guess from file extension
        guessed_type, _ = mimetypes.guess_type(object_key)
        return guessed_type or "application/octet-stream"
    
    # Bucket Operations
    
    def create_bucket(
        self,
        db: Session,
        account_id: str,
        bucket_name: str,
        region: str = "us-east-1",
        tags: Optional[dict] = None
    ) -> Bucket:
        """
        Create a new S3 bucket.
        
        Args:
            db: Database session
            account_id: Owner account ID
            bucket_name: Unique bucket name
            region: AWS region
            tags: Optional tags
        
        Returns:
            Created bucket
        
        Raises:
            ValidationError: If bucket name is invalid
            ConflictError: If bucket already exists
            StorageError: If filesystem operation fails
        """
        # Validate bucket name
        self._validate_bucket_name(bucket_name)
        
        # Check if bucket already exists
        existing = db.query(Bucket).filter(Bucket.bucket_name == bucket_name).first()
        if existing:
            raise ConflictError(f"Bucket '{bucket_name}' already exists")
        
        # Create filesystem directory
        bucket_path = self._get_bucket_path(account_id, bucket_name)
        try:
            bucket_path.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise ConflictError(f"Bucket directory already exists")
        except Exception as e:
            raise StorageError(f"Failed to create bucket directory: {str(e)}")
        
        # Create bucket record
        bucket = Bucket(
            bucket_name=bucket_name,
            account_id=account_id,
            region=region,
            versioning_enabled=False,
            public_access_blocked=True,
            filesystem_path=str(bucket_path),
            tags=str(tags) if tags else None,
            created_at=datetime.utcnow()
        )
        
        db.add(bucket)
        db.commit()
        db.refresh(bucket)
        
        return bucket
    
    def get_bucket(self, db: Session, account_id: str, bucket_name: str) -> Bucket:
        """
        Get bucket by name.
        
        Args:
            db: Database session
            account_id: Owner account ID
            bucket_name: Bucket name
        
        Returns:
            Bucket
        
        Raises:
            ResourceNotFoundError: If bucket not found
        """
        bucket = db.query(Bucket).filter(
            Bucket.bucket_name == bucket_name,
            Bucket.account_id == account_id
        ).first()
        
        if not bucket:
            raise ResourceNotFoundError(f"Bucket '{bucket_name}' not found")
        
        return bucket
    
    def list_buckets(
        self,
        db: Session,
        account_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[Bucket]:
        """
        List buckets for account.
        
        Args:
            db: Database session
            account_id: Owner account ID
            limit: Maximum results
            offset: Pagination offset
        
        Returns:
            List of buckets
        """
        return db.query(Bucket).filter(
            Bucket.account_id == account_id
        ).order_by(
            Bucket.created_at.desc()
        ).limit(limit).offset(offset).all()
    
    def delete_bucket(self, db: Session, account_id: str, bucket_name: str, force: bool = False):
        """
        Delete bucket.
        
        Args:
            db: Database session
            account_id: Owner account ID
            bucket_name: Bucket name
            force: Force delete even if not empty
        
        Raises:
            ResourceNotFoundError: If bucket not found
            ConflictError: If bucket not empty and force=False
            StorageError: If filesystem operation fails
        """
        bucket = self.get_bucket(db, account_id, bucket_name)
        
        # Check if bucket is empty
        if not force:
            object_count = db.query(func.count(S3Object.object_id)).filter(
                S3Object.bucket_name == bucket_name,
                S3Object.account_id == account_id
            ).scalar()
            
            if object_count > 0:
                raise ConflictError(
                    f"Bucket '{bucket_name}' is not empty. "
                    f"Delete all objects first or use force=true"
                )
        
        # Delete filesystem directory
        bucket_path = Path(bucket.filesystem_path)
        try:
            if bucket_path.exists():
                shutil.rmtree(bucket_path)
        except Exception as e:
            raise StorageError(f"Failed to delete bucket directory: {str(e)}")
        
        # Delete all objects (if force)
        if force:
            db.query(S3Object).filter(
                S3Object.bucket_name == bucket_name,
                S3Object.account_id == account_id
            ).delete()
        
        # Delete bucket record
        db.delete(bucket)
        db.commit()
    
    # Object Operations
    
    def put_object(
        self,
        db: Session,
        account_id: str,
        bucket_name: str,
        object_key: str,
        content: BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
        tags: Optional[dict] = None
    ) -> S3Object:
        """
        Upload object to bucket.
        
        Args:
            db: Database session
            account_id: Owner account ID
            bucket_name: Target bucket
            object_key: Object key/path
            content: File-like object with binary content
            content_type: MIME type (auto-detected if None)
            metadata: Custom metadata
            tags: Object tags
        
        Returns:
            Created object
        
        Raises:
            ResourceNotFoundError: If bucket not found
            ValidationError: If object key is invalid
            StorageError: If filesystem operation fails
        """
        # Verify bucket exists
        bucket = self.get_bucket(db, account_id, bucket_name)
        
        # Validate object key
        if not object_key or len(object_key) > 1024:
            raise ValidationError("Object key must be 1-1024 characters")
        
        # Get object path
        object_path = self._get_object_path(account_id, bucket_name, object_key)
        
        # Create parent directories
        try:
            object_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(f"Failed to create object directory: {str(e)}")
        
        # Write content to file
        try:
            with open(object_path, "wb") as f:
                shutil.copyfileobj(content, f)
        except Exception as e:
            raise StorageError(f"Failed to write object: {str(e)}")
        
        # Calculate size and ETag
        size_bytes = object_path.stat().st_size
        etag = self._calculate_etag(object_path)
        
        # Detect content type
        detected_content_type = self._detect_content_type(object_key, content_type)
        
        # Check if versioning is enabled
        from app.services.s3_advanced_service import S3AdvancedService
        advanced_service = S3AdvancedService()
        
        if bucket.versioning_enabled:
            # Versioning enabled - create new version
            
            # Mark all existing versions as not latest
            db.query(S3Object).filter(
                S3Object.bucket_name == bucket_name,
                S3Object.account_id == account_id,
                S3Object.object_key == object_key,
                S3Object.is_latest == True
            ).update({"is_latest": False})
            
            # Generate version ID
            version_id = advanced_service.generate_version_id()
            
            # Create versioned object path
            versioned_path = object_path.parent / f"{object_path.name}.{version_id}"
            object_path.rename(versioned_path)
            object_path = versioned_path
            
            # Create new version
            object_id = generate_id(ResourceType.S3_OBJECT)
            
            s3_object = S3Object(
                object_id=object_id,
                bucket_name=bucket_name,
                account_id=account_id,
                object_key=object_key,
                size_bytes=size_bytes,
                content_type=detected_content_type,
                etag=etag,
                filesystem_path=str(object_path),
                storage_class="STANDARD",
                version_id=version_id,
                is_latest=True,
                is_delete_marker=False,
                object_metadata=str(metadata) if metadata else None,
                tags=str(tags) if tags else None,
                created_at=datetime.utcnow(),
                last_modified=datetime.utcnow()
            )
            
            db.add(s3_object)
            db.commit()
            db.refresh(s3_object)
            
            return s3_object
        else:
            # Versioning disabled - overwrite existing or create new
            existing = db.query(S3Object).filter(
                S3Object.bucket_name == bucket_name,
                S3Object.account_id == account_id,
                S3Object.object_key == object_key
            ).first()
            
            if existing:
                # Update existing object
                existing.size_bytes = size_bytes
                existing.content_type = detected_content_type
                existing.etag = etag
                existing.filesystem_path = str(object_path)
                existing.object_metadata = str(metadata) if metadata else None
                existing.tags = str(tags) if tags else None
                existing.last_modified = datetime.utcnow()
                
                db.commit()
                db.refresh(existing)
                return existing
            else:
                # Create new object
                object_id = generate_id(ResourceType.S3_OBJECT)
                
                s3_object = S3Object(
                    object_id=object_id,
                    bucket_name=bucket_name,
                    account_id=account_id,
                    object_key=object_key,
                    size_bytes=size_bytes,
                    content_type=detected_content_type,
                    etag=etag,
                    filesystem_path=str(object_path),
                    storage_class="STANDARD",
                    version_id=None,
                    is_latest=True,
                    is_delete_marker=False,
                    object_metadata=str(metadata) if metadata else None,
                    tags=str(tags) if tags else None,
                    created_at=datetime.utcnow(),
                    last_modified=datetime.utcnow()
                )
                
                db.add(s3_object)
                db.commit()
                db.refresh(s3_object)
                
                return s3_object
    
    def get_object(
        self,
        db: Session,
        account_id: str,
        bucket_name: str,
        object_key: str
    ) -> tuple[S3Object, BinaryIO]:
        """
        Download object from bucket.
        
        Args:
            db: Database session
            account_id: Owner account ID
            bucket_name: Source bucket
            object_key: Object key/path
        
        Returns:
            Tuple of (object metadata, file handle)
        
        Raises:
            ResourceNotFoundError: If object not found
            StorageError: If filesystem operation fails
        """
        # Get object metadata
        s3_object = db.query(S3Object).filter(
            S3Object.bucket_name == bucket_name,
            S3Object.account_id == account_id,
            S3Object.object_key == object_key
        ).first()
        
        if not s3_object:
            raise ResourceNotFoundError(
                f"Object '{object_key}' not found in bucket '{bucket_name}'"
            )
        
        # Open file
        object_path = Path(s3_object.filesystem_path)
        if not object_path.exists():
            raise StorageError(f"Object file not found: {object_path}")
        
        try:
            file_handle = open(object_path, "rb")
            return s3_object, file_handle
        except Exception as e:
            raise StorageError(f"Failed to read object: {str(e)}")
    
    def get_object_metadata(
        self,
        db: Session,
        account_id: str,
        bucket_name: str,
        object_key: str
    ) -> S3Object:
        """
        Get object metadata without downloading content.
        
        Args:
            db: Database session
            account_id: Owner account ID
            bucket_name: Source bucket
            object_key: Object key/path
        
        Returns:
            Object metadata
        
        Raises:
            ResourceNotFoundError: If object not found
        """
        s3_object = db.query(S3Object).filter(
            S3Object.bucket_name == bucket_name,
            S3Object.account_id == account_id,
            S3Object.object_key == object_key
        ).first()
        
        if not s3_object:
            raise ResourceNotFoundError(
                f"Object '{object_key}' not found in bucket '{bucket_name}'"
            )
        
        return s3_object
    
    def list_objects(
        self,
        db: Session,
        account_id: str,
        bucket_name: str,
        prefix: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> list[S3Object]:
        """
        List objects in bucket.
        
        Args:
            db: Database session
            account_id: Owner account ID
            bucket_name: Source bucket
            prefix: Filter by key prefix (e.g., "folder/")
            limit: Maximum results
            offset: Pagination offset
        
        Returns:
            List of objects
        
        Raises:
            ResourceNotFoundError: If bucket not found
        """
        # Verify bucket exists
        self.get_bucket(db, account_id, bucket_name)
        
        # Build query
        query = db.query(S3Object).filter(
            S3Object.bucket_name == bucket_name,
            S3Object.account_id == account_id
        )
        
        # Apply prefix filter
        if prefix:
            query = query.filter(S3Object.object_key.like(f"{prefix}%"))
        
        # Execute with pagination
        return query.order_by(
            S3Object.object_key
        ).limit(limit).offset(offset).all()
    
    def delete_object(
        self,
        db: Session,
        account_id: str,
        bucket_name: str,
        object_key: str,
        version_id: str = None
    ):
        """
        Delete object from bucket or create delete marker if versioning enabled.
        
        Args:
            db: Database session
            account_id: Owner account ID
            bucket_name: Source bucket
            object_key: Object key/path
            version_id: Specific version to delete (optional)
        
        Raises:
            ResourceNotFoundError: If object not found
            StorageError: If filesystem operation fails
        """
        # Get bucket to check versioning
        bucket = self.get_bucket(db, account_id, bucket_name)
        
        from app.services.s3_advanced_service import S3AdvancedService
        advanced_service = S3AdvancedService()
        
        if version_id:
            # Delete specific version
            advanced_service.delete_version(db, account_id, bucket_name, object_key, version_id)
            return
        
        if bucket.versioning_enabled:
            # Create delete marker
            
            # Mark all existing versions as not latest
            db.query(S3Object).filter(
                S3Object.bucket_name == bucket_name,
                S3Object.account_id == account_id,
                S3Object.object_key == object_key,
                S3Object.is_latest == True
            ).update({"is_latest": False})
            
            # Generate version ID
            version_id = advanced_service.generate_version_id()
            
            # Create delete marker (no filesystem file)
            object_id = generate_id(ResourceType.S3_OBJECT)
            
            delete_marker = S3Object(
                object_id=object_id,
                bucket_name=bucket_name,
                account_id=account_id,
                object_key=object_key,
                size_bytes=0,
                content_type="application/x-delete-marker",
                etag="",
                filesystem_path="",
                storage_class="STANDARD",
                version_id=version_id,
                is_latest=True,
                is_delete_marker=True,
                created_at=datetime.utcnow(),
                last_modified=datetime.utcnow()
            )
            
            db.add(delete_marker)
            db.commit()
        else:
            # Versioning disabled - permanent delete
            s3_object = self.get_object_metadata(db, account_id, bucket_name, object_key)
            
            # Delete file
            object_path = Path(s3_object.filesystem_path)
            try:
                if object_path.exists():
                    object_path.unlink()
            except Exception as e:
                raise StorageError(f"Failed to delete object file: {str(e)}")
            
            # Delete record
            db.delete(s3_object)
            db.commit()

