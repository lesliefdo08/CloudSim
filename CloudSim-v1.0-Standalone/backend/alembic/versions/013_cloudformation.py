"""
CloudFormation Migration
Creates cloudformation_stacks and cloudformation_stack_resources tables
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# Revision identifiers
revision = '013_cloudformation'
down_revision = '012_lambda'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create CloudFormation tables."""
    
    # cloudformation_stacks table
    op.create_table(
        'cloudformation_stacks',
        sa.Column('stack_name', sa.String(128), primary_key=True, nullable=False),
        sa.Column('stack_id', sa.String(255), unique=True, nullable=False),
        sa.Column('account_id', sa.String(12), sa.ForeignKey('iam_accounts.account_id', ondelete='CASCADE'), nullable=False),
        
        # Template
        sa.Column('template_body', sa.Text, nullable=False),
        sa.Column('template_format', sa.String(10), nullable=False),
        
        # Stack status
        sa.Column('stack_status', sa.String(50), nullable=False),
        sa.Column('stack_status_reason', sa.Text, nullable=True),
        
        # Rollback configuration
        sa.Column('disable_rollback', sa.Boolean, nullable=False, default=False),
        sa.Column('rollback_configuration', sa.Text, nullable=True),
        
        # Parameters
        sa.Column('parameters', sa.Text, nullable=True),
        
        # Capabilities
        sa.Column('capabilities', sa.Text, nullable=True),
        
        # Tags
        sa.Column('tags', sa.Text, nullable=True),
        
        # Stack outputs
        sa.Column('outputs', sa.Text, nullable=True),
        
        # Drift detection
        sa.Column('drift_status', sa.String(50), nullable=True),
        sa.Column('last_drift_check_timestamp', sa.DateTime, nullable=True),
        
        # Notifications
        sa.Column('notification_arns', sa.Text, nullable=True),
        
        # Timeout
        sa.Column('timeout_in_minutes', sa.Integer, nullable=True),
        
        # Metadata
        sa.Column('creation_time', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('last_updated_time', sa.DateTime, nullable=True),
        sa.Column('deletion_time', sa.DateTime, nullable=True),
        
        # Parent stack (for nested stacks)
        sa.Column('parent_stack_id', sa.String(255), nullable=True),
        sa.Column('root_stack_id', sa.String(255), nullable=True),
        
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4'
    )
    
    # Create indexes
    op.create_index('ix_cfn_stacks_account', 'cloudformation_stacks', ['account_id'])
    op.create_index('ix_cfn_stacks_status', 'cloudformation_stacks', ['stack_status'])
    
    # cloudformation_stack_resources table
    op.create_table(
        'cloudformation_stack_resources',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('stack_name', sa.String(128), sa.ForeignKey('cloudformation_stacks.stack_name', ondelete='CASCADE'), nullable=False),
        sa.Column('logical_resource_id', sa.String(255), nullable=False),
        sa.Column('physical_resource_id', sa.String(255), nullable=True),
        
        # Resource type
        sa.Column('resource_type', sa.String(255), nullable=False),
        
        # Resource status
        sa.Column('resource_status', sa.String(50), nullable=False),
        sa.Column('resource_status_reason', sa.Text, nullable=True),
        
        # Resource properties
        sa.Column('resource_properties', sa.Text, nullable=True),
        
        # Metadata
        sa.Column('timestamp', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('last_updated_timestamp', sa.DateTime, nullable=True),
        
        # Drift detection
        sa.Column('drift_status', sa.String(50), nullable=True),
        
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4'
    )
    
    # Create indexes
    op.create_index('ix_cfn_stack_resources_stack', 'cloudformation_stack_resources', ['stack_name'])
    op.create_index('ix_cfn_stack_resources_logical_id', 'cloudformation_stack_resources', ['logical_resource_id'])
    op.create_index('ix_cfn_stack_resources_status', 'cloudformation_stack_resources', ['resource_status'])


def downgrade() -> None:
    """Drop CloudFormation tables."""
    op.drop_index('ix_cfn_stack_resources_status', 'cloudformation_stack_resources')
    op.drop_index('ix_cfn_stack_resources_logical_id', 'cloudformation_stack_resources')
    op.drop_index('ix_cfn_stack_resources_stack', 'cloudformation_stack_resources')
    op.drop_table('cloudformation_stack_resources')
    
    op.drop_index('ix_cfn_stacks_status', 'cloudformation_stacks')
    op.drop_index('ix_cfn_stacks_account', 'cloudformation_stacks')
    op.drop_table('cloudformation_stacks')
