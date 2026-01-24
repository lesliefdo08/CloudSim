"""
IAM Policy Model - JSON-based policies for CloudSim
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import secrets


@dataclass
class PolicyStatement:
    """Single policy statement"""
    effect: str  # "Allow" or "Deny"
    actions: List[str]  # e.g., ["ec2:RunInstance", "s3:CreateBucket"]
    resources: List[str] = field(default_factory=lambda: ["*"])  # e.g., ["*", "bucket:my-bucket"]
    
    def to_dict(self) -> dict:
        return {
            "Effect": self.effect,
            "Action": self.actions,
            "Resource": self.resources
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PolicyStatement":
        return cls(
            effect=data.get("Effect", "Allow"),
            actions=data.get("Action", []) if isinstance(data.get("Action"), list) else [data.get("Action", "")],
            resources=data.get("Resource", ["*"]) if isinstance(data.get("Resource"), list) else [data.get("Resource", "*")]
        )


@dataclass
class Policy:
    """IAM Policy with JSON-based permissions"""
    policy_id: str
    name: str
    description: str
    statements: List[PolicyStatement]
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    is_system: bool = False  # System policies cannot be deleted
    
    def to_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "policy_document": {
                "Version": "2024-01-01",
                "Statement": [stmt.to_dict() for stmt in self.statements]
            },
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "is_system": self.is_system
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Policy":
        policy_doc = data.get("policy_document", {})
        statements = [
            PolicyStatement.from_dict(stmt) 
            for stmt in policy_doc.get("Statement", [])
        ]
        
        return cls(
            policy_id=data["policy_id"],
            name=data["name"],
            description=data.get("description", ""),
            statements=statements,
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            created_by=data.get("created_by", ""),
            is_system=data.get("is_system", False)
        )
    
    @classmethod
    def create_new(cls, name: str, description: str, statements: List[PolicyStatement], created_by: str = "") -> "Policy":
        """Create a new policy"""
        policy_id = f"policy-{secrets.token_hex(8)}"
        return cls(
            policy_id=policy_id,
            name=name,
            description=description,
            statements=statements,
            created_by=created_by
        )
    
    def get_policy_document(self) -> dict:
        """Get policy document in AWS IAM format"""
        return {
            "Version": "2024-01-01",
            "Statement": [stmt.to_dict() for stmt in self.statements]
        }
    
    def get_allowed_actions(self) -> List[str]:
        """Get all allowed actions from policy"""
        actions = []
        for stmt in self.statements:
            if stmt.effect == "Allow":
                actions.extend(stmt.actions)
        return actions
    
    def get_denied_actions(self) -> List[str]:
        """Get all explicitly denied actions"""
        actions = []
        for stmt in self.statements:
            if stmt.effect == "Deny":
                actions.extend(stmt.actions)
        return actions


# Pre-defined system policies
SYSTEM_POLICIES = {
    "AdministratorAccess": Policy(
        policy_id="policy-admin",
        name="AdministratorAccess",
        description="Full access to all CloudSim services and resources",
        statements=[
            PolicyStatement(
                effect="Allow",
                actions=["*"],
                resources=["*"]
            )
        ],
        is_system=True
    ),
    
    "ReadOnlyAccess": Policy(
        policy_id="policy-readonly",
        name="ReadOnlyAccess",
        description="Read-only access to all CloudSim services",
        statements=[
            PolicyStatement(
                effect="Allow",
                actions=[
                    "ec2:DescribeInstances",
                    "s3:ListBuckets",
                    "s3:GetObject",
                    "ebs:DescribeVolumes",
                    "rds:DescribeDatabases",
                    "lambda:ListFunctions"
                ],
                resources=["*"]
            )
        ],
        is_system=True
    ),
    
    "EC2FullAccess": Policy(
        policy_id="policy-ec2-full",
        name="EC2FullAccess",
        description="Full access to EC2 compute instances",
        statements=[
            PolicyStatement(
                effect="Allow",
                actions=[
                    "ec2:*"
                ],
                resources=["*"]
            )
        ],
        is_system=True
    ),
    
    "S3FullAccess": Policy(
        policy_id="policy-s3-full",
        name="S3FullAccess",
        description="Full access to S3 storage buckets",
        statements=[
            PolicyStatement(
                effect="Allow",
                actions=[
                    "s3:*"
                ],
                resources=["*"]
            )
        ],
        is_system=True
    ),
    
    "PowerUserAccess": Policy(
        policy_id="policy-poweruser",
        name="PowerUserAccess",
        description="Full access except IAM management",
        statements=[
            PolicyStatement(
                effect="Allow",
                actions=[
                    "ec2:*",
                    "s3:*",
                    "ebs:*",
                    "rds:*",
                    "lambda:*"
                ],
                resources=["*"]
            ),
            PolicyStatement(
                effect="Deny",
                actions=["iam:*"],
                resources=["*"]
            )
        ],
        is_system=True
    )
}
