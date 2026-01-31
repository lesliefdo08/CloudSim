"""
IAM Policy Document Schemas
Pydantic models for IAM policy JSON structure
"""

from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class PolicyStatement(BaseModel):
    """
    Single statement in an IAM policy
    
    AWS IAM Policy Statement structure:
    {
        "Effect": "Allow" | "Deny",
        "Action": "service:Action" | ["service:Action1", "service:Action2"],
        "Resource": "arn:..." | ["arn:...", "arn:..."],
        "Condition": {...}  // Optional, not yet implemented
    }
    """
    
    effect: Literal["Allow", "Deny"] = Field(
        ...,
        description="Effect of the statement: Allow or Deny"
    )
    
    action: Union[str, List[str]] = Field(
        ...,
        description="Action or list of actions (supports wildcards: ec2:*, *)"
    )
    
    resource: Union[str, List[str]] = Field(
        ...,
        description="Resource ARN or list of ARNs (supports wildcards: arn:aws:s3:::bucket/*)"
    )
    
    sid: Optional[str] = Field(
        None,
        description="Statement ID (optional identifier)"
    )
    
    # TODO: Implement condition evaluation
    condition: Optional[dict] = Field(
        None,
        description="Condition block (not yet implemented)"
    )
    
    @field_validator("action")
    @classmethod
    def normalize_action(cls, v):
        """Normalize action to list"""
        if isinstance(v, str):
            return [v]
        return v
    
    @field_validator("resource")
    @classmethod
    def normalize_resource(cls, v):
        """Normalize resource to list"""
        if isinstance(v, str):
            return [v]
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "effect": "Allow",
                    "action": ["ec2:StartInstances", "ec2:StopInstances"],
                    "resource": "arn:aws:ec2:us-east-1:123456789012:instance/*"
                },
                {
                    "effect": "Deny",
                    "action": "ec2:TerminateInstances",
                    "resource": "*"
                }
            ]
        }
    )


class PolicyDocument(BaseModel):
    """
    IAM Policy Document
    
    Complete policy document structure:
    {
        "Version": "2012-10-17",
        "Statement": [...]
    }
    """
    
    version: str = Field(
        default="2012-10-17",
        description="Policy language version (always '2012-10-17' for AWS)"
    )
    
    statement: List[PolicyStatement] = Field(
        ...,
        description="List of policy statements"
    )
    
    @field_validator("version")
    @classmethod
    def validate_version(cls, v):
        """Validate policy version"""
        if v not in ["2012-10-17", "2008-10-17"]:
            raise ValueError("Invalid policy version. Use '2012-10-17'")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version": "2012-10-17",
                "statement": [
                    {
                        "effect": "Allow",
                        "action": "ec2:*",
                        "resource": "*"
                    }
                ]
            }
        }
    )


# Common AWS Managed Policies (for reference)

POLICY_ADMIN_ACCESS = PolicyDocument(
    version="2012-10-17",
    statement=[
        PolicyStatement(
            sid="AdminAccess",
            effect="Allow",
            action="*",
            resource="*"
        )
    ]
)

POLICY_READ_ONLY_ACCESS = PolicyDocument(
    version="2012-10-17",
    statement=[
        PolicyStatement(
            sid="ReadOnlyAccess",
            effect="Allow",
            action=[
                "ec2:Describe*",
                "ec2:Get*",
                "s3:Get*",
                "s3:List*",
                "iam:Get*",
                "iam:List*"
            ],
            resource="*"
        )
    ]
)

POLICY_EC2_FULL_ACCESS = PolicyDocument(
    version="2012-10-17",
    statement=[
        PolicyStatement(
            sid="EC2FullAccess",
            effect="Allow",
            action="ec2:*",
            resource="*"
        )
    ]
)

POLICY_S3_FULL_ACCESS = PolicyDocument(
    version="2012-10-17",
    statement=[
        PolicyStatement(
            sid="S3FullAccess",
            effect="Allow",
            action="s3:*",
            resource="*"
        )
    ]
)
