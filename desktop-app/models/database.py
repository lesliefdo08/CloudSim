"""
Database Model - Represents a database and table with IAM support
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class Database:
    """Database instance (RDS-like or DynamoDB-like) with region and owner tracking"""
    
    name: str
    db_type: str  # "relational" or "nosql"
    created_at: str
    table_count: int = 0
    region: str = "us-east-1"  # AWS-style region
    owner: Optional[str] = None  # IAM username
    tags: Dict[str, str] = field(default_factory=dict)
    
    @staticmethod
    def create_new(name: str, db_type: str) -> 'Database':
        """Create a new database"""
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return Database(
            name=name,
            db_type=db_type,
            created_at=created_at,
            table_count=0,
            region="us-east-1",
            tags={}
        )
    
    def arn(self) -> str:
        """Generate AWS-style ARN for database"""
        return f"arn:cloudsim:database:{self.region}:db/{self.name}"
    
    def to_dict(self) -> dict:
        """Convert database to dictionary"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict) -> 'Database':
        """Create database from dictionary with backward compatibility"""
        # Backward compatibility for old databases without region/owner
        if 'region' not in data:
            data['region'] = "us-east-1"
        if 'owner' not in data:
            data['owner'] = None
        if 'tags' not in data:
            data['tags'] = {}
        return Database(**data)


@dataclass
class Table:
    """Database table"""
    
    name: str
    database_name: str
    db_type: str
    created_at: str
    record_count: int = 0
    schema: Optional[Dict[str, str]] = None  # Column name -> type mapping
    
    @staticmethod
    def create_new(name: str, database_name: str, db_type: str, 
                   schema: Optional[Dict[str, str]] = None) -> 'Table':
        """Create a new table"""
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return Table(
            name=name,
            database_name=database_name,
            db_type=db_type,
            created_at=created_at,
            record_count=0,
            schema=schema or {}
        )
    
    def to_dict(self) -> dict:
        """Convert table to dictionary"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict) -> 'Table':
        """Create table from dictionary"""
        return Table(**data)
