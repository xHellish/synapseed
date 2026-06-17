"""Initial schema — complete current schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-06-13 12:00:00.000000

Crea todas las tablas del schema actual desde cero.
En Supabase (DB existente), Alembic lo omite porque ya está aplicado.
En PostgreSQL local (docker-compose), crea el schema completo.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# Helpers para enums PostgreSQL ya creados (create_type=False → no intenta CREATE TYPE)
_pc  = postgresql.ENUM("plaguicida", "fertilizante",                                                    name="product_category",      create_type=False)
_ps  = postgresql.ENUM("activo", "cancelado", "expirado", "suspendido",                                 name="product_status",         create_type=False)
_tb  = postgresql.ENUM("roja", "amarilla", "azul", "verde", "no_aplica",                                name="toxic_band",             create_type=False)
_rs  = postgresql.ENUM("pending", "processing", "completed", "failed",                                  name="recommendation_status",  create_type=False)
_aa  = postgresql.ENUM("create", "read", "update", "delete", "login",
                       "logout", "recommendation_request", "recommendation_view",                        name="audit_action",           create_type=False)
_rt  = postgresql.ENUM("decreto", "ley", "resolucion", "lista_prohibida", "lmr", "otro",               name="regulationtype",         create_type=False)

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── Enums (checkfirst evita errores si ya existen) ────────────
    for name, values in [
        ("product_category",      ["plaguicida", "fertilizante"]),
        ("product_status",        ["activo", "cancelado", "expirado", "suspendido"]),
        ("toxic_band",            ["roja", "amarilla", "azul", "verde", "no_aplica"]),
        ("recommendation_status", ["pending", "processing", "completed", "failed"]),
        ("audit_action",          ["create", "read", "update", "delete", "login",
                                   "logout", "recommendation_request", "recommendation_view"]),
        ("regulationtype",        ["decreto", "ley", "resolucion", "lista_prohibida", "lmr", "otro"]),
    ]:
        postgresql.ENUM(*values, name=name, create_type=False).create(bind, checkfirst=True)

    # ── 1. users ──────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",             sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("auth_user_id",   sa.Uuid(),    nullable=True),
        sa.Column("email",          sa.String(255), nullable=False),
        sa.Column("password_hash",  sa.String(255), nullable=True),
        sa.Column("full_name",      sa.String(255), nullable=False),
        sa.Column("identification", sa.String(20),  nullable=False),
        sa.Column("phone",          sa.String(30),  nullable=True),
        sa.Column("is_active",      sa.Boolean(),   nullable=False, server_default="true"),
        sa.Column("is_verified",    sa.Boolean(),   nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("auth_user_id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("identification"),
    )
    op.create_index("ix_users_auth_user_id",   "users", ["auth_user_id"], unique=True)
    op.create_index("ix_users_email",          "users", ["email"])
    op.create_index("ix_users_identification", "users", ["identification"])
    op.create_index("ix_users_email_active",   "users", ["email", "is_active"])

    # ── 2. zones ──────────────────────────────────────────────────
    op.create_table(
        "zones",
        sa.Column("id",            sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id",       sa.Integer(), nullable=False),
        sa.Column("name",          sa.String(100), nullable=False),
        sa.Column("soil_type",     sa.String(50),  nullable=True),
        sa.Column("humidity",      sa.Numeric(5, 2), nullable=True),
        sa.Column("temperature",   sa.Numeric(5, 2), nullable=True),
        sa.Column("water_quality", sa.String(50),   nullable=True),
        sa.Column("latitude",      sa.Numeric(10, 8), nullable=True),
        sa.Column("longitude",     sa.Numeric(11, 8), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_zones_user_id",   "zones", ["user_id"])
    op.create_index("ix_zones_user_name", "zones", ["user_id", "name"])

    # ── 3. distributors ───────────────────────────────────────────
    op.create_table(
        "distributors",
        sa.Column("id",        sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre",    sa.String(255), nullable=False),
        sa.Column("correo",    sa.String(255), nullable=True),
        sa.Column("telefono",  sa.String(50),  nullable=True),
        sa.Column("ubicacion", sa.String(255), nullable=True),
        sa.Column("provincia", sa.String(50),  nullable=True),
        sa.Column("canton",    sa.String(50),  nullable=True),
        sa.Column("distrito",  sa.String(50),  nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_distributors_nombre",    "distributors", ["nombre"])
    op.create_index("ix_distributors_ubicacion", "distributors", ["provincia", "canton"])

    # ── 4. products ───────────────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("id",                         sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("numero_registro",             sa.String(50),  nullable=False),
        sa.Column("nombre_comercial",            sa.String(500), nullable=False),
        sa.Column("ingrediente_activo",          sa.Text(),      nullable=False),
        sa.Column("categoria",                   _pc, nullable=False),
        sa.Column("estado",                      _ps, nullable=False),
        sa.Column("banda_toxicologica",          _tb, nullable=True),
        sa.Column("registrante",                 sa.String(500), nullable=True),
        sa.Column("dosis_recomendada",           sa.Text(),      nullable=True),
        sa.Column("intervalo_seguridad_dias",    sa.Integer(),   nullable=True),
        sa.Column("precio_referencia_por_litro", sa.Float(),     nullable=True),
        sa.Column("cultivo_objetivo",            sa.String(100), nullable=True),
        sa.Column("problema_objetivo",           sa.String(100), nullable=True),
        sa.Column("embedding",                   Vector(768),    nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("numero_registro"),
    )
    op.create_index("ix_products_numero_registro",    "products", ["numero_registro"], unique=True)
    op.create_index("ix_products_nombre_comercial",   "products", ["nombre_comercial"])
    op.create_index("ix_products_categoria",          "products", ["categoria"])
    op.create_index("ix_products_estado",             "products", ["estado"])
    op.create_index("ix_products_categoria_estado",   "products", ["categoria", "estado"])
    op.create_index("ix_products_ingrediente_activo", "products", ["ingrediente_activo"])
    op.create_index("ix_products_banda_toxicologica", "products", ["banda_toxicologica"])

    # ── 5. product_distributors ───────────────────────────────────
    op.create_table(
        "product_distributors",
        sa.Column("product_id",     sa.Integer(), nullable=False),
        sa.Column("distributor_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"],     ["products.id"],     ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["distributor_id"], ["distributors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("product_id", "distributor_id"),
    )

    # ── 6. recommendations ────────────────────────────────────────
    op.create_table(
        "recommendations",
        sa.Column("id",                     sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id",                sa.Integer(), nullable=False),
        sa.Column("zone_id",                sa.Integer(), nullable=True),
        sa.Column("ticket_id",              sa.String(100), nullable=False),
        sa.Column("crop",                   sa.String(100), nullable=False),
        sa.Column("crop_stage",             sa.String(50),  nullable=False),
        sa.Column("problem",                sa.String(255), nullable=False),
        sa.Column("problem_category",       sa.String(100), nullable=False),
        sa.Column("last_agrochemical_used", sa.String(255), nullable=True),
        sa.Column("budget_range",           sa.String(50),  nullable=True),
        sa.Column("soil_type",              sa.String(50),  nullable=True),
        sa.Column("humidity",               sa.Numeric(5, 2), nullable=True),
        sa.Column("temperature",            sa.Numeric(5, 2), nullable=True),
        sa.Column("water_quality",          sa.String(50),  nullable=True),
        sa.Column("status",                 _rs, nullable=False, server_default="pending"),
        sa.Column("current_step",           sa.String(50),  nullable=True),
        sa.Column("completed_at",           sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message",          sa.Text(),      nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_id"),
    )
    op.create_index("ix_recommendations_user_id",     "recommendations", ["user_id"])
    op.create_index("ix_recommendations_zone_id",     "recommendations", ["zone_id"])
    op.create_index("ix_recommendations_ticket_id",   "recommendations", ["ticket_id"], unique=True)
    op.create_index("ix_recommendations_status",      "recommendations", ["status"])
    op.create_index("ix_recommendations_user_status", "recommendations", ["user_id", "status"])

    # ── 7. recommendation_products ────────────────────────────────
    op.create_table(
        "recommendation_products",
        sa.Column("id",                        sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("recommendation_id",         sa.Integer(), nullable=False),
        sa.Column("product_id",                sa.Integer(), nullable=False),
        sa.Column("rank",                      sa.Integer(), nullable=False),
        sa.Column("justification",             sa.Text(),    nullable=False),
        sa.Column("dosis",                     sa.Text(),    nullable=True),
        sa.Column("precio_estimado",           sa.Numeric(10, 2), nullable=True),
        sa.Column("toxicidad",                 sa.String(20), nullable=True),
        sa.Column("intervalo_seguridad",       sa.Integer(), nullable=True),
        sa.Column("ventajas",                  sa.Text(),    nullable=True),
        sa.Column("riesgos",                   sa.Text(),    nullable=True),
        sa.Column("recomendacion_uso_general", sa.Text(),    nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["recommendation_id"], ["recommendations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"],        ["products.id"],        ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recommendation_id", "rank",       name="uq_recommendation_rank"),
        sa.UniqueConstraint("recommendation_id", "product_id", name="uq_recommendation_product"),
    )
    op.create_index("ix_recommendation_products_recommendation_id", "recommendation_products", ["recommendation_id"])
    op.create_index("ix_recommendation_products_product_id",        "recommendation_products", ["product_id"])

    # ── 8. lmrs ───────────────────────────────────────────────────
    op.create_table(
        "lmrs",
        sa.Column("id",         sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("plaguicida", sa.String(255), nullable=False),
        sa.Column("clase",      sa.String(255), nullable=True),
        sa.Column("cultivo",    sa.String(500), nullable=False),
        sa.Column("lmr_nac",    sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lmrs_plaguicida", "lmrs", ["plaguicida"])
    op.create_index("ix_lmrs_cultivo",    "lmrs", ["cultivo"])

    # ── 9. regulations ────────────────────────────────────────────
    op.create_table(
        "regulations",
        sa.Column("id",                   sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("numero",               sa.String(50),  nullable=False),
        sa.Column("titulo",               sa.String(500), nullable=False),
        sa.Column("tipo",                 _rt, nullable=False),
        sa.Column("fecha_publicacion",    sa.String(20),  nullable=True),
        sa.Column("fuente_url",           sa.String(500), nullable=True),
        sa.Column("resumen",              sa.Text(),      nullable=True),
        sa.Column("contenido_completo",   sa.Text(),      nullable=True),
        sa.Column("embedding",            Vector(768),    nullable=True),
        sa.Column("sustancias_afectadas", sa.Text(),      nullable=True),
        sa.Column("cultivos_afectados",   sa.Text(),      nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("numero"),
    )
    op.create_index("ix_regulations_numero",     "regulations", ["numero"], unique=True)
    op.create_index("ix_regulations_tipo",       "regulations", ["tipo"])
    op.create_index("ix_regulations_sustancias", "regulations", ["sustancias_afectadas"])

    # ── 10. audit_logs ────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id",          sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id",     sa.Integer(), nullable=True),
        sa.Column("action",      _aa, nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id",   sa.Integer(), nullable=True),
        sa.Column("ip_address",  sa.String(45), nullable=True),
        sa.Column("user_agent",  sa.Text(),     nullable=True),
        sa.Column("detail",      sa.Text(),     nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_user_id",     "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action",      "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id",   "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_user_action", "audit_logs", ["user_id", "action"])
    op.create_index("ix_audit_logs_entity",      "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_created_at",  "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("regulations")
    op.drop_table("lmrs")
    op.drop_table("recommendation_products")
    op.drop_table("recommendations")
    op.drop_table("product_distributors")
    op.drop_table("products")
    op.drop_table("distributors")
    op.drop_table("zones")
    op.drop_table("users")
    for name in ["product_category", "product_status", "toxic_band",
                 "recommendation_status", "audit_action", "regulationtype"]:
        op.execute(f"DROP TYPE IF EXISTS {name}")
