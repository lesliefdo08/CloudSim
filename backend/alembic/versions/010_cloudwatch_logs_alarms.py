"""CloudWatch Logs and Alarms tables

Revision ID: 010_cloudwatch_logs_alarms
Revises: 009_cloudwatch_metrics
Create Date: 2024-01-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '010_cloudwatch_logs_alarms'
down_revision = '009_cloudwatch_metrics'
branch_labels = None
depends_on = None


def upgrade():
    """Create CloudWatch Logs and Alarms tables."""
    
    # ==================== Log Groups ====================
    op.create_table(
        'log_groups',
        sa.Column('log_group_name', sa.String(512), primary_key=True),
        sa.Column('account_id', sa.String(12), nullable=False),
        sa.Column('retention_in_days', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('stored_bytes', sa.Integer, nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(
            ['account_id'],
            ['iam_accounts.account_id'],
            name='fk_log_groups_account',
            ondelete='CASCADE'
        )
    )
    
    # Create indexes for log_groups
    op.create_index(
        'ix_log_groups_account',
        'log_groups',
        ['account_id', 'log_group_name']
    )
    
    # ==================== Log Streams ====================
    op.create_table(
        'log_streams',
        sa.Column('stream_id', sa.String(50), primary_key=True),
        sa.Column('log_group_name', sa.String(512), nullable=False),
        sa.Column('log_stream_name', sa.String(512), nullable=False),
        sa.Column('account_id', sa.String(12), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('first_event_timestamp', sa.DateTime, nullable=True),
        sa.Column('last_event_timestamp', sa.DateTime, nullable=True),
        sa.Column('last_ingestion_time', sa.DateTime, nullable=True),
        sa.Column('stored_bytes', sa.Integer, nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(
            ['log_group_name'],
            ['log_groups.log_group_name'],
            name='fk_log_streams_log_group',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['account_id'],
            ['iam_accounts.account_id'],
            name='fk_log_streams_account',
            ondelete='CASCADE'
        )
    )
    
    # Create indexes for log_streams
    op.create_index(
        'ix_log_streams_log_group_name',
        'log_streams',
        ['log_group_name']
    )
    
    op.create_index(
        'ix_log_streams_account',
        'log_streams',
        ['account_id', 'log_group_name']
    )
    
    op.create_index(
        'ix_log_streams_unique',
        'log_streams',
        ['log_group_name', 'log_stream_name'],
        unique=True
    )
    
    # ==================== Log Events ====================
    op.create_table(
        'log_events',
        sa.Column('event_id', sa.String(50), primary_key=True),
        sa.Column('stream_id', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('ingestion_time', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ['stream_id'],
            ['log_streams.stream_id'],
            name='fk_log_events_stream',
            ondelete='CASCADE'
        )
    )
    
    # Create indexes for log_events
    op.create_index(
        'ix_log_events_stream_id',
        'log_events',
        ['stream_id']
    )
    
    op.create_index(
        'ix_log_events_timestamp',
        'log_events',
        ['timestamp']
    )
    
    op.create_index(
        'ix_log_events_stream_time',
        'log_events',
        ['stream_id', 'timestamp']
    )
    
    # ==================== CloudWatch Alarms ====================
    op.create_table(
        'cloudwatch_alarms',
        sa.Column('alarm_id', sa.String(30), primary_key=True),
        sa.Column('alarm_name', sa.String(255), nullable=False),
        sa.Column('alarm_description', sa.Text, nullable=True),
        sa.Column('account_id', sa.String(12), nullable=False),
        
        # Metric configuration
        sa.Column('namespace', sa.String(255), nullable=False),
        sa.Column('metric_name', sa.String(255), nullable=False),
        sa.Column('dimensions', sa.Text, nullable=True),
        
        # Alarm configuration
        sa.Column('statistic', sa.String(50), nullable=False),
        sa.Column('period', sa.Integer, nullable=False),
        sa.Column('evaluation_periods', sa.Integer, nullable=False),
        sa.Column('threshold', sa.Float, nullable=False),
        sa.Column('comparison_operator', sa.String(50), nullable=False),
        sa.Column('treat_missing_data', sa.String(50), nullable=False, server_default='missing'),
        sa.Column('datapoints_to_alarm', sa.Integer, nullable=True),
        
        # Actions
        sa.Column('alarm_actions', sa.Text, nullable=True),
        sa.Column('ok_actions', sa.Text, nullable=True),
        sa.Column('insufficient_data_actions', sa.Text, nullable=True),
        
        # State
        sa.Column('state_value', sa.String(50), nullable=False, server_default='INSUFFICIENT_DATA'),
        sa.Column('state_reason', sa.Text, nullable=True),
        sa.Column('state_updated_timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
        
        # Metadata
        sa.Column('actions_enabled', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.ForeignKeyConstraint(
            ['account_id'],
            ['iam_accounts.account_id'],
            name='fk_cloudwatch_alarms_account',
            ondelete='CASCADE'
        )
    )
    
    # Create indexes for cloudwatch_alarms
    op.create_index(
        'ix_cloudwatch_alarms_alarm_name',
        'cloudwatch_alarms',
        ['alarm_name']
    )
    
    op.create_index(
        'ix_cloudwatch_alarms_account_name',
        'cloudwatch_alarms',
        ['account_id', 'alarm_name'],
        unique=True
    )
    
    op.create_index(
        'ix_cloudwatch_alarms_namespace_metric',
        'cloudwatch_alarms',
        ['namespace', 'metric_name']
    )
    
    op.create_index(
        'ix_cloudwatch_alarms_state',
        'cloudwatch_alarms',
        ['state_value']
    )


def downgrade():
    """Drop CloudWatch Logs and Alarms tables."""
    
    # Drop cloudwatch_alarms
    op.drop_index('ix_cloudwatch_alarms_state', 'cloudwatch_alarms')
    op.drop_index('ix_cloudwatch_alarms_namespace_metric', 'cloudwatch_alarms')
    op.drop_index('ix_cloudwatch_alarms_account_name', 'cloudwatch_alarms')
    op.drop_index('ix_cloudwatch_alarms_alarm_name', 'cloudwatch_alarms')
    op.drop_table('cloudwatch_alarms')
    
    # Drop log_events
    op.drop_index('ix_log_events_stream_time', 'log_events')
    op.drop_index('ix_log_events_timestamp', 'log_events')
    op.drop_index('ix_log_events_stream_id', 'log_events')
    op.drop_table('log_events')
    
    # Drop log_streams
    op.drop_index('ix_log_streams_unique', 'log_streams')
    op.drop_index('ix_log_streams_account', 'log_streams')
    op.drop_index('ix_log_streams_log_group_name', 'log_streams')
    op.drop_table('log_streams')
    
    # Drop log_groups
    op.drop_index('ix_log_groups_account', 'log_groups')
    op.drop_table('log_groups')
