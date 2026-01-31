"""
Migration 009: Add CloudWatch metrics
- Create cloudwatch_metrics table
- Add composite indexes for efficient time-series queries
"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = '009_cloudwatch_metrics'
down_revision = '008_s3_advanced'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration."""
    
    # ============================================
    # Create cloudwatch_metrics table
    # ============================================
    
    op.create_table(
        'cloudwatch_metrics',
        sa.Column('metric_id', sa.String(30), primary_key=True, nullable=False),
        sa.Column('namespace', sa.String(255), nullable=False),
        sa.Column('metric_name', sa.String(255), nullable=False),
        sa.Column('dimensions', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('account_id', sa.String(12), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    
    # Add foreign key for account_id
    op.create_foreign_key(
        'fk_cloudwatch_metrics_account_id',
        'cloudwatch_metrics',
        'iam_accounts',
        ['account_id'],
        ['account_id'],
        ondelete='CASCADE'
    )
    
    # Create indexes for efficient queries
    
    # Index for namespace filtering
    op.create_index(
        'ix_cloudwatch_metrics_namespace',
        'cloudwatch_metrics',
        ['namespace']
    )
    
    # Index for metric name filtering
    op.create_index(
        'ix_cloudwatch_metrics_metric_name',
        'cloudwatch_metrics',
        ['metric_name']
    )
    
    # Index for timestamp range queries
    op.create_index(
        'ix_cloudwatch_metrics_timestamp',
        'cloudwatch_metrics',
        ['timestamp']
    )
    
    # Index for account filtering
    op.create_index(
        'ix_cloudwatch_metrics_account_id',
        'cloudwatch_metrics',
        ['account_id']
    )
    
    # Composite index for namespace + metric name (common filter)
    op.create_index(
        'ix_cloudwatch_metrics_namespace_name',
        'cloudwatch_metrics',
        ['namespace', 'metric_name']
    )
    
    # Composite index for namespace + metric name + timestamp (time-series queries)
    op.create_index(
        'ix_cloudwatch_metrics_namespace_name_time',
        'cloudwatch_metrics',
        ['namespace', 'metric_name', 'timestamp']
    )
    
    # Composite index for account + namespace (account-specific queries)
    op.create_index(
        'ix_cloudwatch_metrics_account_namespace',
        'cloudwatch_metrics',
        ['account_id', 'namespace']
    )


def downgrade() -> None:
    """Revert migration."""
    
    # Drop indexes
    op.drop_index('ix_cloudwatch_metrics_account_namespace', 'cloudwatch_metrics')
    op.drop_index('ix_cloudwatch_metrics_namespace_name_time', 'cloudwatch_metrics')
    op.drop_index('ix_cloudwatch_metrics_namespace_name', 'cloudwatch_metrics')
    op.drop_index('ix_cloudwatch_metrics_account_id', 'cloudwatch_metrics')
    op.drop_index('ix_cloudwatch_metrics_timestamp', 'cloudwatch_metrics')
    op.drop_index('ix_cloudwatch_metrics_metric_name', 'cloudwatch_metrics')
    op.drop_index('ix_cloudwatch_metrics_namespace', 'cloudwatch_metrics')
    
    # Drop foreign key
    op.drop_constraint('fk_cloudwatch_metrics_account_id', 'cloudwatch_metrics', type_='foreignkey')
    
    # Drop table
    op.drop_table('cloudwatch_metrics')
