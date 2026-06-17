"""Initial schema — all tables matching current ORM models.

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-06-16

Crea todas las tablas del proyecto en un solo bloque idempotente.
Las migraciones posteriores (002, 5e5dc56e6153, a1b2c3d4e5f6) son
idempotentes y detectan columnas/tablas existentes antes de actuar.
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ---- tipos enum ----
    product_category = sa.Enum(
        "plaguicida", "fertilizante",
        name="product_category", create_type=True,
    )
    product_status = sa.Enum(
        "activo", "cancelado", "expirado", "suspendido",
        name="product_status", create_type=True,
    )
    toxic_band = sa.Enum(
        "roja", "amarilla", "azul", "verde", "no_aplica",
        name="toxic_band", create_type=True,
    )
    recommendation_status = sa.Enum(
        "pending", "processing", "completed", "failed",
        name="recommendation_status", create_type=True,
    )
    audit_action = sa.Enum(
        "create", "read", "update", "delete",
        "login", "logout",
        "recommendation_request", "recommendation_view",
        name="audit_action", create_type=True,
    )
    regulation_type = sa.Enum(
        "decreto", "ley", "resolucion", "lista_prohibida", "lmr", "otro",
        name="regulationtype", create_type=True,
    )

    # ---- users ----
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("auth_user_id", sa.Uuid(), unique=True, nullable=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("identification", sa.String(20), unique=True, nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_identification", "users", ["identification"], unique=True)
    op.create_index("ix_users_auth_user_id", "users", ["auth_user_id"])
    op.create_index("ix_users_email_active", "users", ["email", "is_active"])

    # ---- zones ----
    op.create_table(
        "zones",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("soil_type", sa.String(50), nullable=True),
        sa.Column("humidity", sa.Numeric(5, 2), nullable=True),
        sa.Column("temperature", sa.Numeric(5, 2), nullable=True),
        sa.Column("water_quality", sa.String(50), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 8), nullable=True),
        sa.Column("longitude", sa.Numeric(11, 8), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_zones_user_id", "zones", ["user_id"])
    op.create_index("ix_zones_user_name", "zones", ["user_id", "name"])

    # ---- products ----
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("numero_registro", sa.String(50), unique=True, nullable=False),
        sa.Column("nombre_comercial", sa.String(500), nullable=False),
        sa.Column("ingrediente_activo", sa.Text(), nullable=False),
        sa.Column("categoria", product_category, nullable=False),
        sa.Column("estado", product_status, nullable=False),
        sa.Column("banda_toxicologica", toxic_band, nullable=True),
        sa.Column("registrante", sa.String(500), nullable=True),
        sa.Column("dosis_recomendada", sa.Text(), nullable=True),
        sa.Column("intervalo_seguridad_dias", sa.Integer(), nullable=True),
        sa.Column("precio_referencia_por_litro", sa.Float(), nullable=True),
        sa.Column("cultivo_objetivo", sa.String(100), nullable=True),
        sa.Column("problema_objetivo", sa.String(100), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_numero_registro", "products", ["numero_registro"], unique=True)
    op.create_index("ix_products_nombre_comercial", "products", ["nombre_comercial"])
    op.create_index("ix_products_categoria", "products", ["categoria"])
    op.create_index("ix_products_estado", "products", ["estado"])
    op.create_index("ix_products_banda_toxicologica", "products", ["banda_toxicologica"])
    op.create_index("ix_products_categoria_estado", "products", ["categoria", "estado"])
    op.create_index("ix_products_ingrediente_activo", "products", ["ingrediente_activo"])

    # ---- distributors ----
    op.create_table(
        "distributors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("correo", sa.String(255), nullable=True),
        sa.Column("telefono", sa.String(50), nullable=True),
        sa.Column("ubicacion", sa.String(255), nullable=True),
        sa.Column("provincia", sa.String(50), nullable=True),
        sa.Column("canton", sa.String(50), nullable=True),
        sa.Column("distrito", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_distributors_nombre", "distributors", ["nombre"])
    op.create_index("ix_distributors_ubicacion", "distributors", ["provincia", "canton"])

    # ---- product_distributors (many-to-many) ----
    op.create_table(
        "product_distributors",
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("distributor_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["distributor_id"], ["distributors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("product_id", "distributor_id"),
    )

    # ---- recommendations ----
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=True),
        sa.Column("ticket_id", sa.String(100), unique=True, nullable=False),
        sa.Column("crop", sa.String(100), nullable=False),
        sa.Column("crop_stage", sa.String(50), nullable=False),
        sa.Column("problem", sa.String(255), nullable=False),
        sa.Column("problem_category", sa.String(100), nullable=False),
        sa.Column("last_agrochemical_used", sa.String(255), nullable=True),
        sa.Column("budget_range", sa.String(50), nullable=True),
        sa.Column("soil_type", sa.String(50), nullable=True),
        sa.Column("humidity", sa.Numeric(5, 2), nullable=True),
        sa.Column("temperature", sa.Numeric(5, 2), nullable=True),
        sa.Column("water_quality", sa.String(50), nullable=True),
        sa.Column("status", recommendation_status, nullable=False, server_default="pending"),
        sa.Column("current_step", sa.String(50), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recommendations_user_id", "recommendations", ["user_id"])
    op.create_index("ix_recommendations_zone_id", "recommendations", ["zone_id"])
    op.create_index("ix_recommendations_ticket_id", "recommendations", ["ticket_id"], unique=True)
    op.create_index("ix_recommendations_status", "recommendations", ["status"])
    op.create_index("ix_recommendations_user_status", "recommendations", ["user_id", "status"])

    # ---- recommendation_products ----
    # Incluye columnas LLM (ventajas/riesgos/recomendacion_uso_general) que la
    # migración a1b2c3d4e5f6 agrega condicionalmente — al crearlas aquí esa
    # migración las detectará como existentes y las omitirá (idempotente).
    op.create_table(
        "recommendation_products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("recommendation_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("dosis", sa.Text(), nullable=True),
        sa.Column("precio_estimado", sa.Numeric(10, 2), nullable=True),
        sa.Column("toxicidad", sa.String(20), nullable=True),
        sa.Column("intervalo_seguridad", sa.Integer(), nullable=True),
        sa.Column("ventajas", sa.Text(), nullable=True),
        sa.Column("riesgos", sa.Text(), nullable=True),
        sa.Column("recomendacion_uso_general", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["recommendation_id"], ["recommendations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recommendation_id", "rank", name="uq_recommendation_rank"),
        sa.UniqueConstraint("recommendation_id", "product_id", name="uq_recommendation_product"),
    )
    op.create_index("ix_recommendation_products_recommendation_id", "recommendation_products", ["recommendation_id"])
    op.create_index("ix_recommendation_products_product_id", "recommendation_products", ["product_id"])

    # ---- regulations ----
    op.create_table(
        "regulations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("numero", sa.String(50), unique=True, nullable=False),
        sa.Column("titulo", sa.String(500), nullable=False),
        sa.Column("tipo", regulation_type, nullable=False),
        sa.Column("fecha_publicacion", sa.String(20), nullable=True),
        sa.Column("fuente_url", sa.String(500), nullable=True),
        sa.Column("resumen", sa.Text(), nullable=True),
        sa.Column("contenido_completo", sa.Text(), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("sustancias_afectadas", sa.Text(), nullable=True),
        sa.Column("cultivos_afectados", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_regulations_numero", "regulations", ["numero"], unique=True)
    op.create_index("ix_regulations_tipo", "regulations", ["tipo"])
    op.create_index("ix_regulations_sustancias", "regulations", ["sustancias_afectadas"])

    # ---- audit_logs ----
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_user_action", "audit_logs", ["user_id", "action"])
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("regulations")
    op.drop_table("recommendation_products")
    op.drop_table("recommendations")
    op.drop_table("product_distributors")
    op.drop_table("distributors")
    op.drop_table("products")
    op.drop_table("zones")
    op.drop_table("users")

    for name in ("audit_action", "recommendation_status", "toxic_band",
                 "product_status", "product_category", "regulationtype"):
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)

    op.execute("DROP EXTENSION IF EXISTS vector")
