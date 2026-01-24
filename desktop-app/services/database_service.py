"""
Database Service - RDS-like and DynamoDB-like database management with IAM integration
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from models.database import Database, Table
from core.region import get_current_region
from core.iam import IAMManager, Action
from core.events import EventBus, EventType, emit_event
from core.metering import UsageMeter, MetricType


class DatabaseService:
    """Service for managing relational and NoSQL databases with IAM protection
    
    *** SHARED LOCAL STORAGE ***
    Uses: data/databases/ (single namespace with relational/ and nosql/ subdirs)
    """
    
    def __init__(self):
        """Initialize database service with IAM integration"""
        # Shared storage: data/databases/
        self.data_root = Path("data/databases")
        self.relational_root = self.data_root / "relational"
        self.nosql_root = self.data_root / "nosql"
        self.metadata_file = self.data_root / "metadata.json"
        
        # Create directories
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.relational_root.mkdir(exist_ok=True)
        self.nosql_root.mkdir(exist_ok=True)
        
        self._databases = {}
        self._load_databases()
        
        # Initialize core systems
        self.iam = IAMManager()
        self.event_bus = EventBus()
    
    def _check_permission(self, action: str, resource_arn: str):
        """Check IAM permission and raise PermissionError if denied"""
        if not self.iam.check_permission(action, resource_arn):
            username = "local-user"
            raise PermissionError(
                f"User '{username}' does not have permission to perform action '{action}' on resource '{resource_arn}'"
            )
    
    def _load_databases(self):
        """Load database metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    for db_data in data:
                        db = Database.from_dict(db_data)
                        self._databases[db.name] = db
            except (json.JSONDecodeError, IOError):
                pass
        
        self._sync_databases()
    
    def _sync_databases(self):
        """Sync database metadata with actual files"""
        # Sync relational databases
        for item in self.relational_root.glob("*.sqlite"):
            db_name = item.stem
            if db_name not in self._databases:
                db = Database.create_new(db_name, "relational")
                db.table_count = self._count_tables(db_name)
                self._databases[db_name] = db
        
        # Sync NoSQL databases
        for item in self.nosql_root.iterdir():
            if item.is_dir():
                db_name = item.name
                if db_name not in self._databases:
                    db = Database.create_new(db_name, "nosql")
                    db.table_count = self._count_tables(db_name)
                    self._databases[db_name] = db
        
        self._save_databases()
    
    def _save_databases(self):
        """Save database metadata"""
        data = [db.to_dict() for db in self._databases.values()]
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving database metadata: {e}")
    
    def _count_tables(self, db_name: str) -> int:
        """Count tables in a database"""
        db = self._databases.get(db_name)
        if not db:
            return 0
        
        if db.db_type == "relational":
            db_path = self.relational_root / f"{db_name}.sqlite"
            if not db_path.exists():
                return 0
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                count = cursor.fetchone()[0]
                conn.close()
                return count
            except sqlite3.Error:
                return 0
        else:  # nosql
            db_dir = self.nosql_root / db_name
            if not db_dir.exists():
                return 0
            return len([f for f in db_dir.glob("*.json")])
    
    def create_database(self, name: str, db_type: str, region: Optional[str] = None, tags: Optional[dict] = None) -> Database:
        """
        Create a new database with IAM checks
        
        Args:
            name: Database name
            db_type: "relational" or "nosql"
            region: Region for database (defaults to current region)
            tags: Optional tags for the database
            
        Returns:
            Created database
            
        Raises:
            ValueError: If name is invalid or database exists
            PermissionError: If user lacks database:CreateDatabase permission
        """
        region = region or get_current_region()
        resource_arn = f"arn:cloudsim:database:{region}:db/{name}"
        
        # IAM permission check
        self._check_permission(Action.DATABASE_CREATE.value, resource_arn)
        
        if not name or not name.strip():
            raise ValueError("Database name cannot be empty")
        
        if db_type not in ["relational", "nosql"]:
            raise ValueError("Database type must be 'relational' or 'nosql'")
        
        if name in self._databases:
            raise ValueError(f"Database '{name}' already exists")
        
        # Create database file/folder
        if db_type == "relational":
            db_path = self.relational_root / f"{name}.sqlite"
            # Create empty SQLite database
            conn = sqlite3.connect(db_path)
            conn.close()
        else:  # nosql
            db_dir = self.nosql_root / name
            db_dir.mkdir(exist_ok=True)
        
        # Create metadata with region and owner
        db = Database.create_new(name, db_type)
        db.region = region
        db.tags = tags or {}
        db.owner = "local-user"
        
        self._databases[name] = db
        self._save_databases()
        
        # Emit event
        emit_event(
            EventType.DATABASE_CREATED,
            source="database",
            region=region,
            resource_id=name,
            resource_arn=resource_arn,
            details={"db_type": db_type, "tags": tags or {}}
        )
        
        return db
    
    def delete_database(self, name: str) -> bool:
        """
        Delete a database with IAM checks
        
        Args:
            name: Database name
            
        Returns:
            True if deleted successfully
            
        Raises:
            ValueError: If database doesn't exist
            PermissionError: If user lacks database:DeleteDatabase permission
        """
        if name not in self._databases:
            raise ValueError(f"Database '{name}' does not exist")
        
        db = self._databases[name]
        region = getattr(db, 'region', get_current_region())
        resource_arn = f"arn:cloudsim:database:{region}:db/{name}"
        
        # IAM permission check
        self._check_permission(Action.DATABASE_DELETE.value, resource_arn)
        
        # Delete database file/folder
        if db.db_type == "relational":
            db_path = self.relational_root / f"{name}.sqlite"
            if db_path.exists():
                db_path.unlink()
        else:  # nosql
            db_dir = self.nosql_root / name
            if db_dir.exists():
                import shutil
                shutil.rmtree(db_dir)
        
        # Remove from metadata
        del self._databases[name]
        self._save_databases()
        
        # Emit event
        emit_event(
            EventType.DATABASE_DELETED,
            source="database",
            region=region,
            resource_id=name,
            resource_arn=resource_arn,
            details={}
        )
        
        return True
    
    def list_databases(self, region: Optional[str] = None) -> List[Database]:
        """
        Get all databases with IAM checks and optional region filtering
        
        Args:
            region: Optional region filter
            
        Returns:
            List of databases
            
        Raises:
            PermissionError: If user lacks database:ListDatabases permission
        """
        # IAM permission check
        self._check_permission(Action.DATABASE_LIST.value, "arn:cloudsim:database:*:db/*")
        
        for db in self._databases.values():
            db.table_count = self._count_tables(db.name)
        self._save_databases()
        
        # Filter by region if specified
        databases = list(self._databases.values())
        if region:
            databases = [db for db in databases if getattr(db, 'region', None) == region]
        
        return databases
    
    def get_database(self, name: str) -> Optional[Database]:
        """Get database by name"""
        db = self._databases.get(name)
        if db:
            db.table_count = self._count_tables(name)
        return db
    
    def create_table(self, db_name: str, table_name: str, 
                    schema: Optional[Dict[str, str]] = None) -> Table:
        """
        Create a table in a database with IAM checks
        
        Args:
            db_name: Database name
            table_name: Table name
            schema: Column definitions (name -> type)
            
        Returns:
            Created table
            
        Raises:
            ValueError: If database doesn't exist
            PermissionError: If user lacks database:CreateTable permission
        """
        if db_name not in self._databases:
            raise ValueError(f"Database '{db_name}' does not exist")
        
        db = self._databases[db_name]
        region = getattr(db, 'region', get_current_region())
        resource_arn = f"arn:cloudsim:database:{region}:db/{db_name}/table/{table_name}"
        
        # IAM permission check
        self._check_permission(Action.DATABASE_CREATE_TABLE.value, resource_arn)
        
        if db.db_type == "relational":
            table = self._create_relational_table(db_name, table_name, schema or {})
        else:
            table = self._create_nosql_table(db_name, table_name)
        
        # Emit event
        emit_event(
            EventType.TABLE_CREATED,
            source="database",
            region=region,
            resource_id=table_name,
            resource_arn=resource_arn,
            details={"database": db_name, "schema": schema or {}}
        )
        
        return table
    
    def _create_relational_table(self, db_name: str, table_name: str, 
                                schema: Dict[str, str]) -> Table:
        """Create a relational table"""
        db_path = self.relational_root / f"{db_name}.sqlite"
        
        if not schema:
            schema = {"id": "INTEGER PRIMARY KEY", "data": "TEXT"}
        
        # Build CREATE TABLE statement
        columns = []
        for col_name, col_type in schema.items():
            columns.append(f"{col_name} {col_type}")
        
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(create_sql)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            raise ValueError(f"Failed to create table: {e}")
        
        table = Table.create_new(table_name, db_name, "relational", schema)
        return table
    
    def _create_nosql_table(self, db_name: str, table_name: str) -> Table:
        """Create a NoSQL table (JSON file)"""
        db_dir = self.nosql_root / db_name
        table_file = db_dir / f"{table_name}.json"
        
        if table_file.exists():
            raise ValueError(f"Table '{table_name}' already exists")
        
        # Create empty JSON array
        with open(table_file, 'w') as f:
            json.dump([], f)
        
        table = Table.create_new(table_name, db_name, "nosql")
        return table
    
    def list_tables(self, db_name: str) -> List[Table]:
        """List all tables in a database"""
        if db_name not in self._databases:
            raise ValueError(f"Database '{db_name}' does not exist")
        
        db = self._databases[db_name]
        tables = []
        
        if db.db_type == "relational":
            db_path = self.relational_root / f"{db_name}.sqlite"
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                for row in cursor.fetchall():
                    table_name = row[0]
                    # Get schema
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    schema = {col[1]: col[2] for col in cursor.fetchall()}
                    # Get record count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    
                    table = Table.create_new(table_name, db_name, "relational", schema)
                    table.record_count = count
                    tables.append(table)
                conn.close()
            except sqlite3.Error as e:
                raise ValueError(f"Failed to list tables: {e}")
        else:  # nosql
            db_dir = self.nosql_root / db_name
            for table_file in db_dir.glob("*.json"):
                table_name = table_file.stem
                try:
                    with open(table_file, 'r') as f:
                        records = json.load(f)
                        table = Table.create_new(table_name, db_name, "nosql")
                        table.record_count = len(records)
                        tables.append(table)
                except (json.JSONDecodeError, IOError):
                    pass
        
        return tables
    
    def insert_record(self, db_name: str, table_name: str, record: Dict[str, Any]):
        """Insert a record into a table"""
        if db_name not in self._databases:
            raise ValueError(f"Database '{db_name}' does not exist")
        
        db = self._databases[db_name]
        
        if db.db_type == "relational":
            self._insert_relational_record(db_name, table_name, record)
        else:
            self._insert_nosql_record(db_name, table_name, record)
    
    def _insert_relational_record(self, db_name: str, table_name: str, record: Dict[str, Any]):
        """Insert record into relational table"""
        db_path = self.relational_root / f"{db_name}.sqlite"
        
        columns = list(record.keys())
        values = list(record.values())
        placeholders = ','.join(['?' for _ in values])
        
        sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            raise ValueError(f"Failed to insert record: {e}")
    
    def _insert_nosql_record(self, db_name: str, table_name: str, record: Dict[str, Any]):
        """Insert record into NoSQL table"""
        db_dir = self.nosql_root / db_name
        table_file = db_dir / f"{table_name}.json"
        
        if not table_file.exists():
            raise ValueError(f"Table '{table_name}' does not exist")
        
        try:
            with open(table_file, 'r') as f:
                records = json.load(f)
            
            records.append(record)
            
            with open(table_file, 'w') as f:
                json.dump(records, f, indent=2)
        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"Failed to insert record: {e}")
    
    def list_records(self, db_name: str, table_name: str) -> List[Dict[str, Any]]:
        """List all records in a table"""
        if db_name not in self._databases:
            raise ValueError(f"Database '{db_name}' does not exist")
        
        db = self._databases[db_name]
        
        if db.db_type == "relational":
            return self._list_relational_records(db_name, table_name)
        else:
            return self._list_nosql_records(db_name, table_name)
    
    def _list_relational_records(self, db_name: str, table_name: str) -> List[Dict[str, Any]]:
        """List records from relational table"""
        db_path = self.relational_root / f"{db_name}.sqlite"
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            records = [dict(row) for row in rows]
            conn.close()
            return records
        except sqlite3.Error as e:
            raise ValueError(f"Failed to list records: {e}")
    
    def _list_nosql_records(self, db_name: str, table_name: str) -> List[Dict[str, Any]]:
        """List records from NoSQL table"""
        db_dir = self.nosql_root / db_name
        table_file = db_dir / f"{table_name}.json"
        
        if not table_file.exists():
            raise ValueError(f"Table '{table_name}' does not exist")
        
        try:
            with open(table_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"Failed to list records: {e}")
    
    def delete_table(self, db_name: str, table_name: str) -> bool:
        """Delete a table"""
        if db_name not in self._databases:
            raise ValueError(f"Database '{db_name}' does not exist")
        
        db = self._databases[db_name]
        
        if db.db_type == "relational":
            db_path = self.relational_root / f"{db_name}.sqlite"
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                conn.commit()
                conn.close()
            except sqlite3.Error as e:
                raise ValueError(f"Failed to delete table: {e}")
        else:  # nosql
            db_dir = self.nosql_root / db_name
            table_file = db_dir / f"{table_name}.json"
            if table_file.exists():
                table_file.unlink()
        
        return True
