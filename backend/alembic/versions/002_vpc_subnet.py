"""
Add VPC and Subnet tables

Revision ID: 002_vpc_subnet
Revises: 001_iam_schema
Create Date: 2026-01-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = '002_vpc_subnet'
down_revision = '001_iam_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create VPC and Subnet tables"""
    
    # Create VPCs table
    op.create_table(
        'vpcs',
        sa.Column('vpc_id', sa.String(21), primary_key=True),
        sa.Column('account_id', sa.String(12), sa.ForeignKey('accounts.account_id', ondelete='CASCADE'), nullable=False),
        sa.Column('cidr_block', sa.String(18), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('state', sa.String(20), nullable=False, server_default='available'),
        sa.Column('is_default', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('enable_dns_support', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('enable_dns_hostnames', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('docker_network_id', sa.String(64), nullable=True),
        sa.Column('docker_network_name', sa.String(255), nullable=True),
        sa.Column('tags', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now())
    )
    
    # Create indexes for VPCs
    op.create_index('idx_vpc_account_id', 'vpcs', ['account_id'])
    op.create_index('idx_vpc_cidr_block', 'vpcs', ['cidr_block'])
    op.create_index('idx_vpc_state', 'vpcs', ['state'])
    
    # Create Subnets table
    op.create_table(
        'subnets',
        sa.Column('subnet_id', sa.String(24), primary_key=True),
        sa.Column('vpc_id', sa.String(21), sa.ForeignKey('vpcs.vpc_id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_id', sa.String(12), sa.ForeignKey('accounts.account_id', ondelete='CASCADE'), nullable=False),
        sa.Column('cidr_block', sa.String(18), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('state', sa.String(20), nullable=False, server_default='available'),
        sa.Column('availability_zone', sa.String(20), nullable=False, server_default='us-east-1a'),
        sa.Column('available_ip_address_count', sa.Integer, nullable=False),
        sa.Column('map_public_ip_on_launch', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('tags', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now())
    )
    
    # Create indexes for Subnets
    op.create_index('idx_subnet_vpc_id', 'subnets', ['vpc_id'])
    op.create_index('idx_subnet_account_id', 'subnets', ['account_id'])
    op.create_index('idx_subnet_cidr_block', 'subnets', ['cidr_block'])
    op.create_index('idx_subnet_state', 'subnets', ['state'])


def downgrade() -> None:
    """Drop VPC and Subnet tables"""
    
    # Drop indexes first
    op.drop_index('idx_subnet_state', 'subnets')
    op.drop_index('idx_subnet_cidr_block', 'subnets')
    op.drop_index('idx_subnet_account_id', 'subnets')
    op.drop_index('idx_subnet_vpc_id', 'subnets')
    
    op.drop_index('idx_vpc_state', 'vpcs')
    op.drop_index('idx_vpc_cidr_block', 'vpcs')
    op.drop_index('idx_vpc_account_id', 'vpcs')
    
    # Drop tables
    op.drop_table('subnets')
    op.drop_table('vpcs')
