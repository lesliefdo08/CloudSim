"""
Lambda Functions Migration
Creates lambda_functions table
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# Revision identifiers
revision = '012_lambda'
down_revision = '011_rds'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create lambda_functions table."""
    
    # lambda_functions table
    op.create_table(
        'lambda_functions',
        sa.Column('function_name', sa.String(64), primary_key=True, nullable=False),
        sa.Column('function_arn', sa.String(255), unique=True, nullable=False),
        sa.Column('account_id', sa.String(12), sa.ForeignKey('iam_accounts.account_id', ondelete='CASCADE'), nullable=False),
        
        # Runtime configuration
        sa.Column('runtime', sa.String(50), nullable=False),
        sa.Column('handler', sa.String(128), nullable=False),
        
        # Code storage
        sa.Column('code_storage_location', sa.String(255), nullable=False),
        sa.Column('code_sha256', sa.String(64), nullable=False),
        sa.Column('code_size', sa.Integer, nullable=False),
        
        # Function configuration
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('timeout', sa.Integer, nullable=False, default=3),
        sa.Column('memory_size', sa.Integer, nullable=False, default=128),
        
        # Environment
        sa.Column('environment_variables', sa.Text, nullable=True),
        
        # Execution role
        sa.Column('role', sa.String(255), nullable=False),
        
        # Networking
        sa.Column('vpc_config', sa.Text, nullable=True),
        
        # State
        sa.Column('state', sa.String(50), nullable=False, default='Active'),
        sa.Column('state_reason', sa.Text, nullable=True),
        sa.Column('state_reason_code', sa.String(50), nullable=True),
        
        # Last update
        sa.Column('last_modified', sa.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('last_update_status', sa.String(50), nullable=False, default='Successful'),
        
        # Versioning
        sa.Column('version', sa.String(10), nullable=False, default='$LATEST'),
        
        # Layers
        sa.Column('layers', sa.Text, nullable=True),
        
        # Container information
        sa.Column('container_image', sa.String(255), nullable=True),
        
        # Metrics
        sa.Column('invocations', sa.Integer, nullable=False, default=0),
        sa.Column('errors', sa.Integer, nullable=False, default=0),
        
        # Tags
        sa.Column('tags', sa.Text, nullable=True),
        
        # Metadata
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4'
    )
    
    # Create indexes
    op.create_index('ix_lambda_functions_account', 'lambda_functions', ['account_id'])
    op.create_index('ix_lambda_functions_runtime', 'lambda_functions', ['runtime'])
    op.create_index('ix_lambda_functions_state', 'lambda_functions', ['state'])


def downgrade() -> None:
    """Drop lambda_functions table."""
    op.drop_index('ix_lambda_functions_state', 'lambda_functions')
    op.drop_index('ix_lambda_functions_runtime', 'lambda_functions')
    op.drop_index('ix_lambda_functions_account', 'lambda_functions')
    op.drop_table('lambda_functions')
