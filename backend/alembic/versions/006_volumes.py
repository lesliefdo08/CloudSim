"""006_volumes

Create volumes and snapshots tables for EBS storage.

Revision ID: 006_volumes
Revises: 005_amis
Create Date: 2024-01-05
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '006_volumes'
down_revision = '005_amis'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create volumes and snapshots tables"""
    
    # Create volumes table
    op.create_table(
        'volumes',
        sa.Column('volume_id', sa.String(length=21), nullable=False, primary_key=True),
        sa.Column('account_id', sa.String(length=12), sa.ForeignKey('accounts.account_id', ondelete='CASCADE'), nullable=False),
        sa.Column('size_gb', sa.Integer(), nullable=False),
        sa.Column('volume_type', sa.String(length=10), nullable=False, server_default='gp2'),
        sa.Column('state', sa.String(length=20), nullable=False, server_default='available'),
        sa.Column('attached_instance_id', sa.String(length=19), nullable=True),
        sa.Column('device_name', sa.String(length=32), nullable=True),
        sa.Column('availability_zone', sa.String(length=32), nullable=False),
        sa.Column('docker_volume_name', sa.String(length=255), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes for volumes
    op.create_index('idx_volume_account_id', 'volumes', ['account_id'])
    op.create_index('idx_volume_state', 'volumes', ['state'])
    op.create_index('idx_volume_attached_instance', 'volumes', ['attached_instance_id'])
    
    # Create snapshots table
    op.create_table(
        'snapshots',
        sa.Column('snapshot_id', sa.String(length=22), nullable=False, primary_key=True),
        sa.Column('account_id', sa.String(length=12), sa.ForeignKey('accounts.account_id', ondelete='CASCADE'), nullable=False),
        sa.Column('volume_id', sa.String(length=21), nullable=False),
        sa.Column('size_gb', sa.Integer(), nullable=False),
        sa.Column('state', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('docker_volume_backup', sa.String(length=255), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes for snapshots
    op.create_index('idx_snapshot_account_id', 'snapshots', ['account_id'])
    op.create_index('idx_snapshot_volume_id', 'snapshots', ['volume_id'])
    op.create_index('idx_snapshot_state', 'snapshots', ['state'])


def downgrade() -> None:
    """Drop volumes and snapshots tables"""
    
    # Drop indexes for snapshots
    op.drop_index('idx_snapshot_state', table_name='snapshots')
    op.drop_index('idx_snapshot_volume_id', table_name='snapshots')
    op.drop_index('idx_snapshot_account_id', table_name='snapshots')
    
    # Drop snapshots table
    op.drop_table('snapshots')
    
    # Drop indexes for volumes
    op.drop_index('idx_volume_attached_instance', table_name='volumes')
    op.drop_index('idx_volume_state', table_name='volumes')
    op.drop_index('idx_volume_account_id', table_name='volumes')
    
    # Drop volumes table
    op.drop_table('volumes')
