"""
CloudWatch Alarms API Routes
IAM-protected endpoints for metric alarms
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.models.iam_user import User
from app.services.cloudwatch_alarms_service import CloudWatchAlarmsService
from app.schemas.cloudwatch_alarms import *
from app.core.exceptions import ValidationError, ResourceNotFoundError
from app.api.v1.auth import get_current_user


router = APIRouter()
alarms_service = CloudWatchAlarmsService()


@router.post("/alarms", response_model=PutMetricAlarmResponse)
def put_metric_alarm(
    request: PutMetricAlarmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create or update a metric alarm.
    Required IAM permission: cloudwatch:PutMetricAlarm
    """
    try:
        alarm = alarms_service.put_metric_alarm(
            db,
            current_user.account_id,
            request.alarm_name,
            request.comparison_operator,
            request.evaluation_periods,
            request.metric_name,
            request.namespace,
            request.period,
            request.statistic,
            request.threshold,
            request.actions_enabled,
            request.alarm_actions,
            request.alarm_description,
            request.datapoints_to_alarm,
            request.dimensions,
            request.ok_actions,
            request.insufficient_data_actions,
            request.treat_missing_data
        )
        
        return PutMetricAlarmResponse(
            message=f"Alarm '{request.alarm_name}' created/updated successfully",
            alarm_id=alarm.alarm_id,
            alarm_name=alarm.alarm_name
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alarms/describe", response_model=DescribeAlarmsResponse)
def describe_alarms(
    request: DescribeAlarmsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Describe metric alarms.
    Required IAM permission: cloudwatch:DescribeAlarms
    """
    try:
        alarms = alarms_service.describe_alarms(
            db,
            current_user.account_id,
            request.alarm_names,
            request.alarm_name_prefix,
            request.state_value,
            request.max_records
        )
        
        alarm_infos = []
        for alarm in alarms:
            alarm_info = AlarmInfo(
                alarm_id=alarm.alarm_id,
                alarm_name=alarm.alarm_name,
                alarm_description=alarm.alarm_description,
                namespace=alarm.namespace,
                metric_name=alarm.metric_name,
                dimensions=json.loads(alarm.dimensions) if alarm.dimensions else None,
                statistic=alarm.statistic,
                period=alarm.period,
                evaluation_periods=alarm.evaluation_periods,
                threshold=alarm.threshold,
                comparison_operator=alarm.comparison_operator,
                treat_missing_data=alarm.treat_missing_data,
                datapoints_to_alarm=alarm.datapoints_to_alarm,
                actions_enabled=alarm.actions_enabled,
                alarm_actions=json.loads(alarm.alarm_actions) if alarm.alarm_actions else None,
                ok_actions=json.loads(alarm.ok_actions) if alarm.ok_actions else None,
                insufficient_data_actions=json.loads(alarm.insufficient_data_actions) if alarm.insufficient_data_actions else None,
                state_value=alarm.state_value,
                state_reason=alarm.state_reason,
                state_updated_timestamp=alarm.state_updated_timestamp,
                created_at=alarm.created_at,
                updated_at=alarm.updated_at
            )
            alarm_infos.append(alarm_info)
        
        return DescribeAlarmsResponse(
            metric_alarms=alarm_infos
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/alarms", response_model=DeleteAlarmsResponse)
def delete_alarms(
    request: DeleteAlarmsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete metric alarms.
    Required IAM permission: cloudwatch:DeleteAlarms
    """
    try:
        alarms_service.delete_alarms(
            db,
            current_user.account_id,
            request.alarm_names
        )
        
        return DeleteAlarmsResponse(
            message=f"Deleted {len(request.alarm_names)} alarms",
            deleted_count=len(request.alarm_names)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/alarms/state", response_model=SetAlarmStateResponse)
def set_alarm_state(
    request: SetAlarmStateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set alarm state (for testing).
    Required IAM permission: cloudwatch:SetAlarmState
    """
    try:
        alarm = alarms_service.set_alarm_state(
            db,
            current_user.account_id,
            request.alarm_name,
            request.state_value,
            request.state_reason
        )
        
        return SetAlarmStateResponse(
            message=f"Alarm state set to {request.state_value}",
            alarm_name=alarm.alarm_name,
            state_value=alarm.state_value
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

