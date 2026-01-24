"""
Comprehensive IAM Integration Test - All Services
Tests that all services (Compute, Storage, Database, Serverless) properly enforce IAM permissions
"""

import pytest
from core.iam import IAMManager, Policy, PolicyStatement, Effect
from core.events import EventBus
from services.compute_service import ComputeService
from services.storage_service import StorageService
from services.database_service import DatabaseService
from services.serverless_service import ServerlessService


@pytest.fixture(scope="function")
def setup_services():
    """Setup all services with IAM"""
    iam = IAMManager()
    event_bus = EventBus()
    
    compute = ComputeService()
    storage = StorageService()
    database = DatabaseService()
    serverless = ServerlessService()
    
    # Use existing admin user
    admin = iam.users.get("admin")
    
    # Create or get limited user
    if "test_limited_user" not in iam.users:
        limited_user = iam.create_user("test_limited_user", tags={"email": "limited@cloudsim.local"})
        
        # Create read-only policy
        readonly_policy = Policy(
            name="ReadOnlyPolicy",
            statements=[
                PolicyStatement(
                    effect=Effect.ALLOW,
                    actions=[
                        "compute:ListInstances",
                        "storage:ListBuckets",
                        "database:ListDatabases",
                        "serverless:ListFunctions"
                    ],
                    resources=["*"]
                )
            ],
            description="Read-only access to all services"
        )
        
        iam.create_policy(readonly_policy)
        limited_user.policies.append("ReadOnlyPolicy")
    else:
        limited_user = iam.users["test_limited_user"]
    
    return {
        "iam": iam,
        "compute": compute,
        "storage": storage,
        "database": database,
        "serverless": serverless,
        "admin": admin,
        "limited_user": limited_user
    }




def test_compute_service_iam_integration(setup_services):
    """Test that ComputeService properly enforces IAM permissions"""
    services = setup_services
    iam = services["iam"]
    compute = services["compute"]
    
    # Admin can create instance
    iam.set_current_user("admin")
    instance = compute.create_instance("test-instance", cpu=1, memory=512)
    assert instance is not None
    assert instance.name == "test-instance"
    
    # Limited user cannot create instance
    iam.set_current_user("test_limited_user")
    with pytest.raises(PermissionError) as exc_info:
        compute.create_instance("unauthorized-instance", cpu=1, memory=512)
    assert "compute:CreateInstance" in str(exc_info.value)
    
    # Limited user can list instances
    instances = compute.list_instances()
    assert len(instances) > 0


def test_storage_service_iam_integration(setup_services):
    """Test that StorageService properly enforces IAM permissions"""
    services = setup_services
    iam = services["iam"]
    storage = services["storage"]
    
    # Admin can create bucket
    iam.set_current_user("admin")
    import time
    bucket_name = f"test-bucket-{int(time.time())}"
    bucket = storage.create_bucket(bucket_name)
    assert bucket is not None
    assert bucket.name == bucket_name
    
    # Limited user cannot create bucket
    iam.set_current_user("test_limited_user")
    with pytest.raises(PermissionError) as exc_info:
        storage.create_bucket(f"unauthorized-bucket-{int(time.time())}")
    assert "storage:CreateBucket" in str(exc_info.value)
    
    # Limited user can list buckets
    buckets = storage.list_buckets()
    assert len(buckets) > 0


def test_database_service_iam_integration(setup_services):
    """Test that DatabaseService properly enforces IAM permissions"""
    services = setup_services
    iam = services["iam"]
    database = services["database"]
    
    import time
    db_name = f"test-db-{int(time.time())}"
    
    # Admin can create database
    iam.set_current_user("admin")
    db = database.create_database(db_name, "relational")
    assert db is not None
    assert db.name == db_name
    
    # Limited user cannot create database
    iam.set_current_user("test_limited_user")
    with pytest.raises(PermissionError) as exc_info:
        database.create_database(f"unauthorized-db-{int(time.time())}", "relational")
    assert "database:CreateDatabase" in str(exc_info.value)
    
    # Limited user can list databases
    databases = database.list_databases()
    assert len(databases) > 0
    
    # Admin can create table
    iam.set_current_user("admin")
    table = database.create_table(db_name, "users", {"id": "int", "name": "string"})
    assert table is not None
    
    # Limited user cannot create table
    iam.set_current_user("test_limited_user")
    with pytest.raises(PermissionError) as exc_info:
        database.create_table(db_name, "unauthorized-table", {"id": "int"})
    assert "database:CreateTable" in str(exc_info.value)


def test_serverless_service_iam_integration(setup_services):
    """Test that ServerlessService properly enforces IAM permissions"""
    services = setup_services
    iam = services["iam"]
    serverless = services["serverless"]
    
    # Admin can create function
    iam.set_current_user("admin")
    import time
    function_code = "def handler(event, context):\n    return {'result': 'success'}"
    func_name = f"test-function-{int(time.time())}"
    func = serverless.create_function(func_name, function_code, "handler")
    assert func is not None
    assert func.name == func_name
    
    # Limited user cannot create function
    iam.set_current_user("test_limited_user")
    with pytest.raises(PermissionError) as exc_info:
        serverless.create_function(f"unauthorized-function-{int(time.time())}", function_code, "handler")
    assert "serverless:CreateFunction" in str(exc_info.value)
    
    # Limited user can list functions
    functions = serverless.list_functions()
    assert len(functions) > 0
    
    # Admin can invoke function
    iam.set_current_user("admin")
    result = serverless.invoke_function("test-function", {})
    assert result is not None
    
    # Limited user cannot invoke function
    iam.set_current_user("test_limited_user")
    with pytest.raises(PermissionError) as exc_info:
        serverless.invoke_function("test-function", {})
    assert "serverless:InvokeFunction" in str(exc_info.value)


def test_cross_service_iam_consistency(setup_services):
    """Test that IAM is consistently enforced across all services"""
    services = setup_services
    iam = services["iam"]
    
    # Set limited user
    iam.set_current_user("test_limited_user")
    
    # Verify that limited user is denied for all create operations
    with pytest.raises(PermissionError):
        services["compute"].create_instance("test", "t2.micro")
    
    with pytest.raises(PermissionError):
        services["storage"].create_bucket("test")
    
    with pytest.raises(PermissionError):
        services["database"].create_database("test", "postgresql")
    
    with pytest.raises(PermissionError):
        services["serverless"].create_function("test", "code", "handler")
    
    # Verify that limited user can perform all list operations
    assert services["compute"].list_instances() is not None
    assert services["storage"].list_buckets() is not None
    assert services["database"].list_databases() is not None
    assert services["serverless"].list_functions() is not None


def test_regional_isolation(setup_services):
    """Test that resources are properly isolated by region"""
    services = setup_services
    iam = services["iam"]
    compute = services["compute"]
    storage = services["storage"]
    database = services["database"]
    serverless = services["serverless"]
    
    iam.set_current_user("admin")
    
    import time
    ts = int(time.time())
    
    # Create resources in different regions
    instance_us = compute.create_instance(f"us-instance-{ts}", cpu=1, memory=512, region="us-east-1")
    instance_eu = compute.create_instance(f"eu-instance-{ts}", cpu=1, memory=512, region="eu-west-1")
    
    bucket_us = storage.create_bucket(f"us-bucket-{ts}", region="us-east-1")
    bucket_eu = storage.create_bucket(f"eu-bucket-{ts}", region="eu-west-1")
    
    db_us = database.create_database(f"us-db-{ts}", "relational", region="us-east-1")
    db_eu = database.create_database(f"eu-db-{ts}", "relational", region="eu-west-1")
    
    func_us = serverless.create_function(f"us-func-{ts}", "def handler(event, context): pass", "handler", region="us-east-1")
    func_eu = serverless.create_function(f"eu-func-{ts}", "def handler(event, context): pass", "handler", region="eu-west-1")
    
    # Verify region filtering
    us_instances = compute.list_instances(region="us-east-1")
    assert len(us_instances) >= 1
    assert all(i.region == "us-east-1" for i in us_instances)
    
    eu_buckets = storage.list_buckets(region="eu-west-1")
    assert len(eu_buckets) >= 1
    assert all(b.region == "eu-west-1" for b in eu_buckets)
    
    us_databases = database.list_databases(region="us-east-1")
    assert len(us_databases) >= 1
    assert all(db.region == "us-east-1" for db in us_databases)
    
    eu_functions = serverless.list_functions(region="eu-west-1")
    assert len(eu_functions) >= 1
    assert all(f.region == "eu-west-1" for f in eu_functions)


def test_resource_ownership(setup_services):
    """Test that resources track ownership properly"""
    services = setup_services
    iam = services["iam"]
    
    iam.set_current_user("admin")
    
    import time
    ts = int(time.time())
    
    # Create resources
    instance = services["compute"].create_instance(f"owned-instance-{ts}", cpu=1, memory=512)
    bucket = services["storage"].create_bucket(f"owned-bucket-{ts}")
    db = services["database"].create_database(f"owned-db-{ts}", "relational")
    func = services["serverless"].create_function(f"owned-func-{ts}", "def handler(event, context): pass", "handler")
    
    # Verify ownership
    assert instance.owner == "admin"
    assert bucket.owner == "admin"
    assert db.owner == "admin"
    assert func.owner == "admin"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
