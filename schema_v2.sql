-- =============================================================================
-- PRT661 Sydn2 Theme 2 — Schema v2 (Assessment 4)
-- Extends the five A2 tables (schema_a2.sql) with model-ops tables, a privacy-
-- safe public view, and least-privilege roles replacing the shared team login.
-- Idempotent: safe to run repeatedly.
-- =============================================================================

-- ---------- A2 tables get the indexes the A2 report promised ----------------
CREATE INDEX IF NOT EXISTS ix_cleaned_suburb_settle ON cleaned_sales (suburb, settlement_date);
CREATE INDEX IF NOT EXISTS ix_raw_dealing ON raw_sales (dealing_number);

-- ---------- feature store v2 (complete suburb x quarter grid) ----------------
CREATE TABLE IF NOT EXISTS feature_store_v2 (
    suburb                 VARCHAR(100) NOT NULL,
    quarter                DATE         NOT NULL,
    postcode               INTEGER,
    region                 VARCHAR(20),
    n_sales                INTEGER      NOT NULL,
    median_price           DOUBLE PRECISION,
    median_price_per_sqm   DOUBLE PRECISION,
    strata_share           DOUBLE PRECISION,
    qoq_pct_change         DOUBLE PRECISION,
    yoy_pct_change         DOUBLE PRECISION,
    region_qoq             DOUBLE PRECISION,
    state_qoq              DOUBLE PRECISION,
    abs_region_growth_lag1 DOUBLE PRECISION,
    is_partial_quarter     SMALLINT     NOT NULL DEFAULT 0,
    PRIMARY KEY (suburb, quarter),
    CHECK (n_sales >= 0),
    CHECK (strata_share IS NULL OR strata_share BETWEEN 0 AND 1)
);

-- ---------- model registry: every trained model is a row ---------------------
CREATE TABLE IF NOT EXISTS model_registry (
    model_id        SERIAL PRIMARY KEY,
    model_name      VARCHAR(60)  NOT NULL,
    model_version   VARCHAR(20)  NOT NULL,
    horizon         SMALLINT     NOT NULL CHECK (horizon BETWEEN 1 AND 4),
    target          VARCHAR(30)  NOT NULL,          -- 'qoq' or 'cumulative'
    trained_through DATE         NOT NULL,          -- last observed target quarter
    artefact_path   TEXT         NOT NULL,
    artefact_sha256 CHAR(64)     NOT NULL,
    params_json     JSONB,
    backtest_json   JSONB,                          -- RMSE/MAE/coverage on the common window
    git_commit      VARCHAR(40),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    is_champion     BOOLEAN      NOT NULL DEFAULT FALSE,
    UNIQUE (model_name, model_version, horizon, target)
);

-- ---------- published forecasts --------------------------------------------
CREATE TABLE IF NOT EXISTS forecasts (
    suburb            VARCHAR(100) NOT NULL,
    origin_quarter    DATE         NOT NULL,
    target_quarter    DATE         NOT NULL,
    horizon           SMALLINT     NOT NULL,
    anchor_price      DOUBLE PRECISION,
    point_pct         DOUBLE PRECISION,   -- cumulative % change from anchor
    p10_pct           DOUBLE PRECISION,
    p90_pct           DOUBLE PRECISION,
    point_price       DOUBLE PRECISION,
    p10_price         DOUBLE PRECISION,
    p90_price         DOUBLE PRECISION,
    reliability       VARCHAR(10),        -- 'high' | 'medium' | 'low' (liquidity-based)
    model_version     VARCHAR(20)  NOT NULL,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    PRIMARY KEY (suburb, origin_quarter, horizon, model_version)
);

CREATE TABLE IF NOT EXISTS backtest_predictions (
    suburb VARCHAR(100), origin DATE, target_quarter DATE, horizon SMALLINT,
    model VARCHAR(60), actual DOUBLE PRECISION, predicted DOUBLE PRECISION,
    PRIMARY KEY (suburb, target_quarter, horizon, model)
);

-- ---------- pipeline audit log -------------------------------------------------
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id       SERIAL PRIMARY KEY,
    stage        VARCHAR(30) NOT NULL,
    started_at   TIMESTAMPTZ NOT NULL,
    finished_at  TIMESTAMPTZ,
    status       VARCHAR(10) NOT NULL,     -- 'ok' | 'failed'
    rows_in      BIGINT,
    rows_out     BIGINT,
    details_json JSONB
);

-- ---------- privacy-safe public view (never exposes cells built from <5 sales) --
CREATE OR REPLACE VIEW v_public_suburb_quarter AS
SELECT suburb, quarter, region,
       n_sales,
       CASE WHEN n_sales >= 5 THEN median_price END       AS median_price,
       CASE WHEN n_sales >= 5 THEN qoq_pct_change END     AS qoq_pct_change
FROM feature_store_v2
WHERE is_partial_quarter = 0;

-- =============================================================================
-- Least-privilege roles (replaces the single shared 'prt661_team' login)
-- Group roles hold privileges; each person gets their own LOGIN role.
-- =============================================================================
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'prt661_etl')     THEN CREATE ROLE prt661_etl NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'prt661_analyst') THEN CREATE ROLE prt661_analyst NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'prt661_app_ro')  THEN CREATE ROLE prt661_app_ro NOLOGIN; END IF;
END $$;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public TO prt661_etl;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO prt661_etl;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO prt661_analyst;
REVOKE SELECT ON raw_sales FROM prt661_analyst;         -- addresses stay with the ETL role
-- the web app can only read published, aggregated outputs
GRANT SELECT ON forecasts, v_public_suburb_quarter, model_registry TO prt661_app_ro;
