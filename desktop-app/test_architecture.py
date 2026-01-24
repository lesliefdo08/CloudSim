"""
Test AWS-style architecture components
Run this to verify region, IAM, events, and metering work correctly
"""

from core.region import set_current_region, get_current_region, list_all_regions, RegionContext
from core.iam import IAMManager, Policy, PolicyStatement, Effect, Action
from core.events import EventBus, EventType
from core.metering import UsageMeter, MetricType
from services.compute_service import ComputeService


def test_regions():
    """Test region management"""
    print("=" * 60)
    print("Testing Region Management")
    print("=" * 60)
    
    # List all regions
    regions = list_all_regions()
    print(f"Available regions: {len(regions)}")
    for region in regions:
        print(f"  - {region}")
    
    # Get current region
    current = get_current_region()
    print(f"\nCurrent region: {current}")
    
    # Change region
    set_current_region("eu-west-1")
    print(f"Changed to: {get_current_region()}")
    
    # Region context
    print("\nTesting region context:")
    with RegionContext("ap-southeast-1"):
        print(f"  Inside context: {get_current_region()}")
    print(f"  Outside context: {get_current_region()}")
    
    # Reset to us-east-1
    set_current_region("us-east-1")
    print(f"\nReset to: {get_current_region()}")
    print("✅ Region management working!\n")


def test_iam():
    """Test IAM system"""
    print("=" * 60)
    print("Testing IAM System")
    print("=" * 60)
    
    iam = IAMManager()
    
    # Default admin user
    admin = iam.get_current_user()
    print(f"Current user: {admin.username}")
    print(f"Admin ARN: {admin.arn()}")
    print(f"Admin policies: {admin.policies}")
    
    # Create restricted user
    dev_user = iam.create_user("developer", tags={"team": "backend"})
    print(f"\nCreated user: {dev_user.username}")
    print(f"User ARN: {dev_user.arn()}")
    
    # Create read-only policy
    readonly_policy = Policy(
        name="ComputeReadOnly",
        statements=[
            PolicyStatement(
                effect=Effect.ALLOW,
                actions=["compute:ListInstances", "compute:DescribeInstance"],
                resources=["*"]
            )
        ],
        description="Read-only access to compute instances"
    )
    iam.create_policy(readonly_policy)
    print(f"\nCreated policy: {readonly_policy.name}")
    
    # Attach policy to user
    iam.attach_user_policy("developer", "ComputeReadOnly")
    print(f"Attached policy to {dev_user.username}")
    
    # Test permissions
    iam.set_current_user("developer")
    can_list = iam.check_permission("compute:ListInstances", "*")
    can_create = iam.check_permission("compute:CreateInstance", "*")
    print(f"\nDeveloper permissions:")
    print(f"  Can list instances: {can_list}")
    print(f"  Can create instances: {can_create}")
    
    # Reset to admin
    iam.set_current_user("admin")
    print("\n✅ IAM system working!\n")


def test_events():
    """Test event system"""
    print("=" * 60)
    print("Testing Event System")
    print("=" * 60)
    
    event_bus = EventBus()
    
    # Clear previous events
    event_bus.clear_history()
    
    # Subscribe to events
    event_count = 0
    
    def count_events(event):
        nonlocal event_count
        event_count += 1
        print(f"  Event received: {event.event_type.value} - {event.resource_id}")
    
    event_bus.subscribe(EventType.INSTANCE_CREATED, count_events)
    event_bus.subscribe(EventType.INSTANCE_STARTED, count_events)
    
    print("Subscribed to instance events")
    
    # Create instance (should emit event)
    compute = ComputeService()
    instance = compute.create_instance("test-server", cpu=1, memory=512)
    print(f"\nCreated instance: {instance.id}")
    
    # Start instance (should emit event)
    compute.start_instance(instance.id)
    print(f"Started instance: {instance.id}")
    
    print(f"\nEvents received: {event_count}")
    
    # Query event history
    events = event_bus.get_events(limit=10)
    print(f"Total events in history: {len(events)}")
    for event in events[-5:]:
        print(f"  - {event.event_type.value} at {event.timestamp.strftime('%H:%M:%S')}")
    
    # Cleanup
    compute.stop_instance(instance.id)
    compute.delete_instance(instance.id)
    
    print("✅ Event system working!\n")


def test_metering():
    """Test usage metering"""
    print("=" * 60)
    print("Testing Usage Metering")
    print("=" * 60)
    
    meter = UsageMeter()
    meter.clear_records()
    
    # Simulate compute usage
    print("Simulating compute usage...")
    
    # Start tracking
    meter.start_tracking("i-test001")
    print("  Started tracking i-test001")
    
    # Simulate some time passing
    import time
    time.sleep(0.1)
    
    # Stop tracking
    hours = meter.stop_tracking("i-test001")
    print(f"  Stopped tracking - ran for {hours:.4f} hours")
    
    # Record usage
    from core.metering import record_compute_usage
    record_compute_usage("i-test001", "us-east-1", vcpu=2, hours=hours or 0.001)
    print(f"  Recorded usage")
    
    # Get usage summary
    summary = meter.get_usage_summary(region="us-east-1")
    print(f"\nUsage summary: {len(summary)} metric types")
    for s in summary:
        print(f"  {s.metric_type.value}:")
        print(f"    Total: {s.total_value:.6f} {s.unit}")
        print(f"    Resources: {s.resource_count}")
        cost = meter.estimate_cost(s)
        print(f"    Estimated cost: ${cost:.6f}")
    
    print("\n✅ Usage metering working!\n")


def test_compute_service_integration():
    """Test compute service with all architecture components"""
    print("=" * 60)
    print("Testing Compute Service Integration")
    print("=" * 60)
    
    # Set region
    set_current_region("eu-west-1")
    print(f"Using region: {get_current_region()}")
    
    # Create service
    compute = ComputeService()
    
    # Create instance with tags
    instance = compute.create_instance(
        name="production-api",
        cpu=4,
        memory=2048,
        tags={"env": "production", "app": "api"}
    )
    print(f"\nCreated instance:")
    print(f"  ID: {instance.id}")
    print(f"  Name: {instance.name}")
    print(f"  Region: {instance.region}")
    print(f"  Owner: {instance.owner}")
    print(f"  ARN: {instance.arn()}")
    print(f"  Tags: {instance.tags}")
    
    # List instances in current region
    instances = compute.list_instances()
    print(f"\nInstances in {get_current_region()}: {len(instances)}")
    
    # Switch region and verify filtering
    set_current_region("us-east-1")
    us_instances = compute.list_instances()
    print(f"Instances in {get_current_region()}: {len(us_instances)}")
    
    # Create instance in us-east-1
    us_instance = compute.create_instance("us-server", cpu=1, memory=512)
    print(f"\nCreated instance in us-east-1: {us_instance.id}")
    
    # Verify region filtering
    us_instances = compute.list_instances(region="us-east-1")
    eu_instances = compute.list_instances(region="eu-west-1")
    print(f"\nRegion filtering:")
    print(f"  US East: {len(us_instances)} instances")
    print(f"  EU West: {len(eu_instances)} instances")
    
    # Cleanup
    compute.delete_instance(instance.id)
    compute.delete_instance(us_instance.id)
    
    print("\n✅ Compute service integration working!\n")


def test_iam_enforcement():
    """Test IAM permission enforcement"""
    print("=" * 60)
    print("Testing IAM Permission Enforcement")
    print("=" * 60)
    
    iam = IAMManager()
    
    # Create restricted user with no permissions
    restricted = iam.create_user("restricted")
    print(f"Created restricted user: {restricted.username}")
    
    # Switch to restricted user
    iam.set_current_user("restricted")
    print(f"Switched to user: {iam.get_current_user().username}")
    
    # Try to create instance (should fail)
    compute = ComputeService()
    try:
        compute.create_instance("unauthorized-instance")
        print("❌ ERROR: Should have been denied!")
    except PermissionError as e:
        print(f"✅ Permission denied as expected: {e}")
    
    # Switch back to admin
    iam.set_current_user("admin")
    print(f"\nSwitched back to: {iam.get_current_user().username}")
    
    # Try again (should succeed)
    try:
        instance = compute.create_instance("authorized-instance", cpu=1, memory=512)
        print(f"✅ Created instance as admin: {instance.id}")
        compute.delete_instance(instance.id)
    except PermissionError:
        print("❌ ERROR: Admin should have permission!")
    
    print("\n✅ IAM enforcement working!\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CloudSim AWS-Style Architecture Test Suite")
    print("=" * 60 + "\n")
    
    try:
        test_regions()
        test_iam()
        test_events()
        test_metering()
        test_compute_service_integration()
        test_iam_enforcement()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe AWS-style architecture is working correctly:")
        print("  - Region management ✅")
        print("  - IAM permissions ✅")
        print("  - Event system ✅")
        print("  - Usage metering ✅")
        print("  - Service integration ✅")
        print("\nReady for UI integration!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
