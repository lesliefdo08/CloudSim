"""
IAM Service - Manage users, roles, and policies
"""
from typing import List, Optional, Dict, Tuple
from pathlib import Path
import json

from models.user import User
from models.iam_role import Role
from models.iam_policy import Policy, PolicyStatement, SYSTEM_POLICIES
from services.policy_engine import policy_engine
from core.config import AppConfig


class IAMService:
    """Service for managing IAM resources"""
    
    def __init__(self):
        self.roles_file = AppConfig.DATA_DIR / "iam_roles.json"
        self.policies_file = AppConfig.DATA_DIR / "iam_policies.json"
        self.user_policies_file = AppConfig.DATA_DIR / "user_policies.json"
        
        self._roles: Dict[str, Role] = {}
        self._policies: Dict[str, Policy] = {}
        self._user_policies: Dict[str, List[str]] = {}  # user_id -> [policy_ids]
        self._user_roles: Dict[str, List[str]] = {}  # user_id -> [role_ids]
        
        self._load_data()
        self._ensure_system_policies()
    
    def _load_data(self):
        """Load IAM data from storage"""
        # Load roles
        if self.roles_file.exists():
            try:
                with open(self.roles_file, 'r') as f:
                    data = json.load(f)
                    for role_data in data:
                        role = Role.from_dict(role_data)
                        self._roles[role.role_id] = role
            except (json.JSONDecodeError, IOError):
                pass
        
        # Load policies
        if self.policies_file.exists():
            try:
                with open(self.policies_file, 'r') as f:
                    data = json.load(f)
                    for policy_data in data:
                        policy = Policy.from_dict(policy_data)
                        self._policies[policy.policy_id] = policy
            except (json.JSONDecodeError, IOError):
                pass
        
        # Load user policy/role assignments
        if self.user_policies_file.exists():
            try:
                with open(self.user_policies_file, 'r') as f:
                    data = json.load(f)
                    self._user_policies = data.get("user_policies", {})
                    self._user_roles = data.get("user_roles", {})
            except (json.JSONDecodeError, IOError):
                pass
    
    def _ensure_system_policies(self):
        """Ensure system policies are loaded"""
        for policy in SYSTEM_POLICIES.values():
            if policy.policy_id not in self._policies:
                self._policies[policy.policy_id] = policy
    
    def _save_roles(self):
        """Save roles to storage"""
        data = [role.to_dict() for role in self._roles.values()]
        with open(self.roles_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_policies(self):
        """Save policies to storage"""
        # Only save non-system policies
        data = [
            policy.to_dict() 
            for policy in self._policies.values() 
            if not policy.is_system
        ]
        with open(self.policies_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_user_assignments(self):
        """Save user policy/role assignments"""
        data = {
            "user_policies": self._user_policies,
            "user_roles": self._user_roles
        }
        with open(self.user_policies_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    # ===== Policy Management =====
    
    def create_policy(
        self, 
        name: str, 
        description: str, 
        statements: List[PolicyStatement],
        created_by: str = ""
    ) -> Tuple[bool, str, Optional[Policy]]:
        """Create a new policy"""
        # Validate name uniqueness
        for policy in self._policies.values():
            if policy.name.lower() == name.lower():
                return False, "Policy name already exists", None
        
        # Create policy
        policy = Policy.create_new(name, description, statements, created_by)
        self._policies[policy.policy_id] = policy
        self._save_policies()
        
        return True, "Policy created successfully", policy
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get policy by ID"""
        return self._policies.get(policy_id)
    
    def list_policies(self, include_system: bool = True) -> List[Policy]:
        """List all policies"""
        policies = list(self._policies.values())
        if not include_system:
            policies = [p for p in policies if not p.is_system]
        return sorted(policies, key=lambda p: p.name)
    
    def update_policy(
        self, 
        policy_id: str, 
        name: Optional[str] = None,
        description: Optional[str] = None,
        statements: Optional[List[PolicyStatement]] = None
    ) -> Tuple[bool, str]:
        """Update an existing policy"""
        policy = self.get_policy(policy_id)
        if not policy:
            return False, "Policy not found"
        
        if policy.is_system:
            return False, "Cannot modify system policies"
        
        if name:
            policy.name = name
        if description:
            policy.description = description
        if statements:
            policy.statements = statements
        
        self._save_policies()
        return True, "Policy updated successfully"
    
    def delete_policy(self, policy_id: str) -> Tuple[bool, str]:
        """Delete a policy"""
        policy = self.get_policy(policy_id)
        if not policy:
            return False, "Policy not found"
        
        if policy.is_system:
            return False, "Cannot delete system policies"
        
        # Remove from all users and roles
        for user_id in list(self._user_policies.keys()):
            if policy_id in self._user_policies[user_id]:
                self._user_policies[user_id].remove(policy_id)
        
        for role in self._roles.values():
            if policy_id in role.policy_ids:
                role.policy_ids.remove(policy_id)
        
        del self._policies[policy_id]
        self._save_policies()
        self._save_roles()
        self._save_user_assignments()
        
        return True, "Policy deleted successfully"
    
    # ===== Role Management =====
    
    def create_role(
        self, 
        name: str, 
        description: str,
        created_by: str = ""
    ) -> Tuple[bool, str, Optional[Role]]:
        """Create a new role"""
        # Validate name uniqueness
        for role in self._roles.values():
            if role.name.lower() == name.lower():
                return False, "Role name already exists", None
        
        role = Role.create_new(name, description, created_by)
        self._roles[role.role_id] = role
        self._save_roles()
        
        return True, "Role created successfully", role
    
    def get_role(self, role_id: str) -> Optional[Role]:
        """Get role by ID"""
        return self._roles.get(role_id)
    
    def list_roles(self) -> List[Role]:
        """List all roles"""
        return sorted(self._roles.values(), key=lambda r: r.name)
    
    def update_role(
        self, 
        role_id: str, 
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Update an existing role"""
        role = self.get_role(role_id)
        if not role:
            return False, "Role not found"
        
        if name:
            role.name = name
        if description:
            role.description = description
        
        self._save_roles()
        return True, "Role updated successfully"
    
    def delete_role(self, role_id: str) -> Tuple[bool, str]:
        """Delete a role"""
        role = self.get_role(role_id)
        if not role:
            return False, "Role not found"
        
        # Remove from all users
        for user_id in list(self._user_roles.keys()):
            if role_id in self._user_roles[user_id]:
                self._user_roles[user_id].remove(role_id)
        
        del self._roles[role_id]
        self._save_roles()
        self._save_user_assignments()
        
        return True, "Role deleted successfully"
    
    def attach_policy_to_role(self, role_id: str, policy_id: str) -> Tuple[bool, str]:
        """Attach a policy to a role"""
        role = self.get_role(role_id)
        if not role:
            return False, "Role not found"
        
        policy = self.get_policy(policy_id)
        if not policy:
            return False, "Policy not found"
        
        role.attach_policy(policy_id)
        self._save_roles()
        
        return True, f"Policy '{policy.name}' attached to role '{role.name}'"
    
    def detach_policy_from_role(self, role_id: str, policy_id: str) -> Tuple[bool, str]:
        """Detach a policy from a role"""
        role = self.get_role(role_id)
        if not role:
            return False, "Role not found"
        
        role.detach_policy(policy_id)
        self._save_roles()
        
        return True, "Policy detached from role"
    
    # ===== User Policy/Role Assignment =====
    
    def attach_policy_to_user(self, user_id: str, policy_id: str) -> Tuple[bool, str]:
        """Attach a policy directly to a user"""
        policy = self.get_policy(policy_id)
        if not policy:
            return False, "Policy not found"
        
        if user_id not in self._user_policies:
            self._user_policies[user_id] = []
        
        if policy_id not in self._user_policies[user_id]:
            self._user_policies[user_id].append(policy_id)
            self._save_user_assignments()
        
        return True, f"Policy '{policy.name}' attached to user"
    
    def detach_policy_from_user(self, user_id: str, policy_id: str) -> Tuple[bool, str]:
        """Detach a policy from a user"""
        if user_id in self._user_policies and policy_id in self._user_policies[user_id]:
            self._user_policies[user_id].remove(policy_id)
            self._save_user_assignments()
        
        return True, "Policy detached from user"
    
    def attach_role_to_user(self, user_id: str, role_id: str) -> Tuple[bool, str]:
        """Attach a role to a user"""
        role = self.get_role(role_id)
        if not role:
            return False, "Role not found"
        
        if user_id not in self._user_roles:
            self._user_roles[user_id] = []
        
        if role_id not in self._user_roles[user_id]:
            self._user_roles[user_id].append(role_id)
            self._save_user_assignments()
        
        return True, f"Role '{role.name}' attached to user"
    
    def detach_role_from_user(self, user_id: str, role_id: str) -> Tuple[bool, str]:
        """Detach a role from a user"""
        if user_id in self._user_roles and role_id in self._user_roles[user_id]:
            self._user_roles[user_id].remove(role_id)
            self._save_user_assignments()
        
        return True, "Role detached from user"
    
    def get_user_policies(self, user_id: str) -> List[Policy]:
        """Get all policies for a user (direct + from roles)"""
        policies = []
        
        # Direct policies
        policy_ids = self._user_policies.get(user_id, [])
        for policy_id in policy_ids:
            policy = self.get_policy(policy_id)
            if policy:
                policies.append(policy)
        
        # Policies from roles
        role_ids = self._user_roles.get(user_id, [])
        for role_id in role_ids:
            role = self.get_role(role_id)
            if role:
                for policy_id in role.policy_ids:
                    policy = self.get_policy(policy_id)
                    if policy and policy not in policies:
                        policies.append(policy)
        
        return policies
    
    def get_user_roles(self, user_id: str) -> List[Role]:
        """Get all roles assigned to a user"""
        roles = []
        role_ids = self._user_roles.get(user_id, [])
        for role_id in role_ids:
            role = self.get_role(role_id)
            if role:
                roles.append(role)
        return roles
    
    # ===== Permission Checking =====
    
    def check_permission(
        self, 
        user_id: str, 
        action: str, 
        resource: str = "*"
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user has permission to perform an action.
        
        Returns:
            (allowed: bool, reason: Optional[str])
        """
        policies = self.get_user_policies(user_id)
        return policy_engine.evaluate_action(action, resource, policies)
    
    def simulate_permission(
        self, 
        user_id: str, 
        action: str, 
        resource: str = "*"
    ) -> dict:
        """
        Simulate permission check with detailed results.
        Useful for debugging and testing.
        """
        policies = self.get_user_policies(user_id)
        return policy_engine.simulate_action(action, resource, policies)
    
    def get_user_permissions_summary(self, user_id: str) -> dict:
        """Get summary of user's effective permissions"""
        policies = self.get_user_policies(user_id)
        return policy_engine.get_effective_permissions(policies)


# Global IAM service instance
iam_service = IAMService()
