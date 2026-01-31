"""
CloudWatch Alarms Service
Handles alarm CRUD, evaluation, and actions
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.models.cloudwatch_alarm import CloudWatchAlarm
from app.models.instance import Instance
from app.services.cloudwatch_service import CloudWatchService
from app.services.instance_service import InstanceService
from app.core.exceptions import ValidationError, ResourceNotFoundError
from app.core.resource_ids import generate_id, ResourceType


class CloudWatchAlarmsService:
    """Service for CloudWatch Alarms operations."""
    
    def __init__(self):
        self.cloudwatch_service = CloudWatchService()
        self.instance_service = InstanceService()
    
    # ==================== Alarm CRUD ====================
    
    def put_metric_alarm(
        self,
        db: Session,
        account_id: str,
        alarm_name: str,
        comparison_operator: str,
        evaluation_periods: int,
        metric_name: str,
        namespace: str,
        period: int,
        statistic: str,
        threshold: float,
        actions_enabled: bool = True,
        alarm_actions: Optional[List[str]] = None,
        alarm_description: Optional[str] = None,
        datapoints_to_alarm: Optional[int] = None,
        dimensions: Optional[Dict[str, str]] = None,
        ok_actions: Optional[List[str]] = None,
        insufficient_data_actions: Optional[List[str]] = None,
        treat_missing_data: str = "missing"
    ) -> CloudWatchAlarm:
        """
        Create or update a metric alarm.
        
        Args:
            db: Database session
            account_id: Account ID
            alarm_name: Alarm name
            comparison_operator: GreaterThanThreshold, LessThanThreshold, etc.
            evaluation_periods: Number of periods to evaluate
            metric_name: Metric name
            namespace: Metric namespace
            period: Period in seconds
            statistic: Average, Sum, Minimum, Maximum, SampleCount
            threshold: Threshold value
            actions_enabled: Whether actions are enabled
            alarm_actions: Actions when ALARM state
            alarm_description: Description
            datapoints_to_alarm: M of N evaluation (optional)
            dimensions: Metric dimensions
            ok_actions: Actions when OK state
            insufficient_data_actions: Actions when INSUFFICIENT_DATA
            treat_missing_data: How to treat missing data
        
        Returns:
            Created or updated alarm
        """
        # Validate
        valid_operators = [
            "GreaterThanThreshold", "GreaterThanOrEqualToThreshold",
            "LessThanThreshold", "LessThanOrEqualToThreshold"
        ]
        if comparison_operator not in valid_operators:
            raise ValidationError(f"Invalid comparison operator: {comparison_operator}")
        
        valid_statistics = ["Average", "Sum", "Minimum", "Maximum", "SampleCount"]
        if statistic not in valid_statistics:
            raise ValidationError(f"Invalid statistic: {statistic}")
        
        if period < 60:
            raise ValidationError("Period must be at least 60 seconds")
        
        if evaluation_periods < 1:
            raise ValidationError("Evaluation periods must be at least 1")
        
        valid_missing_data = ["missing", "notBreaching", "breaching", "ignore"]
        if treat_missing_data not in valid_missing_data:
            raise ValidationError(f"Invalid treat_missing_data: {treat_missing_data}")
        
        # Check if alarm exists
        existing = db.query(CloudWatchAlarm).filter(
            CloudWatchAlarm.alarm_name == alarm_name,
            CloudWatchAlarm.account_id == account_id
        ).first()
        
        if existing:
            # Update existing
            existing.comparison_operator = comparison_operator
            existing.evaluation_periods = evaluation_periods
            existing.metric_name = metric_name
            existing.namespace = namespace
            existing.period = period
            existing.statistic = statistic
            existing.threshold = threshold
            existing.actions_enabled = actions_enabled
            existing.alarm_description = alarm_description
            existing.datapoints_to_alarm = datapoints_to_alarm
            existing.dimensions = json.dumps(dimensions) if dimensions else None
            existing.alarm_actions = json.dumps(alarm_actions) if alarm_actions else None
            existing.ok_actions = json.dumps(ok_actions) if ok_actions else None
            existing.insufficient_data_actions = json.dumps(insufficient_data_actions) if insufficient_data_actions else None
            existing.treat_missing_data = treat_missing_data
            existing.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new
        alarm_id = generate_id(ResourceType.ALARM)
        
        alarm = CloudWatchAlarm(
            alarm_id=alarm_id,
            alarm_name=alarm_name,
            alarm_description=alarm_description,
            account_id=account_id,
            namespace=namespace,
            metric_name=metric_name,
            dimensions=json.dumps(dimensions) if dimensions else None,
            statistic=statistic,
            period=period,
            evaluation_periods=evaluation_periods,
            threshold=threshold,
            comparison_operator=comparison_operator,
            treat_missing_data=treat_missing_data,
            datapoints_to_alarm=datapoints_to_alarm,
            alarm_actions=json.dumps(alarm_actions) if alarm_actions else None,
            ok_actions=json.dumps(ok_actions) if ok_actions else None,
            insufficient_data_actions=json.dumps(insufficient_data_actions) if insufficient_data_actions else None,
            state_value="INSUFFICIENT_DATA",
            state_reason="Alarm just created",
            state_updated_timestamp=datetime.utcnow(),
            actions_enabled=actions_enabled,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(alarm)
        db.commit()
        db.refresh(alarm)
        
        return alarm
    
    def describe_alarms(
        self,
        db: Session,
        account_id: str,
        alarm_names: Optional[List[str]] = None,
        alarm_name_prefix: Optional[str] = None,
        state_value: Optional[str] = None,
        max_records: int = 100
    ) -> List[CloudWatchAlarm]:
        """List alarms."""
        query = db.query(CloudWatchAlarm).filter(
            CloudWatchAlarm.account_id == account_id
        )
        
        if alarm_names:
            query = query.filter(CloudWatchAlarm.alarm_name.in_(alarm_names))
        
        if alarm_name_prefix:
            query = query.filter(CloudWatchAlarm.alarm_name.startswith(alarm_name_prefix))
        
        if state_value:
            query = query.filter(CloudWatchAlarm.state_value == state_value)
        
        return query.limit(max_records).all()
    
    def delete_alarms(
        self,
        db: Session,
        account_id: str,
        alarm_names: List[str]
    ):
        """Delete alarms."""
        db.query(CloudWatchAlarm).filter(
            CloudWatchAlarm.alarm_name.in_(alarm_names),
            CloudWatchAlarm.account_id == account_id
        ).delete(synchronize_session=False)
        
        db.commit()
    
    def set_alarm_state(
        self,
        db: Session,
        account_id: str,
        alarm_name: str,
        state_value: str,
        state_reason: str
    ) -> CloudWatchAlarm:
        """Manually set alarm state (for testing)."""
        alarm = db.query(CloudWatchAlarm).filter(
            CloudWatchAlarm.alarm_name == alarm_name,
            CloudWatchAlarm.account_id == account_id
        ).first()
        
        if not alarm:
            raise ResourceNotFoundError(f"Alarm '{alarm_name}' not found")
        
        valid_states = ["OK", "ALARM", "INSUFFICIENT_DATA"]
        if state_value not in valid_states:
            raise ValidationError(f"Invalid state: {state_value}")
        
        alarm.state_value = state_value
        alarm.state_reason = state_reason
        alarm.state_updated_timestamp = datetime.utcnow()
        
        db.commit()
        db.refresh(alarm)
        
        return alarm
    
    # ==================== Alarm Evaluation ====================
    
    def evaluate_alarm(
        self,
        db: Session,
        alarm: CloudWatchAlarm
    ) -> Dict[str, any]:
        """
        Evaluate an alarm against current metrics.
        
        Returns:
            {
                "alarm": alarm,
                "old_state": str,
                "new_state": str,
                "reason": str,
                "breaching_datapoints": int,
                "total_datapoints": int
            }
        """
        old_state = alarm.state_value
        
        # Get metrics for evaluation period
        end_time = datetime.utcnow()
        lookback = alarm.period * alarm.evaluation_periods
        start_time = end_time - timedelta(seconds=lookback)
        
        dimensions = json.loads(alarm.dimensions) if alarm.dimensions else None
        
        try:
            stats = self.cloudwatch_service.get_metric_statistics(
                db,
                alarm.account_id,
                alarm.namespace,
                alarm.metric_name,
                start_time,
                end_time,
                alarm.period,
                [alarm.statistic],
                dimensions
            )
        except Exception as e:
            # Error getting metrics
            return {
                "alarm": alarm,
                "old_state": old_state,
                "new_state": "INSUFFICIENT_DATA",
                "reason": f"Failed to get metrics: {str(e)}",
                "breaching_datapoints": 0,
                "total_datapoints": 0
            }
        
        datapoints = stats.get("datapoints", [])
        
        if not datapoints:
            # No data
            new_state = self._handle_missing_data(alarm, "INSUFFICIENT_DATA")
            return {
                "alarm": alarm,
                "old_state": old_state,
                "new_state": new_state,
                "reason": "No datapoints available",
                "breaching_datapoints": 0,
                "total_datapoints": 0
            }
        
        # Evaluate each datapoint
        breaching_count = 0
        stat_key = alarm.statistic.lower()
        
        for dp in datapoints:
            value = dp.get(stat_key)
            if value is None:
                continue
            
            if self._is_breaching(value, alarm.threshold, alarm.comparison_operator):
                breaching_count += 1
        
        total_datapoints = len(datapoints)
        
        # Determine state
        required_breaches = alarm.datapoints_to_alarm or alarm.evaluation_periods
        
        if breaching_count >= required_breaches:
            new_state = "ALARM"
            reason = f"{breaching_count} datapoints were greater than the threshold ({alarm.threshold})"
        elif breaching_count == 0:
            new_state = "OK"
            reason = f"Threshold not breached (0/{total_datapoints} datapoints)"
        else:
            new_state = "OK"
            reason = f"Threshold breached but not enough times ({breaching_count}/{required_breaches})"
        
        return {
            "alarm": alarm,
            "old_state": old_state,
            "new_state": new_state,
            "reason": reason,
            "breaching_datapoints": breaching_count,
            "total_datapoints": total_datapoints
        }
    
    def evaluate_all_alarms(
        self,
        db: Session
    ) -> List[Dict[str, any]]:
        """Evaluate all alarms across all accounts."""
        alarms = db.query(CloudWatchAlarm).all()
        
        results = []
        for alarm in alarms:
            try:
                result = self.evaluate_alarm(db, alarm)
                
                # Update state if changed
                if result["new_state"] != result["old_state"]:
                    alarm.state_value = result["new_state"]
                    alarm.state_reason = result["reason"]
                    alarm.state_updated_timestamp = datetime.utcnow()
                    db.commit()
                    
                    # Execute actions if enabled
                    if alarm.actions_enabled:
                        self._execute_alarm_actions(db, alarm, result["old_state"], result["new_state"])
                
                results.append(result)
            except Exception as e:
                print(f"Error evaluating alarm {alarm.alarm_name}: {str(e)}")
                continue
        
        return results
    
    def _is_breaching(self, value: float, threshold: float, operator: str) -> bool:
        """Check if value breaches threshold."""
        if operator == "GreaterThanThreshold":
            return value > threshold
        elif operator == "GreaterThanOrEqualToThreshold":
            return value >= threshold
        elif operator == "LessThanThreshold":
            return value < threshold
        elif operator == "LessThanOrEqualToThreshold":
            return value <= threshold
        return False
    
    def _handle_missing_data(self, alarm: CloudWatchAlarm, default_state: str) -> str:
        """Handle missing data based on alarm configuration."""
        if alarm.treat_missing_data == "missing":
            return "INSUFFICIENT_DATA"
        elif alarm.treat_missing_data == "notBreaching":
            return "OK"
        elif alarm.treat_missing_data == "breaching":
            return "ALARM"
        elif alarm.treat_missing_data == "ignore":
            return alarm.state_value  # Keep current state
        return default_state
    
    # ==================== Alarm Actions ====================
    
    def _execute_alarm_actions(
        self,
        db: Session,
        alarm: CloudWatchAlarm,
        old_state: str,
        new_state: str
    ):
        """Execute alarm actions based on state transition."""
        actions = []
        
        if new_state == "ALARM" and alarm.alarm_actions:
            actions = json.loads(alarm.alarm_actions)
        elif new_state == "OK" and alarm.ok_actions:
            actions = json.loads(alarm.ok_actions)
        elif new_state == "INSUFFICIENT_DATA" and alarm.insufficient_data_actions:
            actions = json.loads(alarm.insufficient_data_actions)
        
        for action_arn in actions:
            try:
                self._execute_action(db, alarm, action_arn)
            except Exception as e:
                print(f"Error executing action {action_arn}: {str(e)}")
    
    def _execute_action(
        self,
        db: Session,
        alarm: CloudWatchAlarm,
        action_arn: str
    ):
        """
        Execute a single alarm action.
        
        Supported actions:
        - arn:aws:automate:region:ec2:stop (Stop EC2 instance)
        - arn:aws:automate:region:ec2:terminate (Terminate EC2 instance)
        - arn:aws:automate:region:ec2:reboot (Reboot EC2 instance)
        """
        # Parse action ARN
        # Format: arn:aws:automate:region:ec2:action
        if not action_arn.startswith("arn:aws:automate:"):
            print(f"Unsupported action ARN: {action_arn}")
            return
        
        parts = action_arn.split(":")
        if len(parts) < 6:
            print(f"Invalid action ARN format: {action_arn}")
            return
        
        service = parts[4]  # ec2
        action = parts[5]   # stop, terminate, reboot
        
        if service != "ec2":
            print(f"Unsupported service: {service}")
            return
        
        # Get instance ID from alarm dimensions
        if not alarm.dimensions:
            print("Alarm has no dimensions, cannot determine instance")
            return
        
        dimensions = json.loads(alarm.dimensions)
        instance_id = dimensions.get("InstanceId")
        
        if not instance_id:
            print("Alarm dimensions do not contain InstanceId")
            return
        
        # Execute EC2 action
        try:
            if action == "stop":
                self.instance_service.stop_instance(db, alarm.account_id, instance_id)
                print(f"Stopped instance {instance_id} due to alarm {alarm.alarm_name}")
            elif action == "terminate":
                self.instance_service.terminate_instance(db, alarm.account_id, instance_id)
                print(f"Terminated instance {instance_id} due to alarm {alarm.alarm_name}")
            elif action == "reboot":
                self.instance_service.reboot_instance(db, alarm.account_id, instance_id)
                print(f"Rebooted instance {instance_id} due to alarm {alarm.alarm_name}")
            else:
                print(f"Unsupported EC2 action: {action}")
        except Exception as e:
            print(f"Error executing EC2 action {action} on {instance_id}: {str(e)}")


