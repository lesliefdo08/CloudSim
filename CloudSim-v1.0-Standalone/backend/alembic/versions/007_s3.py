"""
S3 Buckets and Objects Migration

Creates tables for S3 storage simulation with filesystem backing.

Revision ID: 007_s3
Revises: 006_volumes
Create Date: 2026-01-31
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '007_s3'
down_revision = '006_volumes'
branch_labels = None
depends_on = None


def upgrade():
    """Create S3 buckets and objects tables."""
    
    # Create buckets table
    op.create_table(
        'buckets',
        sa.Column('bucket_name', sa.String(length=63), primary_key=True, comment='Unique bucket name'),
        sa.Column('account_id', sa.String(length=12), nullable=False, comment='Owner account ID'),
        sa.Column('region', sa.String(length=32), nullable=False, server_default='us-east-1', comment='AWS region'),
        sa.Column('versioning_enabled', sa.Boolean(), nullable=False, server_default='false', comment='Versioning enabled'),
        sa.Column('public_access_blocked', sa.Boolean(), nullable=False, server_default='true', comment='Block public access'),
        sa.Column('filesystem_path', sa.String(length=500), nullable=False, comment='Bucket directory path'),
        sa.Column('tags', sa.Text(), nullable=True, comment='JSON tags'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='Creation timestamp'),
        sa.ForeignKeyConstraint(['account_id'], ['iam_accounts.account_id'], ondelete='CASCADE'),
    )
    
    # Create indexes for buckets
    op.create_index('idx_bucket_account_id', 'buckets', ['account_id'])
    
    # Create s3_objects table
    op.create_table(
        's3_objects',
        sa.Column('object_id', sa.String(length=22), primary_key=True, comment='Unique object ID'),
        sa.Column('bucket_name', sa.String(length=63), nullable=False, comment='Parent bucket'),
        sa.Column('account_id', sa.String(length=12), nullable=False, comment='Owner account ID'),
        sa.Column('object_key', sa.String(length=1024), nullable=False, comment='Object key/path'),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False, comment='Object size'),
        sa.Column('content_type', sa.String(length=255), nullable=False, server_default='application/octet-stream', comment='MIME type'),
        sa.Column('etag', sa.String(length=64), nullable=False, comment='Entity tag (MD5)'),
        sa.Column('filesystem_path', sa.String(length=1500), nullable=False, comment='Object file path'),
        sa.Column('storage_class', sa.String(length=32), nullable=False, server_default='STANDARD', comment='Storage class'),
        sa.Column('version_id', sa.String(length=64), nullable=True, comment='Version ID'),
        sa.Column('metadata', sa.Text(), nullable=True, comment='JSON metadata'),
        sa.Column('tags', sa.Text(), nullable=True, comment='JSON tags'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='Upload timestamp'),
        sa.Column('last_modified', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='Last modified'),
        sa.ForeignKeyConstraint(['account_id'], ['iam_accounts.account_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bucket_name'], ['buckets.bucket_name'], ondelete='CASCADE'),
    )
    
    # Create indexes for s3_objects
    op.create_index('idx_s3_object_bucket_name', 's3_objects', ['bucket_name'])
    op.create_index('idx_s3_object_account_id', 's3_objects', ['account_id'])
    op.create_index('idx_s3_object_key', 's3_objects', ['object_key'])
    op.create_index('idx_s3_object_bucket_key', 's3_objects', ['bucket_name', 'object_key'], unique=True)


def downgrade():
    """Drop S3 tables."""
    
    # Drop indexes
    op.drop_index('idx_s3_object_bucket_key', 's3_objects')
    op.drop_index('idx_s3_object_key', 's3_objects')
    op.drop_index('idx_s3_object_account_id', 's3_objects')
    op.drop_index('idx_s3_object_bucket_name', 's3_objects')
    op.drop_index('idx_bucket_account_id', 'buckets')
    
    # Drop tables
    op.drop_table('s3_objects')
    op.drop_table('buckets')
