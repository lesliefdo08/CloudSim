"""
Database migration: EC2 Instances

Creates instances table.

Revision ID: 004_instances
Revises: 003_security_groups
Create Date: 2026-01-31
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_instances'
down_revision = '003_security_groups'
branch_labels = None
depends_on = None


def upgrade():
    # Create instances table
    op.create_table(
        'instances',
        sa.Column('instance_id', sa.String(19), primary_key=True),
        sa.Column('subnet_id', sa.String(24), sa.ForeignKey('subnets.subnet_id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_id', sa.String(12), sa.ForeignKey('accounts.account_id', ondelete='CASCADE'), nullable=False),
        sa.Column('instance_type', sa.String(20), nullable=False),
        sa.Column('image_id', sa.String(100), nullable=False),
        sa.Column('state', sa.String(20), nullable=False),
        sa.Column('state_reason', sa.Text, nullable=True),
        sa.Column('private_ip_address', sa.String(15), nullable=True),
        sa.Column('public_ip_address', sa.String(15), nullable=True),
        sa.Column('security_group_ids', sa.Text, nullable=True),
        sa.Column('docker_container_id', sa.String(64), nullable=True),
        sa.Column('docker_container_name', sa.String(255), nullable=True),
        sa.Column('key_name', sa.String(255), nullable=True),
        sa.Column('user_data', sa.Text, nullable=True),
        sa.Column('tags', sa.Text, nullable=True),
        sa.Column('launch_time', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    
    # Create indexes for instances
    op.create_index('idx_instance_account_id', 'instances', ['account_id'])
    op.create_index('idx_instance_subnet_id', 'instances', ['subnet_id'])
    op.create_index('idx_instance_state', 'instances', ['state'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_instance_state', 'instances')
    op.drop_index('idx_instance_subnet_id', 'instances')
    op.drop_index('idx_instance_account_id', 'instances')
    
    # Drop table
    op.drop_table('instances')
