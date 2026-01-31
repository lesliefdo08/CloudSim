"""
IAM Foundation - AWS-style Identity and Access Management
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum
from datetime import datetime
import json
import hashlib


class Effect(Enum):
    """Policy effect"""
    ALLOW = "Allow"
    DENY = "Deny"


class Action(Enum):
    """IAM actions"""
    # Compute actions
    COMPUTE_CREATE = "compute:CreateInstance"
    COMPUTE_START = "compute:StartInstance"
    COMPUTE_STOP = "compute:StopInstance"
    COMPUTE_TERMINATE = "compute:TerminateInstance"
    COMPUTE_LIST = "compute:ListInstances"
    COMPUTE_DESCRIBE = "compute:DescribeInstance"
    
    # Storage actions
    STORAGE_CREATE_BUCKET = "storage:CreateBucket"
    STORAGE_DELETE_BUCKET = "storage:DeleteBucket"
    STORAGE_LIST_BUCKETS = "storage:ListBuckets"
    STORAGE_PUT_OBJECT = "storage:PutObject"
    STORAGE_GET_OBJECT = "storage:GetObject"
    STORAGE_DELETE_OBJECT = "storage:DeleteObject"
    
    # Database actions
    DATABASE_CREATE = "database:CreateDatabase"
    DATABASE_DELETE = "database:DeleteDatabase"
    DATABASE_LIST = "database:ListDatabases"
    DATABASE_CREATE_TABLE = "database:CreateTable"
    DATABASE_QUERY = "database:Query"
    
    # Serverless actions
    SERVERLESS_CREATE_FUNCTION = "serverless:CreateFunction"
    SERVERLESS_INVOKE_FUNCTION = "serverless:InvokeFunction"
    SERVERLESS_DELETE_FUNCTION = "serverless:DeleteFunction"
    SERVERLESS_LIST_FUNCTIONS = "serverless:ListFunctions"
    
    # IAM actions
    IAM_CREATE_USER = "iam:CreateUser"
    IAM_DELETE_USER = "iam:DeleteUser"
    IAM_CREATE_POLICY = "iam:CreatePolicy"
    IAM_ATTACH_POLICY = "iam:AttachUserPolicy"
    
    # Wildcard
    ALL_ACTIONS = "*:*"


@dataclass
class PolicyStatement:
    """IAM policy statement"""
    effect: Effect
    actions: List[str]
    resources: List[str]  # ARN patterns
    conditions: Dict = field(default_factory=dict)
    
    def matches_action(self, action: str) -> bool:
        """Check if action matches this statement"""
        for pattern in self.actions:
            if pattern == "*" or pattern == action:
                return True
            # Wildcard matching (e.g., "compute:*")
            if pattern.endswith("*") and action.startswith(pattern[:-1]):
                return True
        return False
    
    def matches_resource(self, resource_arn: str) -> bool:
        """Check if resource ARN matches this statement"""
        for pattern in self.resources:
            if pattern == "*" or pattern == resource_arn:
                return True
            # Wildcard matching
            if pattern.endswith("*") and resource_arn.startswith(pattern[:-1]):
                return True
        return False


@dataclass
class Policy:
    """IAM policy"""
    name: str
    statements: List[PolicyStatement]
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def evaluate(self, action: str, resource_arn: str) -> bool:
        """
        Evaluate policy for given action and resource.
        Returns True if action is allowed, False otherwise.
        AWS-style: explicit deny overrides allow.
        """
        has_allow = False
        has_deny = False
        
        for statement in self.statements:
            if statement.matches_action(action) and statement.matches_resource(resource_arn):
                if statement.effect == Effect.ALLOW:
                    has_allow = True
                elif statement.effect == Effect.DENY:
                    has_deny = True
        
        # Explicit deny always wins
        if has_deny:
            return False
        
        return has_allow


@dataclass
class User:
    """IAM user"""
    username: str
    user_id: str = field(default_factory=lambda: hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:16])
    created_at: datetime = field(default_factory=datetime.now)
    policies: List[str] = field(default_factory=list)  # Policy names
    groups: List[str] = field(default_factory=list)  # Group names
    tags: Dict[str, str] = field(default_factory=dict)
    
    def arn(self) -> str:
        """Generate AWS-style ARN for user"""
        return f"arn:cloudsim:iam::user/{self.username}"


@dataclass
class Role:
    """IAM role that can be attached to resources or assumed by users"""
    name: str
    role_id: str = field(default_factory=lambda: hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:16])
    assume_role_policy: Optional[Policy] = None
    policies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    
    def arn(self) -> str:
        """Generate AWS-style ARN for role"""
        return f"arn:cloudsim:iam::role/{self.name}"
    
    def to_json(self) -> Dict:
        """Export role to JSON format"""
        return {
            "name": self.name,
            "role_id": self.role_id,
            "policies": self.policies,
            "description": self.description,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class SessionContext:
    """Current user session context for tracking who is performing actions"""
    username: str
    session_id: str
    started_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for event logging"""
        return {
            "username": self.username,
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat()
        }


class IAMManager:
    """Manages IAM users, policies, and roles"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize IAM system"""
        self.users: Dict[str, User] = {}
        self.policies: Dict[str, Policy] = {}
        self.roles: Dict[str, Role] = {}
        self.resource_roles: Dict[str, str] = {}  # resource_arn -> role_name
        self._current_user: Optional[str] = None
        self._session_context: Optional[SessionContext] = None
        
        # Create default admin user
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user with full permissions"""
        admin_policy = Policy(
            name="AdministratorAccess",
            statements=[
                PolicyStatement(
                    effect=Effect.ALLOW,
                    actions=["*"],
                    resources=["*"]
                )
            ],
            description="Full access to all CloudSim resources"
        )
        
        admin_user = User(
            username="admin",
            policies=["AdministratorAccess"]
        )
        
        self.policies["AdministratorAccess"] = admin_policy
        self.users["admin"] = admin_user
        self._current_user = "admin"
    
    def create_user(self, username: str, tags: Optional[Dict[str, str]] = None) -> User:
        """Create a new IAM user"""
        if username in self.users:
            raise ValueError(f"User {username} already exists")
        
        user = User(username=username, tags=tags or {})
        self.users[username] = user
        return user
    
    def create_policy(self, policy: Policy) -> bool:
        """Create a new policy"""
        if policy.name in self.policies:
            return False
        self.policies[policy.name] = policy
        return True
    
    def attach_user_policy(self, username: str, policy_name: str) -> bool:
        """Attach policy to user"""
        if username not in self.users or policy_name not in self.policies:
            return False
        
        user = self.users[username]
        if policy_name not in user.policies:
            user.policies.append(policy_name)
        return True
    
    def detach_user_policy(self, username: str, policy_name: str) -> bool:
        """Detach policy from user"""
        if username not in self.users:
            return False
        
        user = self.users[username]
        if policy_name in user.policies:
            user.policies.remove(policy_name)
        return True
    
    def set_current_user(self, username: str) -> bool:
        """Set the current user context"""
        if username in self.users:
            self._current_user = username
            # Create session context for activity logging
            self._session_context = SessionContext(
                username=username,
                session_id=hashlib.sha256(f"{username}{datetime.now().timestamp()}".encode()).hexdigest()[:16]
            )
            return True
        return False
    
    def get_current_user(self) -> Optional[User]:
        """Get the current user (auth disabled - returns mock local user)"""
        from models.user import User
        from datetime import datetime
        # Return a mock local user since auth is disabled
        return User(
            user_id="local-user-id",
            username="local-user",
            email="local@cloudsim.local",
            password_hash="",
            created_at=datetime.now(),
            is_active=True
        )
    
    def get_session_context(self) -> Optional[SessionContext]:
        """Get current session context for activity logging"""
        return self._session_context
    
    def check_permission(self, action: str, resource_arn: str) -> bool:
        """
        Check if current user has permission for action on resource.
        Checks both user policies and resource-attached roles.
        Returns True if allowed, False otherwise.
        
        Auth disabled - always returns True to allow all operations.
        """
        # Auth disabled - allow all operations
        return True
    
    def create_role(self, name: str, description: str = "") -> Role:
        """Create a new IAM role"""
        if name in self.roles:
            raise ValueError(f"Role {name} already exists")
        
        role = Role(name=name, description=description)
        self.roles[name] = role
        return role
    
    def attach_role_policy(self, role_name: str, policy_name: str) -> bool:
        """Attach policy to role"""
        if role_name not in self.roles or policy_name not in self.policies:
            return False
        
        role = self.roles[role_name]
        if policy_name not in role.policies:
            role.policies.append(policy_name)
        return True
    
    def attach_role_to_resource(self, resource_arn: str, role_name: str) -> bool:
        """Attach a role to a resource"""
        if role_name not in self.roles:
            return False
        
        self.resource_roles[resource_arn] = role_name
        return True
    
    def detach_role_from_resource(self, resource_arn: str) -> bool:
        """Detach role from resource"""
        if resource_arn in self.resource_roles:
            del self.resource_roles[resource_arn]
            return True
        return False
    
    def get_resource_role(self, resource_arn: str) -> Optional[Role]:
        """Get the role attached to a resource"""
        if resource_arn in self.resource_roles:
            role_name = self.resource_roles[resource_arn]
            return self.roles.get(role_name)
        return None
    
    def policy_to_json(self, policy_name: str) -> Optional[str]:
        """Export policy to AWS-style JSON format"""
        policy = self.policies.get(policy_name)
        if not policy:
            return None
        
        statements = []
        for stmt in policy.statements:
            statements.append({
                "Effect": stmt.effect.value,
                "Action": stmt.actions,
                "Resource": stmt.resources,
                "Condition": stmt.conditions if stmt.conditions else {}
            })
        
        return json.dumps({
            "Version": "2012-10-17",
            "Statement": statements
        }, indent=2)
    
    def policy_from_json(self, name: str, json_str: str, description: str = "") -> Policy:
        """Import policy from AWS-style JSON format"""
        data = json.loads(json_str)
        
        statements = []
        for stmt_data in data.get("Statement", []):
            effect = Effect.ALLOW if stmt_data.get("Effect") == "Allow" else Effect.DENY
            actions = stmt_data.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]
            resources = stmt_data.get("Resource", [])
            if isinstance(resources, str):
                resources = [resources]
            conditions = stmt_data.get("Condition", {})
            
            statements.append(PolicyStatement(
                effect=effect,
                actions=actions,
                resources=resources,
                conditions=conditions
            ))
        
        return Policy(name=name, statements=statements, description=description)
    
    def list_users(self) -> List[User]:
        """List all users"""
        return list(self.users.values())
    
    def list_policies(self) -> List[Policy]:
        """List all policies"""
        return list(self.policies.values())


def require_permission(action: str):
    """Decorator to enforce IAM permissions on service methods"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # For now, we'll add the actual enforcement later
            # This is the hook for IAM integration
            iam = IAMManager()
            # Resource ARN would be constructed based on the service and resource
            resource_arn = "*"  # Simplified for now
            
            if not iam.check_permission(action, resource_arn):
                raise PermissionError(f"User does not have permission for action: {action}")
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator
