"""
REST API routes for S3 advanced features (versioning, lifecycle, policies).
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError
)
from app.middleware.auth import get_current_user
from app.models.iam_user import User
from app.services.s3_advanced_service import S3AdvancedService
from app.schemas.s3_advanced import (
    VersioningConfiguration,
    VersioningConfigurationResponse,
    ListObjectVersionsResponse,
    ObjectVersion,
    DeleteVersionRequest,
    LifecycleConfiguration,
    LifecycleConfigurationResponse,
    LifecycleEvaluationResult,
    BucketPolicyRequest,
    BucketPolicyResponse,
    BucketPolicyDocument,
    EvaluatePolicyRequest,
    EvaluatePolicyResponse
)
import json

router = APIRouter(prefix="/s3-advanced", tags=["S3 Advanced"])
s3_advanced_service = S3AdvancedService()


# ==================== Versioning Endpoints ====================

@router.put(
    "/buckets/{bucket_name}/versioning",
    response_model=VersioningConfigurationResponse,
    summary="Enable or suspend versioning",
    description="Configure bucket versioning (Enabled or Suspended)"
)
def put_bucket_versioning(
    bucket_name: str,
    config: VersioningConfiguration,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enable or suspend bucket versioning."""
    try:
        if config.status == "Enabled":
            bucket = s3_advanced_service.enable_versioning(
                db,
                current_user.account_id,
                bucket_name
            )
        elif config.status == "Suspended":
            bucket = s3_advanced_service.suspend_versioning(
                db,
                current_user.account_id,
                bucket_name
            )
        else:
            raise ValidationError(f"Invalid status: {config.status}. Must be 'Enabled' or 'Suspended'")
        
        return VersioningConfigurationResponse(
            status="Enabled" if bucket.versioning_enabled else "Suspended"
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get(
    "/buckets/{bucket_name}/versioning",
    response_model=VersioningConfigurationResponse,
    summary="Get versioning configuration",
    description="Get current bucket versioning status"
)
def get_bucket_versioning(
    bucket_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get bucket versioning status."""
    try:
        from app.services.s3_service import S3Service
        s3_service = S3Service()
        bucket = s3_service.get_bucket(db, current_user.account_id, bucket_name)
        
        return VersioningConfigurationResponse(
            status="Enabled" if bucket.versioning_enabled else "Suspended"
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get(
    "/buckets/{bucket_name}/objects/{object_key:path}/versions",
    response_model=ListObjectVersionsResponse,
    summary="List object versions",
    description="List all versions of an object"
)
def list_object_versions(
    bucket_name: str,
    object_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all versions of an object."""
    try:
        versions = s3_advanced_service.list_object_versions(
            db,
            current_user.account_id,
            bucket_name,
            object_key
        )
        
        version_list = [
            ObjectVersion(
                version_id=v.version_id,
                object_key=v.object_key,
                is_latest=v.is_latest,
                is_delete_marker=v.is_delete_marker,
                size_bytes=v.size_bytes,
                etag=v.etag,
                last_modified=v.last_modified,
                storage_class=v.storage_class
            )
            for v in versions
        ]
        
        return ListObjectVersionsResponse(
            object_key=object_key,
            versions=version_list
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete(
    "/buckets/{bucket_name}/objects/{object_key:path}/versions/{version_id}",
    summary="Delete specific version",
    description="Permanently delete a specific object version"
)
def delete_object_version(
    bucket_name: str,
    object_key: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific object version."""
    try:
        s3_advanced_service.delete_version(
            db,
            current_user.account_id,
            bucket_name,
            object_key,
            version_id
        )
        
        return {"message": f"Version {version_id} deleted successfully"}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ==================== Lifecycle Endpoints ====================

@router.put(
    "/buckets/{bucket_name}/lifecycle",
    response_model=LifecycleConfigurationResponse,
    summary="Put lifecycle configuration",
    description="Configure bucket lifecycle rules"
)
def put_bucket_lifecycle(
    bucket_name: str,
    config: LifecycleConfiguration,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Configure bucket lifecycle rules."""
    try:
        # Convert to dict for service
        rules_dict = [rule.model_dump() for rule in config.rules]
        
        bucket = s3_advanced_service.put_lifecycle_configuration(
            db,
            current_user.account_id,
            bucket_name,
            rules_dict
        )
        
        # Parse back for response
        lifecycle_rules = json.loads(bucket.lifecycle_rules) if bucket.lifecycle_rules else []
        
        return LifecycleConfigurationResponse(
            rules=lifecycle_rules
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get(
    "/buckets/{bucket_name}/lifecycle",
    response_model=LifecycleConfigurationResponse,
    summary="Get lifecycle configuration",
    description="Get current bucket lifecycle rules"
)
def get_bucket_lifecycle(
    bucket_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get bucket lifecycle configuration."""
    try:
        from app.services.s3_service import S3Service
        s3_service = S3Service()
        bucket = s3_service.get_bucket(db, current_user.account_id, bucket_name)
        
        if not bucket.lifecycle_rules:
            return LifecycleConfigurationResponse(rules=[])
        
        rules = json.loads(bucket.lifecycle_rules)
        return LifecycleConfigurationResponse(rules=rules)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete(
    "/buckets/{bucket_name}/lifecycle",
    summary="Delete lifecycle configuration",
    description="Remove all lifecycle rules from bucket"
)
def delete_bucket_lifecycle(
    bucket_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete bucket lifecycle configuration."""
    try:
        s3_advanced_service.delete_lifecycle_configuration(
            db,
            current_user.account_id,
            bucket_name
        )
        
        return {"message": "Lifecycle configuration deleted"}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post(
    "/buckets/{bucket_name}/lifecycle/evaluate",
    response_model=LifecycleEvaluationResult,
    summary="Evaluate lifecycle rules",
    description="Evaluate lifecycle rules and return objects to expire/transition"
)
def evaluate_bucket_lifecycle(
    bucket_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Evaluate lifecycle rules for bucket."""
    try:
        result = s3_advanced_service.evaluate_lifecycle_rules(
            db,
            current_user.account_id,
            bucket_name
        )
        
        return LifecycleEvaluationResult(
            expired=result["expired"],
            transitioned=result["transitioned"]
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ==================== Bucket Policy Endpoints ====================

@router.put(
    "/buckets/{bucket_name}/policy",
    response_model=BucketPolicyResponse,
    summary="Put bucket policy",
    description="Attach a policy to a bucket"
)
def put_bucket_policy(
    bucket_name: str,
    request: BucketPolicyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Attach policy to bucket."""
    try:
        # Convert policy to dict
        policy_dict = request.policy.model_dump()
        
        bucket_policy = s3_advanced_service.put_bucket_policy(
            db,
            current_user.account_id,
            bucket_name,
            policy_dict
        )
        
        # Parse policy document
        policy_doc = json.loads(bucket_policy.policy_document)
        
        return BucketPolicyResponse(
            policy_id=bucket_policy.policy_id,
            bucket_name=bucket_policy.bucket_name,
            policy=BucketPolicyDocument(**policy_doc),
            created_at=bucket_policy.created_at,
            updated_at=bucket_policy.updated_at
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get(
    "/buckets/{bucket_name}/policy",
    response_model=BucketPolicyResponse,
    summary="Get bucket policy",
    description="Get the policy attached to a bucket"
)
def get_bucket_policy(
    bucket_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get bucket policy."""
    try:
        bucket_policy = s3_advanced_service.get_bucket_policy(
            db,
            current_user.account_id,
            bucket_name
        )
        
        # Parse policy document
        policy_doc = json.loads(bucket_policy.policy_document)
        
        return BucketPolicyResponse(
            policy_id=bucket_policy.policy_id,
            bucket_name=bucket_policy.bucket_name,
            policy=BucketPolicyDocument(**policy_doc),
            created_at=bucket_policy.created_at,
            updated_at=bucket_policy.updated_at
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete(
    "/buckets/{bucket_name}/policy",
    summary="Delete bucket policy",
    description="Remove the policy from a bucket"
)
def delete_bucket_policy(
    bucket_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete bucket policy."""
    try:
        s3_advanced_service.delete_bucket_policy(
            db,
            current_user.account_id,
            bucket_name
        )
        
        return {"message": "Bucket policy deleted"}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post(
    "/buckets/{bucket_name}/policy/evaluate",
    response_model=EvaluatePolicyResponse,
    summary="Evaluate bucket policy",
    description="Evaluate whether a principal can perform an action"
)
def evaluate_bucket_policy(
    bucket_name: str,
    request: EvaluatePolicyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Evaluate bucket policy for an action."""
    try:
        allowed = s3_advanced_service.evaluate_bucket_policy(
            db,
            bucket_name,
            request.principal_arn,
            request.action,
            request.resource
        )
        
        return EvaluatePolicyResponse(
            allowed=allowed,
            reason="Explicit allow matched" if allowed else "No matching allow statement or explicit deny"
        )
    except ResourceNotFoundError as e:
        # No policy means default deny
        return EvaluatePolicyResponse(
            allowed=False,
            reason="No bucket policy found"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

