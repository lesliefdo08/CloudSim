"""005_amis

Create AMIs table for custom machine images.

Revision ID: 005_amis
Revises: 004_instances
Create Date: 2024-01-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = '005_amis'
down_revision = '004_instances'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create AMIs table"""
    
    # Create amis table
    op.create_table(
        'amis',
        sa.Column('ami_id', sa.String(length=21), nullable=False, primary_key=True),
        sa.Column('account_id', sa.String(length=12), sa.ForeignKey('accounts.account_id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_instance_id', sa.String(length=19), nullable=True),
        sa.Column('docker_image_id', sa.String(length=255), nullable=True),
        sa.Column('docker_image_tag', sa.String(length=255), nullable=True),
        sa.Column('state', sa.String(length=20), nullable=False, server_default='available'),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes
    op.create_index('idx_ami_account_id', 'amis', ['account_id'])
    op.create_index('idx_ami_state', 'amis', ['state'])
    op.create_index('idx_ami_name', 'amis', ['name'])


def downgrade() -> None:
    """Drop AMIs table"""
    
    # Drop indexes
    op.drop_index('idx_ami_name', table_name='amis')
    op.drop_index('idx_ami_state', table_name='amis')
    op.drop_index('idx_ami_account_id', table_name='amis')
    
    # Drop table
    op.drop_table('amis')
