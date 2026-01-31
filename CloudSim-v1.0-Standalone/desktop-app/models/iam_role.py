"""
IAM Role Model - Roles with attached policies
"""
from dataclasses import dataclass, field
from typing import List
from datetime import datetime
import secrets


@dataclass
class Role:
    """IAM Role that can have multiple policies attached"""
    role_id: str
    name: str
    description: str
    policy_ids: List[str] = field(default_factory=list)  # List of attached policy IDs
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    def to_dict(self) -> dict:
        return {
            "role_id": self.role_id,
            "name": self.name,
            "description": self.description,
            "policy_ids": self.policy_ids,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Role":
        return cls(
            role_id=data["role_id"],
            name=data["name"],
            description=data.get("description", ""),
            policy_ids=data.get("policy_ids", []),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            created_by=data.get("created_by", "")
        )
    
    @classmethod
    def create_new(cls, name: str, description: str, created_by: str = "") -> "Role":
        """Create a new role"""
        role_id = f"role-{secrets.token_hex(8)}"
        return cls(
            role_id=role_id,
            name=name,
            description=description,
            created_by=created_by
        )
    
    def attach_policy(self, policy_id: str):
        """Attach a policy to this role"""
        if policy_id not in self.policy_ids:
            self.policy_ids.append(policy_id)
    
    def detach_policy(self, policy_id: str):
        """Detach a policy from this role"""
        if policy_id in self.policy_ids:
            self.policy_ids.remove(policy_id)
