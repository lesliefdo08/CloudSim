"""
Migration 008: Add S3 advanced features
- Add versioning support fields to s3_objects
- Add lifecycle_rules field to buckets
- Create bucket_policies table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '008_s3_advanced'
down_revision = '007_s3_storage'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration."""
    
    # ============================================
    # 1. Update s3_objects table for versioning
    # ============================================
    
    # Add version_id index
    op.create_index(
        'ix_s3_objects_version_id',
        's3_objects',
        ['version_id']
    )
    
    # Add is_latest column
    op.add_column(
        's3_objects',
        sa.Column('is_latest', sa.Boolean(), nullable=False, server_default='true')
    )
    
    # Add is_delete_marker column
    op.add_column(
        's3_objects',
        sa.Column('is_delete_marker', sa.Boolean(), nullable=False, server_default='false')
    )
    
    # ============================================
    # 2. Update buckets table for lifecycle
    # ============================================
    
    # Add lifecycle_rules column
    op.add_column(
        'buckets',
        sa.Column('lifecycle_rules', sa.Text(), nullable=True)
    )
    
    # ============================================
    # 3. Create bucket_policies table
    # ============================================
    
    op.create_table(
        'bucket_policies',
        sa.Column('policy_id', sa.String(22), primary_key=True, nullable=False),
        sa.Column('bucket_name', sa.String(63), nullable=False),
        sa.Column('account_id', sa.String(12), nullable=False),
        sa.Column('policy_document', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Add foreign key for bucket_name
    op.create_foreign_key(
        'fk_bucket_policies_bucket_name',
        'bucket_policies',
        'buckets',
        ['bucket_name'],
        ['bucket_name'],
        ondelete='CASCADE'
    )
    
    # Add foreign key for account_id
    op.create_foreign_key(
        'fk_bucket_policies_account_id',
        'bucket_policies',
        'iam_accounts',
        ['account_id'],
        ['account_id'],
        ondelete='CASCADE'
    )
    
    # Create unique index on bucket_name (one policy per bucket)
    op.create_index(
        'ix_bucket_policies_bucket_name',
        'bucket_policies',
        ['bucket_name'],
        unique=True
    )
    
    # Create index on account_id for faster lookups
    op.create_index(
        'ix_bucket_policies_account_id',
        'bucket_policies',
        ['account_id']
    )


def downgrade() -> None:
    """Revert migration."""
    
    # ============================================
    # 3. Drop bucket_policies table
    # ============================================
    
    op.drop_index('ix_bucket_policies_account_id', 'bucket_policies')
    op.drop_index('ix_bucket_policies_bucket_name', 'bucket_policies')
    op.drop_constraint('fk_bucket_policies_account_id', 'bucket_policies', type_='foreignkey')
    op.drop_constraint('fk_bucket_policies_bucket_name', 'bucket_policies', type_='foreignkey')
    op.drop_table('bucket_policies')
    
    # ============================================
    # 2. Revert buckets table changes
    # ============================================
    
    op.drop_column('buckets', 'lifecycle_rules')
    
    # ============================================
    # 1. Revert s3_objects table changes
    # ============================================
    
    op.drop_column('s3_objects', 'is_delete_marker')
    op.drop_column('s3_objects', 'is_latest')
    op.drop_index('ix_s3_objects_version_id', 's3_objects')
