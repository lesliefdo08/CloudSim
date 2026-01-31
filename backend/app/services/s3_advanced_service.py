"""
S3 Advanced Features Service

Handles versioning, lifecycle rules, and bucket policies.
"""

import json
import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models.bucket import Bucket
from app.models.s3_object import S3Object
from app.models.bucket_policy import BucketPolicy
from app.core.resource_ids import generate_id, ResourceType
from app.core.exceptions import ValidationError, ResourceNotFoundError, ConflictError


class S3AdvancedService:
    """
    S3 Advanced Features Service
    
    Provides versioning, lifecycle, and bucket policy management.
    
    Features:
        - Object versioning with version IDs
        - Lifecycle rules for automatic archiving/deletion
        - Bucket policies for cross-account access
        - Policy evaluation for access control
    """
    
    # Versioning Operations
    
    def enable_versioning(self, db: Session, account_id: str, bucket_name: str) -> Bucket:
        """
        Enable versioning for a bucket.
        
        Args:
            db: Database session
            account_id: Owner account ID
            bucket_name: Target bucket
        
        Returns:
            Updated bucket
        
        Raises:
            ResourceNotFoundError: If bucket not found
        """
        bucket = db.query(Bucket).filter(
            Bucket.bucket_name == bucket_name,
            Bucket.account_id == account_id
        ).first()
        
        if not bucket:
            raise ResourceNotFoundError(f"Bucket '{bucket_name}' not found")
        
        bucket.versioning_enabled = True
        db.commit()
        db.refresh(bucket)
        
        return bucket
    
    def suspend_versioning(self, db: Session, account_id: str, bucket_name: str) -> Bucket:
        """
        Suspend versioning for a bucket.
        
        Note: Existing versions are preserved, but new uploads won't create versions.
        
        Args:
            db: Database session
            account_id: Owner account ID
            bucket_name: Target bucket
        
        Returns:
            Updated bucket
        
        Raises:
            ResourceNotFoundError: If bucket not found
        """
        bucket = db.query(Bucket).filter(
            Bucket.bucket_name == bucket_name,
            Bucket.account_id == account_id
        ).first()
        
        if not bucket:
            raise ResourceNotFoundError(f"Bucket '{bucket_name}' not found")
        
        bucket.versioning_enabled = False
        db.commit()
        db.refresh(bucket)
        
        return bucket
    
    def generate_version_id(self) -> str:
        """Generate a version ID for an object."""
        return secrets.token_hex(16)  # 32-character hex string
    
    def list_object_versions(
        self,
        db: Session,
        account_id: str,
        bucket_name: str,
        object_key: str
    ) -> list[S3Object]:
        """
        List all versions of an object.
        
        Args:
            db: Database session
            account_id: Owner account ID
            bucket_name: Source bucket
            object_key: Object key
        
        Returns:
            List of object versions, newest first
        """
        return db.query(S3Object).filter(
            S3Object.bucket_name == bucket_name,
            S3Object.account_id == account_id,
            S3Object.object_key == object_key
        ).order_by(
            S3Object.created_at.desc()
        ).all()
    
    def delete_version(
        self,
        db: Session,
        account_id: str,
        bucket_name: str,
        object_key: str,
        version_id: str
    ):
        """
        Permanently delete a specific version of an object.
        
        Args:
            db: Database session
            account_id: Owner account ID
            bucket_name: Source bucket
            object_key: Object key
            version_id: Version to delete
        
        Raises:
            ResourceNotFoundError: If version not found
        """
        s3_object = db.query(S3Object).filter(
            S3Object.bucket_name == bucket_name,
            S3Object.account_id == account_id,
            S3Object.object_key == object_key,
            S3Object.version_id == version_id
        ).first()
        
        if not s3_object:
            raise ResourceNotFoundError(
                f"Version '{version_id}' not found for object '{object_key}'"
            )
        
        # Delete file if not a delete marker
        if not s3_object.is_delete_marker:
            from pathlib import Path
            object_path = Path(s3_object.filesystem_path)
            if object_path.exists():
                object_path.unlink()
        
        # If this was the latest version, promote next version
        if s3_object.is_latest:
            next_version = db.query(S3Object).filter(
                S3Object.bucket_name == bucket_name,
                S3Object.account_id == account_id,
                S3Object.object_key == object_key,
                S3Object.object_id != s3_object.object_id
            ).order_by(
                S3Object.created_at.desc()
            ).first()
            
            if next_version:
                next_version.is_latest = True
        
        db.delete(s3_object)
        db.commit()
    
    # Lifecycle Operations
    
    def put_lifecycle_configuration(
        self,
        db: Session,
        account_id: str,
        bucket_name: str,
        rules: list[dict]
    ) -> Bucket:
        """
        Set lifecycle rules for a bucket.
        
        Args:
            db: Database session
            account_id: Owner account ID
            bucket_name: Target bucket
            rules: List of lifecycle rules
        
        Returns:
            Updated bucket
        
        Raises:
            ResourceNotFoundError: If bucket not found
            ValidationError: If rules are invalid
        
        Example rules:
            [
                {
                    "id": "delete-old-objects",
                    "status": "Enabled",
                    "expiration": {"days": 90},
                    "prefix": "logs/"
                },
                {
                    "id": "transition-to-glacier",
                    "status": "Enabled",
                    "transitions": [{"days": 30, "storage_class": "GLACIER"}],
                    "prefix": "archive/"
                }
            ]
        """
        bucket = db.query(Bucket).filter(
            Bucket.bucket_name == bucket_name,
            Bucket.account_id == account_id
        ).first()
        
        if not bucket:
            raise ResourceNotFoundError(f"Bucket '{bucket_name}' not found")
        
        # Validate rules
        self._validate_lifecycle_rules(rules)
        
        # Store as JSON
        bucket.lifecycle_rules = json.dumps(rules)
        db.commit()
        db.refresh(bucket)
        
        return bucket
    
    def delete_lifecycle_configuration(
        self,
        db: Session,
        account_id: str,
        bucket_name: str
    ) -> Bucket:
        """Delete lifecycle configuration from bucket."""
        bucket = db.query(Bucket).filter(
            Bucket.bucket_name == bucket_name,
            Bucket.account_id == account_id
        ).first()
        
        if not bucket:
            raise ResourceNotFoundError(f"Bucket '{bucket_name}' not found")
        
        bucket.lifecycle_rules = None
        db.commit()
        db.refresh(bucket)
        
        return bucket
    
    def _validate_lifecycle_rules(self, rules: list[dict]):
        """Validate lifecycle rules format."""
        if not isinstance(rules, list):
            raise ValidationError("Lifecycle rules must be a list")
        
        for rule in rules:
            if "id" not in rule:
                raise ValidationError("Each rule must have an 'id'")
            
            if "status" not in rule or rule["status"] not in ["Enabled", "Disabled"]:
                raise ValidationError("Rule status must be 'Enabled' or 'Disabled'")
            
            # Must have at least one action
            has_action = (
                "expiration" in rule or
                "transitions" in rule or
                "noncurrent_version_expiration" in rule
            )
            
            if not has_action:
                raise ValidationError(
                    f"Rule '{rule['id']}' must have at least one action "
                    "(expiration, transitions, or noncurrent_version_expiration)"
                )
    
    def evaluate_lifecycle_rules(
        self,
        db: Session,
        account_id: str,
        bucket_name: str
    ) -> dict:
        """
        Evaluate lifecycle rules and return actions to take.
        
        Returns:
            Dict with 'expired' (objects to delete) and 'transitioned' (objects to move)
        """
        bucket = db.query(Bucket).filter(
            Bucket.bucket_name == bucket_name,
            Bucket.account_id == account_id
        ).first()
        
        if not bucket or not bucket.lifecycle_rules:
            return {"expired": [], "transitioned": []}
        
        rules = json.loads(bucket.lifecycle_rules)
        expired = []
        transitioned = []
        
        for rule in rules:
            if rule["status"] != "Enabled":
                continue
            
            prefix = rule.get("prefix", "")
            
            # Get matching objects
            query = db.query(S3Object).filter(
                S3Object.bucket_name == bucket_name,
                S3Object.account_id == account_id,
                S3Object.is_latest == True
            )
            
            if prefix:
                query = query.filter(S3Object.object_key.like(f"{prefix}%"))
            
            objects = query.all()
            
            for obj in objects:
                age_days = (datetime.utcnow() - obj.created_at).days
                
                # Check expiration
                if "expiration" in rule:
                    if age_days >= rule["expiration"].get("days", float('inf')):
                        expired.append({
                            "object_key": obj.object_key,
                            "version_id": obj.version_id,
                            "rule_id": rule["id"]
                        })
                
                # Check transitions
                if "transitions" in rule:
                    for transition in rule["transitions"]:
                        if age_days >= transition.get("days", float('inf')):
                            if obj.storage_class != transition["storage_class"]:
                                transitioned.append({
                                    "object_key": obj.object_key,
                                    "version_id": obj.version_id,
                                    "from_class": obj.storage_class,
                                    "to_class": transition["storage_class"],
                                    "rule_id": rule["id"]
                                })
        
        return {"expired": expired, "transitioned": transitioned}
    
    # Bucket Policy Operations
    
    def put_bucket_policy(
        self,
        db: Session,
        account_id: str,
        bucket_name: str,
        policy_document: dict
    ) -> BucketPolicy:
        """
        Set bucket policy for cross-account access control.
        
        Args:
            db: Database session
            account_id: Bucket owner account ID
            bucket_name: Target bucket
            policy_document: IAM policy document
        
        Returns:
            Created/updated bucket policy
        
        Raises:
            ResourceNotFoundError: If bucket not found
            ValidationError: If policy is invalid
        """
        # Verify bucket exists
        bucket = db.query(Bucket).filter(
            Bucket.bucket_name == bucket_name,
            Bucket.account_id == account_id
        ).first()
        
        if not bucket:
            raise ResourceNotFoundError(f"Bucket '{bucket_name}' not found")
        
        # Validate policy document
        self._validate_policy_document(policy_document)
        
        # Check if policy exists
        existing_policy = db.query(BucketPolicy).filter(
            BucketPolicy.bucket_name == bucket_name
        ).first()
        
        if existing_policy:
            # Update existing
            existing_policy.policy_document = json.dumps(policy_document)
            existing_policy.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_policy)
            return existing_policy
        else:
            # Create new
            policy_id = generate_id(ResourceType.BUCKET)  # Reuse bucket prefix
            
            policy = BucketPolicy(
                policy_id=f"bp-{policy_id.split('-')[1]}",
                bucket_name=bucket_name,
                account_id=account_id,
                policy_document=json.dumps(policy_document),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(policy)
            db.commit()
            db.refresh(policy)
            
            return policy
    
    def get_bucket_policy(
        self,
        db: Session,
        account_id: str,
        bucket_name: str
    ) -> BucketPolicy:
        """Get bucket policy."""
        policy = db.query(BucketPolicy).filter(
            BucketPolicy.bucket_name == bucket_name,
            BucketPolicy.account_id == account_id
        ).first()
        
        if not policy:
            raise ResourceNotFoundError(f"Bucket policy not found for '{bucket_name}'")
        
        return policy
    
    def delete_bucket_policy(
        self,
        db: Session,
        account_id: str,
        bucket_name: str
    ):
        """Delete bucket policy."""
        policy = db.query(BucketPolicy).filter(
            BucketPolicy.bucket_name == bucket_name,
            BucketPolicy.account_id == account_id
        ).first()
        
        if not policy:
            raise ResourceNotFoundError(f"Bucket policy not found for '{bucket_name}'")
        
        db.delete(policy)
        db.commit()
    
    def _validate_policy_document(self, policy_doc: dict):
        """Validate bucket policy document."""
        if not isinstance(policy_doc, dict):
            raise ValidationError("Policy document must be a dictionary")
        
        if "Version" not in policy_doc:
            raise ValidationError("Policy document must have 'Version' field")
        
        if "Statement" not in policy_doc or not isinstance(policy_doc["Statement"], list):
            raise ValidationError("Policy document must have 'Statement' list")
        
        for statement in policy_doc["Statement"]:
            if "Effect" not in statement or statement["Effect"] not in ["Allow", "Deny"]:
                raise ValidationError("Statement must have 'Effect' (Allow or Deny)")
            
            if "Principal" not in statement:
                raise ValidationError("Statement must have 'Principal'")
            
            if "Action" not in statement:
                raise ValidationError("Statement must have 'Action'")
            
            if "Resource" not in statement:
                raise ValidationError("Statement must have 'Resource'")
    
    def evaluate_bucket_policy(
        self,
        db: Session,
        bucket_name: str,
        principal_arn: str,
        action: str,
        resource: str
    ) -> bool:
        """
        Evaluate bucket policy to determine if action is allowed.
        
        Args:
            db: Database session
            bucket_name: Target bucket
            principal_arn: ARN of the principal (user/role)
            action: S3 action (e.g., s3:GetObject)
            resource: Resource ARN (e.g., arn:aws:s3:::bucket/key)
        
        Returns:
            True if allowed, False if denied
        """
        policy = db.query(BucketPolicy).filter(
            BucketPolicy.bucket_name == bucket_name
        ).first()
        
        if not policy:
            # No policy = deny by default
            return False
        
        policy_doc = json.loads(policy.policy_document)
        
        # Evaluate statements
        explicit_deny = False
        explicit_allow = False
        
        for statement in policy_doc["Statement"]:
            # Check if principal matches
            if not self._match_principal(statement["Principal"], principal_arn):
                continue
            
            # Check if action matches
            actions = statement["Action"] if isinstance(statement["Action"], list) else [statement["Action"]]
            action_matches = any(self._match_action(a, action) for a in actions)
            
            if not action_matches:
                continue
            
            # Check if resource matches
            resources = statement["Resource"] if isinstance(statement["Resource"], list) else [statement["Resource"]]
            resource_matches = any(self._match_resource(r, resource) for r in resources)
            
            if not resource_matches:
                continue
            
            # Statement matches
            if statement["Effect"] == "Deny":
                explicit_deny = True
            elif statement["Effect"] == "Allow":
                explicit_allow = True
        
        # Explicit deny always wins
        if explicit_deny:
            return False
        
        # Otherwise allow if explicitly allowed
        return explicit_allow
    
    def _match_principal(self, principal: dict, arn: str) -> bool:
        """Check if principal matches ARN."""
        if principal == "*":
            return True
        
        if "AWS" in principal:
            aws_principals = principal["AWS"] if isinstance(principal["AWS"], list) else [principal["AWS"]]
            return arn in aws_principals or "*" in aws_principals
        
        return False
    
    def _match_action(self, pattern: str, action: str) -> bool:
        """Check if action matches pattern (supports wildcards)."""
        if pattern == "*" or pattern == "s3:*":
            return True
        
        if "*" in pattern:
            # Simple wildcard matching
            prefix = pattern.split("*")[0]
            return action.startswith(prefix)
        
        return pattern == action
    
    def _match_resource(self, pattern: str, resource: str) -> bool:
        """Check if resource matches pattern (supports wildcards)."""
        if pattern == "*":
            return True
        
        if "*" in pattern:
            # Simple wildcard matching
            prefix = pattern.rstrip("*")
            return resource.startswith(prefix)
        
        return pattern == resource

