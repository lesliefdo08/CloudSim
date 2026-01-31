"""RDS database instances and snapshots tables

Revision ID: 011_rds
Revises: 010_cloudwatch_logs_alarms
Create Date: 2024-01-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '011_rds'
down_revision = '010_cloudwatch_logs_alarms'
branch_labels = None
depends_on = None


def upgrade():
    """Create RDS tables."""
    
    # ==================== DB Instances ====================
    op.create_table(
        'db_instances',
        sa.Column('db_instance_identifier', sa.String(63), primary_key=True),
        sa.Column('db_instance_arn', sa.String(255), unique=True, nullable=False),
        sa.Column('account_id', sa.String(12), nullable=False),
        
        # Engine configuration
        sa.Column('engine', sa.String(50), nullable=False),
        sa.Column('engine_version', sa.String(50), nullable=False),
        sa.Column('db_instance_class', sa.String(50), nullable=False),
        
        # Database configuration
        sa.Column('master_username', sa.String(63), nullable=False),
        sa.Column('master_user_password', sa.String(255), nullable=False),
        sa.Column('db_name', sa.String(64), nullable=True),
        sa.Column('port', sa.Integer, nullable=False),
        
        # Storage
        sa.Column('allocated_storage', sa.Integer, nullable=False),
        sa.Column('storage_type', sa.String(50), nullable=False, server_default='gp2'),
        sa.Column('storage_encrypted', sa.Boolean, nullable=False, server_default='0'),
        
        # Networking
        sa.Column('vpc_id', sa.String(21), nullable=True),
        sa.Column('subnet_group', sa.String(255), nullable=True),
        sa.Column('publicly_accessible', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('endpoint_address', sa.String(255), nullable=True),
        sa.Column('endpoint_port', sa.Integer, nullable=True),
        
        # Backup configuration
        sa.Column('backup_retention_period', sa.Integer, nullable=False, server_default='7'),
        sa.Column('preferred_backup_window', sa.String(50), nullable=True),
        sa.Column('preferred_maintenance_window', sa.String(50), nullable=True),
        
        # State
        sa.Column('db_instance_status', sa.String(50), nullable=False, server_default='creating'),
        
        # Container information
        sa.Column('container_id', sa.String(64), nullable=True),
        sa.Column('container_name', sa.String(255), nullable=True),
        
        # Metadata
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deletion_protection', sa.Boolean, nullable=False, server_default='0'),
        
        # Multi-AZ
        sa.Column('multi_az', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('availability_zone', sa.String(50), nullable=True),
        
        # Monitoring
        sa.Column('enhanced_monitoring_arn', sa.String(255), nullable=True),
        sa.Column('performance_insights_enabled', sa.Boolean, nullable=False, server_default='0'),
        
        # Tags
        sa.Column('tags', sa.Text, nullable=True),
        
        sa.ForeignKeyConstraint(
            ['account_id'],
            ['iam_accounts.account_id'],
            name='fk_db_instances_account',
            ondelete='CASCADE'
        )
    )
    
    # Create indexes for db_instances
    op.create_index(
        'ix_db_instances_account',
        'db_instances',
        ['account_id']
    )
    
    op.create_index(
        'ix_db_instances_status',
        'db_instances',
        ['db_instance_status']
    )
    
    op.create_index(
        'ix_db_instances_engine',
        'db_instances',
        ['engine']
    )
    
    # ==================== DB Snapshots ====================
    op.create_table(
        'db_snapshots',
        sa.Column('db_snapshot_identifier', sa.String(255), primary_key=True),
        sa.Column('db_snapshot_arn', sa.String(255), unique=True, nullable=False),
        sa.Column('account_id', sa.String(12), nullable=False),
        
        # Source instance
        sa.Column('db_instance_identifier', sa.String(63), nullable=False),
        
        # Engine information
        sa.Column('engine', sa.String(50), nullable=False),
        sa.Column('engine_version', sa.String(50), nullable=False),
        
        # Snapshot configuration
        sa.Column('snapshot_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='creating'),
        
        # Storage
        sa.Column('allocated_storage', sa.Integer, nullable=False),
        sa.Column('storage_type', sa.String(50), nullable=False),
        
        # Port
        sa.Column('port', sa.Integer, nullable=False),
        
        # Backup details
        sa.Column('master_username', sa.String(63), nullable=False),
        sa.Column('availability_zone', sa.String(50), nullable=True),
        sa.Column('vpc_id', sa.String(21), nullable=True),
        
        # Snapshot metadata
        sa.Column('snapshot_create_time', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('percent_progress', sa.Integer, nullable=False, server_default='0'),
        
        # Docker volume information
        sa.Column('volume_name', sa.String(255), nullable=True),
        
        # Tags
        sa.Column('tags', sa.Text, nullable=True),
        
        sa.ForeignKeyConstraint(
            ['account_id'],
            ['iam_accounts.account_id'],
            name='fk_db_snapshots_account',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['db_instance_identifier'],
            ['db_instances.db_instance_identifier'],
            name='fk_db_snapshots_instance',
            ondelete='CASCADE'
        )
    )
    
    # Create indexes for db_snapshots
    op.create_index(
        'ix_db_snapshots_account',
        'db_snapshots',
        ['account_id']
    )
    
    op.create_index(
        'ix_db_snapshots_instance',
        'db_snapshots',
        ['db_instance_identifier']
    )
    
    op.create_index(
        'ix_db_snapshots_type',
        'db_snapshots',
        ['snapshot_type']
    )


def downgrade():
    """Drop RDS tables."""
    
    # Drop db_snapshots
    op.drop_index('ix_db_snapshots_type', 'db_snapshots')
    op.drop_index('ix_db_snapshots_instance', 'db_snapshots')
    op.drop_index('ix_db_snapshots_account', 'db_snapshots')
    op.drop_table('db_snapshots')
    
    # Drop db_instances
    op.drop_index('ix_db_instances_engine', 'db_instances')
    op.drop_index('ix_db_instances_status', 'db_instances')
    op.drop_index('ix_db_instances_account', 'db_instances')
    op.drop_table('db_instances')
