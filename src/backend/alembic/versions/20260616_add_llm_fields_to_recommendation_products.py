"""add_llm_fields_to_recommendation_products

Revision ID: a1b2c3d4e5f6
Revises: 5e5dc56e6153
Create Date: 2026-06-16 22:00:00.000000

Agrega ventajas, riesgos y recomendacion_uso_general a recommendation_products.
Estos campos almacenan el contenido interpretativo generado por el LLM sintetizador.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "a1b2c3d4e5f6"
down_revision = "5e5dc56e6153"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = [c["name"] for c in inspector.get_columns(table)]
    return column in cols


def upgrade() -> None:
    for col_name in ("ventajas", "riesgos", "recomendacion_uso_general"):
        if not _column_exists("recommendation_products", col_name):
            op.add_column(
                "recommendation_products",
                sa.Column(col_name, sa.Text(), nullable=True),
            )


def downgrade() -> None:
    for col_name in ("recomendacion_uso_general", "riesgos", "ventajas"):
        op.drop_column("recommendation_products", col_name)
