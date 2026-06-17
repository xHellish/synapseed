"""create_lmrs_table

Revision ID: 5e5dc56e6153
Revises: 002_add_auth_user_id
Create Date: 2026-06-16 20:54:06.752045+00:00

En DB local (docker-compose), la tabla lmrs y los índices ya existen porque
001_initial_schema los crea. Esta migración es idempotente para ambos casos.
En Supabase, aplica los cambios normalmente.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "5e5dc56e6153"
down_revision: Union[str, None] = "002_add_auth_user_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    return inspect(op.get_bind()).has_table(name)


def _index_exists(index_name: str, table_name: str) -> bool:
    indexes = inspect(op.get_bind()).get_indexes(table_name)
    return any(i["name"] == index_name for i in indexes)


def upgrade() -> None:
    if not _table_exists("lmrs"):
        op.create_table(
            "lmrs",
            sa.Column("plaguicida", sa.String(length=255), nullable=False),
            sa.Column("clase",      sa.String(length=255), nullable=True),
            sa.Column("cultivo",    sa.String(length=500), nullable=False),
            sa.Column("lmr_nac",   sa.String(length=100), nullable=True),
            sa.Column("id",         sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_lmrs_cultivo"),    "lmrs", ["cultivo"],    unique=False)
        op.create_index(op.f("ix_lmrs_plaguicida"), "lmrs", ["plaguicida"], unique=False)

    # Borra el unique constraint si existe (en Supabase fue creado por 002; en local no existe).
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS uq_users_auth_user_id")


def downgrade() -> None:
    op.create_unique_constraint("uq_users_auth_user_id", "users", ["auth_user_id"])
    if _table_exists("lmrs"):
        op.drop_index(op.f("ix_lmrs_plaguicida"), table_name="lmrs")
        op.drop_index(op.f("ix_lmrs_cultivo"),    table_name="lmrs")
        op.drop_table("lmrs")
