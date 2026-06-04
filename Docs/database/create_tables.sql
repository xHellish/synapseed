-- ============================================================
-- SynapSeed — Script de creación de tablas
-- Motor: PostgreSQL 16 + pgvector 0.8
-- Ejecutar en orden. Requiere la extensión pgvector instalada.
-- ============================================================

-- Habilitar extensión para UUIDs y vectores
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ─────────────────────────────────────────────────────────────
-- USUARIOS
-- ─────────────────────────────────────────────────────────────
CREATE TABLE users (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    identification  VARCHAR(20) NOT NULL UNIQUE,   -- Cédula (se usa para login)
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    phone           VARCHAR(50)  NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX ix_users_identification ON users (identification);
CREATE UNIQUE INDEX ix_users_email         ON users (email);


-- ─────────────────────────────────────────────────────────────
-- ZONAS / FINCAS
-- El usuario registra sus fincas para reutilizar contexto ambiental.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE zones (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID         NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name          VARCHAR(255) NOT NULL,
    -- Valores controlados por dropdown:
    soil_type     VARCHAR(100) NOT NULL,  -- arcilloso | arenoso | limoso | franco | franco-arcilloso | franco-arenoso
    humidity      VARCHAR(50)  NOT NULL,  -- baja | media | alta
    temperature   VARCHAR(50)  NOT NULL,  -- <15°C | 15-20°C | 20-25°C | 25-30°C | >30°C
    water_quality VARCHAR(50)  NOT NULL,  -- buena | regular | mala
    location      VARCHAR(255),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_zones_user ON zones (user_id);


-- ─────────────────────────────────────────────────────────────
-- DISTRIBUIDORES / PROVEEDORES
-- Información de contacto. El usuario los contacta vía mailto:
-- ─────────────────────────────────────────────────────────────
CREATE TABLE distributors (
    id         UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name       VARCHAR(255) NOT NULL,
    email      VARCHAR(255),
    phone      VARCHAR(50),
    location   VARCHAR(255),
    website    VARCHAR(500),
    is_active  BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);


-- ─────────────────────────────────────────────────────────────
-- PRODUCTOS AGROQUÍMICOS
-- Catálogo con embeddings vectoriales para búsqueda semántica.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE products (
    id                   UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    name                 VARCHAR(255)  NOT NULL,
    active_ingredient     VARCHAR(255),
    description          TEXT,
    -- herbicida | fungicida | insecticida | fertilizante | biocontrol
    category             VARCHAR(100)  NOT NULL,
    -- líquido | granular | polvo | emulsión
    formulation          VARCHAR(100),
    concentration        VARCHAR(100),
    dosage_per_hectare   VARCHAR(255),
    application_method   VARCHAR(255),
    safety_interval_days INT,
    price_per_liter      FLOAT,
    distributor_id       UUID          REFERENCES distributors (id) ON DELETE SET NULL,
    sfe_registration     VARCHAR(50),
    -- active | expired | revoked
    sfe_status           VARCHAR(50)   NOT NULL DEFAULT 'active',
    -- I | II | III | IV  (banda toxicológica)
    toxicity_band        VARCHAR(20),
    -- Embedding 768 dimensiones para búsqueda semántica (pgvector)
    embedding            VECTOR(768),
    is_active            BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_products_category    ON products (category);
CREATE INDEX ix_products_sfe_reg     ON products (sfe_registration);
CREATE INDEX ix_products_distributor ON products (distributor_id);

-- Índice HNSW para búsqueda vectorial rápida (similitud coseno)
CREATE INDEX ix_products_embedding ON products
    USING hnsw (embedding vector_cosine_ops);


-- ─────────────────────────────────────────────────────────────
-- RECOMENDACIONES
-- Cada caso solicitado por un usuario con su contexto completo.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE recommendations (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id    VARCHAR(100) NOT NULL UNIQUE,   -- ID público para tracking SSE
    user_id      UUID         NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    zone_id      UUID         REFERENCES zones (id) ON DELETE SET NULL,  -- NULL si eligió "Ninguna"

    -- Estado del pipeline de agentes
    -- pending | analyzing | researching | validating | synthesizing | completed | failed
    status       VARCHAR(50)  NOT NULL DEFAULT 'pending',

    -- Contexto del caso (todos vienen de dropdowns)
    crop                 VARCHAR(100)  NOT NULL,
    crop_stage           VARCHAR(100)  NOT NULL,
    affected_area        VARCHAR(100)  NOT NULL,
    soil_type            VARCHAR(100)  NOT NULL,
    humidity             VARCHAR(50)   NOT NULL,
    temperature          VARCHAR(50)   NOT NULL,
    water_quality        VARCHAR(50)   NOT NULL,
    problem_to_solve     VARCHAR(255)  NOT NULL,
    last_agrochemical    VARCHAR(255),   -- puede ser "ninguno"
    max_budget_per_liter VARCHAR(100),

    -- Outputs de cada agente (JSON)
    agent_context     JSONB,  -- Agente 1: Analizador
    agent_research    JSONB,  -- Agente 2: Investigador RAG
    agent_validation  JSONB,  -- Agente 3: Validador Legal
    final_recommendation JSONB,  -- Agente 4: Sintetizador

    processing_time_ms INT,
    error_message      TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at       TIMESTAMPTZ
);

CREATE UNIQUE INDEX ix_recommendations_ticket     ON recommendations (ticket_id);
CREATE        INDEX ix_recommendations_user       ON recommendations (user_id);
CREATE        INDEX ix_recommendations_status     ON recommendations (status);
CREATE        INDEX ix_recommendations_user_date  ON recommendations (user_id, created_at DESC);


-- ─────────────────────────────────────────────────────────────
-- PRODUCTOS RECOMENDADOS
-- Siempre exactamente 3 por recomendación (rank 1, 2 y 3).
-- ─────────────────────────────────────────────────────────────
CREATE TABLE recommendation_products (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_id UUID        NOT NULL REFERENCES recommendations (id) ON DELETE CASCADE,
    product_id        UUID        NOT NULL REFERENCES products (id) ON DELETE RESTRICT,
    rank              INT         NOT NULL CHECK (rank IN (1, 2, 3)),
    justification     TEXT        NOT NULL,
    recommended_dosage VARCHAR(255),
    estimated_cost    FLOAT,
    compatibility_notes TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_rec_product_rank UNIQUE (recommendation_id, rank)
);

CREATE INDEX ix_rec_products_rec     ON recommendation_products (recommendation_id);
CREATE INDEX ix_rec_products_product ON recommendation_products (product_id);


-- ─────────────────────────────────────────────────────────────
-- REGULACIONES
-- Normativas del SFE/MAG para validación legal de productos.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE regulations (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    regulation_code       VARCHAR(100) NOT NULL UNIQUE,
    title                 VARCHAR(500) NOT NULL,
    -- SFE | MAG | SENASA
    issuing_body          VARCHAR(100) NOT NULL,
    description           TEXT,
    prohibited_substances JSONB,   -- Lista de ingredientes prohibidos
    restricted_crops      JSONB,   -- Restricciones por cultivo
    is_active             BOOLEAN  NOT NULL DEFAULT TRUE,
    source_url            VARCHAR(500),
    -- Embedding para búsqueda semántica (el Agente Validador la consulta)
    embedding             VECTOR(768),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX ix_regulations_code   ON regulations (regulation_code);
CREATE        INDEX ix_regulations_issuer ON regulations (issuing_body);

-- Índice HNSW para búsqueda vectorial
CREATE INDEX ix_regulations_embedding ON regulations
    USING hnsw (embedding vector_cosine_ops);


-- ─────────────────────────────────────────────────────────────
-- BITÁCORA DE AUDITORÍA
-- Registro de acciones críticas del sistema (login, cambios, etc.)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE audit_logs (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID         REFERENCES users (id) ON DELETE SET NULL,
    -- login | register | create_recommendation | update_profile | delete_zone | etc.
    action      VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id   UUID,
    details     JSONB,
    ip_address  VARCHAR(45),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_audit_user   ON audit_logs (user_id);
CREATE INDEX ix_audit_action ON audit_logs (action);
CREATE INDEX ix_audit_date   ON audit_logs (created_at DESC);


-- ─────────────────────────────────────────────────────────────
-- VERIFICACIÓN: mostrar tablas creadas
-- ─────────────────────────────────────────────────────────────
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
