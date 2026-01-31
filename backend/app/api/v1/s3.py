"""
S3 API Routes

IAM-protected endpoints for S3 bucket and object operations.
"""

from io import BytesIO
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.middleware.auth import get_current_account
from app.middleware.authorization import RequirePermission
from app.models.iam_account import Account
from app.models.bucket import Bucket
from app.models.s3_object import S3Object
from app.services.s3_service import S3Service
from app.schemas.s3 import (
    CreateBucketRequest,
    BucketResponse,
    ListBucketsResponse,
    DeleteBucketRequest,
    PutObjectRequest,
    ObjectResponse,
    ListObjectsRequest,
    ListObjectsResponse,
    GetObjectResponse,
    DeleteObjectsRequest,
    DeleteObjectsResponse
)
from app.core.exceptions import ResourceNotFoundError, ValidationError, ConflictError


router = APIRouter(prefix="/s3", tags=["S3"])
s3_service = S3Service()


# Bucket Operations

@router.post("/buckets", response_model=BucketResponse)

async def create_bucket(
    request: CreateBucketRequest,
    db: Session = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Create a new S3 bucket.
    
    Requires: s3:CreateBucket
    
    Args:
        request: Bucket creation parameters
        db: Database session
        current_account: Authenticated account
    
    Returns:
        Created bucket information
    
    Raises:
        ValidationError: If bucket name is invalid
        ConflictError: If bucket already exists
    """
    bucket = s3_service.create_bucket(
        db=db,
        account_id=current_account.account_id,
        bucket_name=request.bucket_name,
        region=request.region,
        tags=request.tags
    )
    
    return bucket


@router.get("/buckets", response_model=ListBucketsResponse)

async def list_buckets(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    List all buckets for the account.
    
    Requires: s3:ListBuckets
    
    Args:
        limit: Maximum results
        offset: Pagination offset
        db: Database session
        current_account: Authenticated account
    
    Returns:
        List of buckets with total count
    """
    buckets = s3_service.list_buckets(
        db=db,
        account_id=current_account.account_id,
        limit=limit,
        offset=offset
    )
    
    # Get total count
    total = db.query(func.count(Bucket.bucket_name)).filter(
        Bucket.account_id == current_account.account_id
    ).scalar()
    
    return ListBucketsResponse(
        buckets=buckets,
        total=total
    )


@router.get("/buckets/{bucket_name}", response_model=BucketResponse)

async def get_bucket(
    bucket_name: str,
    db: Session = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Get bucket information.
    
    Requires: s3:GetBucket
    
    Args:
        bucket_name: Bucket name
        db: Database session
        current_account: Authenticated account
    
    Returns:
        Bucket information
    
    Raises:
        ResourceNotFoundError: If bucket not found
    """
    bucket = s3_service.get_bucket(
        db=db,
        account_id=current_account.account_id,
        bucket_name=bucket_name
    )
    
    return bucket


@router.delete("/buckets/{bucket_name}")

async def delete_bucket(
    bucket_name: str,
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Delete a bucket.
    
    Requires: s3:DeleteBucket
    
    Args:
        bucket_name: Bucket name
        force: Force delete even if not empty
        db: Database session
        current_account: Authenticated account
    
    Returns:
        Success message
    
    Raises:
        ResourceNotFoundError: If bucket not found
        ConflictError: If bucket not empty and force=False
    """
    s3_service.delete_bucket(
        db=db,
        account_id=current_account.account_id,
        bucket_name=bucket_name,
        force=force
    )
    
    return {"message": f"Bucket '{bucket_name}' deleted successfully"}


# Object Operations

@router.post("/buckets/{bucket_name}/objects", response_model=ObjectResponse)

async def put_object(
    bucket_name: str,
    object_key: str = Query(..., description="Object key/path"),
    file: UploadFile = File(...),
    content_type: str = Query(default=None),
    db: Session = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Upload an object to a bucket.
    
    Requires: s3:PutObject
    
    Args:
        bucket_name: Target bucket
        object_key: Object key/path
        file: File to upload
        content_type: MIME type (auto-detected if not provided)
        db: Database session
        current_account: Authenticated account
    
    Returns:
        Created object information
    
    Raises:
        ResourceNotFoundError: If bucket not found
        ValidationError: If object key is invalid
    """
    # Use file's content_type if not explicitly provided
    if content_type is None:
        content_type = file.content_type
    
    # Read file content
    content = await file.read()
    content_io = BytesIO(content)
    
    # Upload object
    s3_object = s3_service.put_object(
        db=db,
        account_id=current_account.account_id,
        bucket_name=bucket_name,
        object_key=object_key,
        content=content_io,
        content_type=content_type,
        metadata=None,
        tags=None
    )
    
    return s3_object


@router.get("/buckets/{bucket_name}/objects", response_model=ListObjectsResponse)

async def list_objects(
    bucket_name: str,
    prefix: str = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    List objects in a bucket.
    
    Requires: s3:ListObjects
    
    Args:
        bucket_name: Source bucket
        prefix: Filter by key prefix (e.g., "folder/")
        limit: Maximum results
        offset: Pagination offset
        db: Database session
        current_account: Authenticated account
    
    Returns:
        List of objects with total count
    
    Raises:
        ResourceNotFoundError: If bucket not found
    """
    objects = s3_service.list_objects(
        db=db,
        account_id=current_account.account_id,
        bucket_name=bucket_name,
        prefix=prefix,
        limit=limit,
        offset=offset
    )
    
    # Get total count
    query = db.query(func.count(S3Object.object_id)).filter(
        S3Object.bucket_name == bucket_name,
        S3Object.account_id == current_account.account_id
    )
    
    if prefix:
        query = query.filter(S3Object.object_key.like(f"{prefix}%"))
    
    total = query.scalar()
    
    return ListObjectsResponse(
        objects=objects,
        total=total,
        bucket_name=bucket_name
    )


@router.get("/buckets/{bucket_name}/objects/{object_key:path}")

async def get_object(
    bucket_name: str,
    object_key: str,
    download: bool = Query(default=True, description="Download file content"),
    db: Session = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Get an object from a bucket.
    
    Requires: s3:GetObject
    
    Args:
        bucket_name: Source bucket
        object_key: Object key/path
        download: If True, download content; if False, return metadata only
        db: Database session
        current_account: Authenticated account
    
    Returns:
        Object content (if download=True) or metadata (if download=False)
    
    Raises:
        ResourceNotFoundError: If object not found
    """
    if download:
        # Download object content
        s3_object, file_handle = s3_service.get_object(
            db=db,
            account_id=current_account.account_id,
            bucket_name=bucket_name,
            object_key=object_key
        )
        
        # Return as streaming response
        return StreamingResponse(
            file_handle,
            media_type=s3_object.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{object_key.split("/")[-1]}"',
                "ETag": s3_object.etag,
                "Content-Length": str(s3_object.size_bytes)
            }
        )
    else:
        # Return metadata only
        s3_object = s3_service.get_object_metadata(
            db=db,
            account_id=current_account.account_id,
            bucket_name=bucket_name,
            object_key=object_key
        )
        
        return GetObjectResponse(object=s3_object)


@router.delete("/buckets/{bucket_name}/objects/{object_key:path}")

async def delete_object(
    bucket_name: str,
    object_key: str,
    db: Session = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Delete an object from a bucket.
    
    Requires: s3:DeleteObject
    
    Args:
        bucket_name: Source bucket
        object_key: Object key/path
        db: Database session
        current_account: Authenticated account
    
    Returns:
        Success message
    
    Raises:
        ResourceNotFoundError: If object not found
    """
    s3_service.delete_object(
        db=db,
        account_id=current_account.account_id,
        bucket_name=bucket_name,
        object_key=object_key
    )
    
    return {"message": f"Object '{object_key}' deleted successfully"}


@router.post("/buckets/{bucket_name}/delete-objects", response_model=DeleteObjectsResponse)

async def delete_objects(
    bucket_name: str,
    request: DeleteObjectsRequest,
    db: Session = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Delete multiple objects from a bucket.
    
    Requires: s3:DeleteObject
    
    Args:
        bucket_name: Source bucket
        request: List of object keys to delete
        db: Database session
        current_account: Authenticated account
    
    Returns:
        List of deleted objects and errors
    """
    deleted = []
    errors = []
    
    for object_key in request.object_keys:
        try:
            s3_service.delete_object(
                db=db,
                account_id=current_account.account_id,
                bucket_name=bucket_name,
                object_key=object_key
            )
            deleted.append(object_key)
        except Exception as e:
            errors.append({
                "object_key": object_key,
                "error": str(e)
            })
    
    return DeleteObjectsResponse(
        deleted=deleted,
        errors=errors
    )


