"""
Database migration: Security Groups

Creates security_groups and security_group_rules tables.

Revision ID: 003_security_groups
Revises: 002_vpc_subnet
Create Date: 2026-01-31
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_security_groups'
down_revision = '002_vpc_subnet'
branch_labels = None
depends_on = None


def upgrade():
    # Create security_groups table
    op.create_table(
        'security_groups',
        sa.Column('group_id', sa.String(24), primary_key=True),
        sa.Column('vpc_id', sa.String(21), sa.ForeignKey('vpcs.vpc_id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_id', sa.String(12), sa.ForeignKey('accounts.account_id', ondelete='CASCADE'), nullable=False),
        sa.Column('group_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_default', sa.Boolean, server_default='false', nullable=False),
        sa.Column('tags', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    
    # Create indexes for security_groups
    op.create_index('idx_sg_vpc_id', 'security_groups', ['vpc_id'])
    op.create_index('idx_sg_account_id', 'security_groups', ['account_id'])
    op.create_index('idx_sg_group_name', 'security_groups', ['group_name'])
    
    # Create security_group_rules table
    op.create_table(
        'security_group_rules',
        sa.Column('rule_id', sa.String(32), primary_key=True),
        sa.Column('group_id', sa.String(24), sa.ForeignKey('security_groups.group_id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_type', sa.String(10), nullable=False),  # 'ingress' or 'egress'
        sa.Column('ip_protocol', sa.String(10), nullable=False),  # 'tcp', 'udp', 'icmp', '-1'
        sa.Column('from_port', sa.Integer, nullable=True),
        sa.Column('to_port', sa.Integer, nullable=True),
        sa.Column('cidr_ipv4', sa.String(18), nullable=True),
        sa.Column('source_security_group_id', sa.String(24), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    
    # Create indexes for security_group_rules
    op.create_index('idx_sgr_group_id', 'security_group_rules', ['group_id'])
    op.create_index('idx_sgr_rule_type', 'security_group_rules', ['rule_type'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_sgr_rule_type', 'security_group_rules')
    op.drop_index('idx_sgr_group_id', 'security_group_rules')
    op.drop_index('idx_sg_group_name', 'security_groups')
    op.drop_index('idx_sg_account_id', 'security_groups')
    op.drop_index('idx_sg_vpc_id', 'security_groups')
    
    # Drop tables
    op.drop_table('security_group_rules')
    op.drop_table('security_groups')
