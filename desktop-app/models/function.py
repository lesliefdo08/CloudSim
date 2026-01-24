"""
Function Model - Represents a serverless function (Lambda-like) with IAM support
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, Dict


@dataclass
class Function:
    """Serverless function (Lambda-like) with region and owner tracking"""
    
    name: str
    runtime: str  # "python3.9"
    handler: str  # "handler" (function name in code)
    code: str  # Python code
    created_at: str
    last_modified: str
    invocation_count: int = 0
    region: str = "us-east-1"  # AWS-style region
    owner: Optional[str] = None  # IAM username
    tags: Dict[str, str] = field(default_factory=dict)
    
    @staticmethod
    def create_new(name: str, code: str, handler: str = "handler", 
                   runtime: str = "python3.9") -> 'Function':
        """Create a new function"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return Function(
            name=name,
            runtime=runtime,
            handler=handler,
            code=code,
            created_at=timestamp,
            last_modified=timestamp,
            invocation_count=0,
            region="us-east-1",
            tags={}
        )
    
    def arn(self) -> str:
        """Generate AWS-style ARN for function"""
        return f"arn:cloudsim:serverless:{self.region}:function/{self.name}"
    
    def update_code(self, new_code: str):
        """Update function code"""
        self.code = new_code
        self.last_modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def increment_invocations(self):
        """Increment invocation count"""
        self.invocation_count += 1
    
    def to_dict(self) -> dict:
        """Convert function to dictionary"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict) -> 'Function':
        """Create function from dictionary with backward compatibility"""
        # Backward compatibility for old functions without region/owner
        if 'region' not in data:
            data['region'] = "us-east-1"
        if 'owner' not in data:
            data['owner'] = None
        if 'tags' not in data:
            data['tags'] = {}
        return Function(**data)


@dataclass
class InvocationResult:
    """Result of a function invocation"""
    
    success: bool
    output: Optional[str] = None
    logs: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
