"""Initial IAM schema

Revision ID: 001_iam_schema
Revises: 
Create Date: 2026-01-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_iam_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create IAM tables"""
    
    # Create accounts table
    op.create_table(
        "accounts",
        sa.Column("account_id", sa.String(12), primary_key=True, comment="12-digit AWS account ID"),
        sa.Column("account_name", sa.String(128), nullable=False, comment="Friendly account name"),
        sa.Column("email", sa.String(255), nullable=False, unique=True, comment="Root account email"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", comment="Account status: active, suspended, closed"),
        sa.Column("arn", sa.String(255), nullable=False, unique=True, comment="Account ARN: arn:aws:iam::123456789012:root"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), comment="Timestamp when record was created"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now(), comment="Timestamp when record was last updated"),
    )
    op.create_index("ix_accounts_email", "accounts", ["email"])
    
    # Create users table
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(50), primary_key=True, comment="Unique user ID"),
        sa.Column("account_id", sa.String(12), sa.ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False, index=True, comment="Account this user belongs to"),
        sa.Column("username", sa.String(64), nullable=False, index=True, comment="IAM username (unique within account)"),
        sa.Column("arn", sa.String(255), nullable=False, unique=True, index=True, comment="User ARN: arn:aws:iam::123456789012:user/alice"),
        sa.Column("path", sa.String(512), nullable=False, server_default="/", comment="Path prefix for organizational structure"),
        sa.Column("password_hash", sa.String(255), nullable=True, comment="Bcrypt password hash (null if password auth disabled)"),
        sa.Column("password_last_changed", sa.DateTime(timezone=True), nullable=True, comment="When password was last changed"),
        sa.Column("require_password_reset", sa.Boolean, nullable=False, server_default="false", comment="Force password reset on next login"),
        sa.Column("console_access_enabled", sa.Boolean, nullable=False, server_default="true", comment="Whether user can log into web console"),
        sa.Column("mfa_enabled", sa.Boolean, nullable=False, server_default="false", comment="Whether MFA is enabled"),
        sa.Column("mfa_secret", sa.String(255), nullable=True, comment="TOTP secret for MFA (encrypted)"),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True, comment="Last successful login timestamp"),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=True, comment="Last API/console activity"),
        sa.Column("inline_policy", sa.Text, nullable=True, comment="Inline IAM policy JSON (optional)"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true", comment="Whether user is active"),
        sa.Column("tags", sa.Text, nullable=True, comment="User tags as JSON"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), comment="Timestamp when record was created"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now(), comment="Timestamp when record was last updated"),
    )
    op.create_index("ix_users_account_id", "users", ["account_id"])
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_arn", "users", ["arn"])
    
    # Create groups table
    op.create_table(
        "groups",
        sa.Column("group_id", sa.String(50), primary_key=True, comment="Unique group ID"),
        sa.Column("account_id", sa.String(12), sa.ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False, index=True, comment="Account this group belongs to"),
        sa.Column("group_name", sa.String(128), nullable=False, index=True, comment="IAM group name (unique within account)"),
        sa.Column("arn", sa.String(255), nullable=False, unique=True, index=True, comment="Group ARN: arn:aws:iam::123456789012:group/Developers"),
        sa.Column("path", sa.String(512), nullable=False, server_default="/", comment="Path prefix for organizational structure"),
        sa.Column("inline_policy", sa.Text, nullable=True, comment="Inline IAM policy JSON (optional)"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), comment="Timestamp when record was created"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now(), comment="Timestamp when record was last updated"),
    )
    op.create_index("ix_groups_account_id", "groups", ["account_id"])
    op.create_index("ix_groups_group_name", "groups", ["group_name"])
    op.create_index("ix_groups_arn", "groups", ["arn"])
    
    # Create roles table
    op.create_table(
        "roles",
        sa.Column("role_id", sa.String(50), primary_key=True, comment="Unique role ID"),
        sa.Column("account_id", sa.String(12), sa.ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False, index=True, comment="Account this role belongs to"),
        sa.Column("role_name", sa.String(64), nullable=False, index=True, comment="IAM role name (unique within account)"),
        sa.Column("arn", sa.String(255), nullable=False, unique=True, index=True, comment="Role ARN: arn:aws:iam::123456789012:role/EC2InstanceRole"),
        sa.Column("path", sa.String(512), nullable=False, server_default="/", comment="Path prefix for organizational structure"),
        sa.Column("description", sa.Text, nullable=True, comment="Role description"),
        sa.Column("assume_role_policy", sa.Text, nullable=False, comment="Trust policy JSON defining who can assume this role"),
        sa.Column("inline_policy", sa.Text, nullable=True, comment="Inline IAM policy JSON (optional)"),
        sa.Column("max_session_duration", sa.Integer, nullable=False, server_default="3600", comment="Maximum session duration in seconds (default 1 hour)"),
        sa.Column("tags", sa.Text, nullable=True, comment="Role tags as JSON"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), comment="Timestamp when record was created"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now(), comment="Timestamp when record was last updated"),
    )
    op.create_index("ix_roles_account_id", "roles", ["account_id"])
    op.create_index("ix_roles_role_name", "roles", ["role_name"])
    op.create_index("ix_roles_arn", "roles", ["arn"])
    
    # Create policies table
    op.create_table(
        "policies",
        sa.Column("policy_id", sa.String(50), primary_key=True, comment="Unique policy ID"),
        sa.Column("account_id", sa.String(12), sa.ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=True, index=True, comment="Account this policy belongs to (null for AWS-managed)"),
        sa.Column("policy_name", sa.String(128), nullable=False, index=True, comment="IAM policy name"),
        sa.Column("arn", sa.String(255), nullable=False, unique=True, index=True, comment="Policy ARN"),
        sa.Column("path", sa.String(512), nullable=False, server_default="/", comment="Path prefix for organizational structure"),
        sa.Column("description", sa.Text, nullable=True, comment="Policy description"),
        sa.Column("policy_document", sa.Text, nullable=False, comment="IAM policy JSON document with Version and Statement"),
        sa.Column("is_aws_managed", sa.Boolean, nullable=False, server_default="false", comment="Whether this is an AWS-managed policy"),
        sa.Column("version_id", sa.String(50), nullable=False, server_default="v1", comment="Policy version identifier"),
        sa.Column("is_default_version", sa.Boolean, nullable=False, server_default="true", comment="Whether this is the default (active) version"),
        sa.Column("attachment_count", sa.Integer, nullable=False, server_default="0", comment="Number of entities this policy is attached to"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), comment="Timestamp when record was created"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now(), comment="Timestamp when record was last updated"),
    )
    op.create_index("ix_policies_account_id", "policies", ["account_id"])
    op.create_index("ix_policies_policy_name", "policies", ["policy_name"])
    op.create_index("ix_policies_arn", "policies", ["arn"])
    
    # Create access_keys table
    op.create_table(
        "access_keys",
        sa.Column("access_key_id", sa.String(20), primary_key=True, comment="Access Key ID: AKIAIOSFODNN7EXAMPLE"),
        sa.Column("user_id", sa.String(50), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True, comment="User this access key belongs to"),
        sa.Column("secret_access_key_hash", sa.String(255), nullable=False, comment="Bcrypt hash of secret access key"),
        sa.Column("status", sa.String(20), nullable=False, server_default="Active", comment="Status: Active or Inactive"),
        sa.Column("last_used", sa.DateTime(timezone=True), nullable=True, comment="Last time this key was used"),
        sa.Column("last_used_service", sa.String(100), nullable=True, comment="Last AWS service accessed with this key"),
        sa.Column("last_used_region", sa.String(50), nullable=True, comment="Last region accessed with this key"),
        sa.Column("last_rotated", sa.DateTime(timezone=True), nullable=True, comment="Last time this key was rotated"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), comment="Timestamp when record was created"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now(), comment="Timestamp when record was last updated"),
    )
    op.create_index("ix_access_keys_user_id", "access_keys", ["user_id"])
    
    # Create association tables (many-to-many relationships)
    
    # User ↔ Group
    op.create_table(
        "user_groups",
        sa.Column("user_id", sa.String, sa.ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("group_id", sa.String, sa.ForeignKey("groups.group_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # User ↔ Policy
    op.create_table(
        "user_policies",
        sa.Column("user_id", sa.String, sa.ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("policy_id", sa.String, sa.ForeignKey("policies.policy_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("attached_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Group ↔ Policy
    op.create_table(
        "group_policies",
        sa.Column("group_id", sa.String, sa.ForeignKey("groups.group_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("policy_id", sa.String, sa.ForeignKey("policies.policy_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("attached_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Role ↔ Policy
    op.create_table(
        "role_policies",
        sa.Column("role_id", sa.String, sa.ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("policy_id", sa.String, sa.ForeignKey("policies.policy_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("attached_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop IAM tables"""
    
    # Drop association tables first (foreign key constraints)
    op.drop_table("role_policies")
    op.drop_table("group_policies")
    op.drop_table("user_policies")
    op.drop_table("user_groups")
    
    # Drop main tables
    op.drop_table("access_keys")
    op.drop_table("policies")
    op.drop_table("roles")
    op.drop_table("groups")
    op.drop_table("users")
    op.drop_table("accounts")
