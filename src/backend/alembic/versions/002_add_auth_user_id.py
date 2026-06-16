"""Add auth_user_id to users table if not exists

Revision ID: 002_add_auth_user_id
Revises: 001_initial_schema
Create Date: 2026-06-15 00:00:00.000000

This migration adds the auth_user_id UUID column to the users table.
The column links each local user profile to the Supabase Auth identity.
It uses a conditional check so it is idempotent (safe to run even if
the column already exists).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "002_add_auth_user_id"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    """Return True if the column already exists in the table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = [c["name"] for c in inspector.get_columns(table)]
    return column in cols


def upgrade() -> None:
    """Add auth_user_id column to users table (idempotent)."""
    if not _column_exists("users", "auth_user_id"):
        op.add_column(
            "users",
            sa.Column("auth_user_id", sa.UUID(), nullable=True),
        )
        op.create_unique_constraint(
            "uq_users_auth_user_id", "users", ["auth_user_id"]
        )
        op.create_index(
            "ix_users_auth_user_id", "users", ["auth_user_id"], unique=True
        )


def downgrade() -> None:
    """Remove auth_user_id column from users table."""
    op.drop_index("ix_users_auth_user_id", table_name="users")
    op.drop_constraint("uq_users_auth_user_id", "users", type_="unique")
    op.drop_column("users", "auth_user_id")
