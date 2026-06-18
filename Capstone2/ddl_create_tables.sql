-- ============================================================
-- CAPSTONE 2: Austria Energy Transition
-- DDL - Create all tables for normalized 3NF schema
-- Target: PostgreSQL
-- ============================================================

-- Drop tables if they exist (for idempotent re-runs)
DROP TABLE IF EXISTS economic_indicator CASCADE;
DROP TABLE IF EXISTS policy_event CASCADE;
DROP TABLE IF EXISTS electricity_generation CASCADE;
DROP TABLE IF EXISTS emissions CASCADE;
DROP TABLE IF EXISTS consumption CASCADE;
DROP TABLE IF EXISTS energy_source CASCADE;
DROP TABLE IF EXISTS year_dim CASCADE;
DROP TABLE IF EXISTS country CASCADE;

-- ============================================================
-- 1. country
-- ============================================================
CREATE TABLE country (
    country_id   SERIAL       PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL,
    iso_code     CHAR(3),
    CONSTRAINT uq_country_name UNIQUE (country_name)
);

-- ============================================================
-- 2. year_dim  (temporal dimension)
-- ============================================================
CREATE TABLE year_dim (
    year_id SERIAL      PRIMARY KEY,
    year    INTEGER     NOT NULL,
    decade  VARCHAR(10),
    CONSTRAINT uq_year UNIQUE (year),
    CONSTRAINT chk_year_range CHECK (year >= 1800 AND year <= 2100)
);

-- ============================================================
-- 3. energy_source
-- ============================================================
CREATE TABLE energy_source (
    source_id   SERIAL      PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL,
    source_type VARCHAR(20),
    is_renewable BOOLEAN,
    CONSTRAINT uq_source_name UNIQUE (source_name),
    CONSTRAINT chk_source_type CHECK (
        source_type IN ('renewable', 'fossil', 'nuclear', 'other')
    )
);

-- ============================================================
-- 4. consumption  (per year per source)
-- ============================================================
CREATE TABLE consumption (
    consumption_id       SERIAL       PRIMARY KEY,
    year_id              INTEGER      NOT NULL,
    source_id            INTEGER      NOT NULL,
    total_consumption_twh NUMERIC(10,3),
    renewable_share_pct  NUMERIC(5,2),
    fossil_share_pct     NUMERIC(5,2),
    CONSTRAINT fk_consumption_year
        FOREIGN KEY (year_id) REFERENCES year_dim (year_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_consumption_source
        FOREIGN KEY (source_id) REFERENCES energy_source (source_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_consumption_positive
        CHECK (total_consumption_twh IS NULL OR total_consumption_twh >= 0),
    CONSTRAINT chk_share_range CHECK (
        renewable_share_pct IS NULL OR
        (renewable_share_pct >= 0 AND renewable_share_pct <= 100)
    ),
    CONSTRAINT chk_fossil_share_range CHECK (
        fossil_share_pct IS NULL OR
        (fossil_share_pct >= 0 AND fossil_share_pct <= 100)
    )
);

-- ============================================================
-- 5. emissions  (per year)
-- ============================================================
CREATE TABLE emissions (
    emission_id    SERIAL       PRIMARY KEY,
    year_id        INTEGER      NOT NULL,
    co2_mt         NUMERIC(10,3),
    co2_per_capita_t NUMERIC(8,4),
    CONSTRAINT fk_emissions_year
        FOREIGN KEY (year_id) REFERENCES year_dim (year_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_co2_positive CHECK (co2_mt IS NULL OR co2_mt >= 0),
    CONSTRAINT chk_co2_pc_positive CHECK (co2_per_capita_t IS NULL OR co2_per_capita_t >= 0)
);

-- ============================================================
-- 6. electricity_generation  (per year per source)
-- ============================================================
CREATE TABLE electricity_generation (
    gen_id        SERIAL       PRIMARY KEY,
    year_id       INTEGER      NOT NULL,
    source_id     INTEGER      NOT NULL,
    generation_twh NUMERIC(10,3),
    CONSTRAINT fk_gen_year
        FOREIGN KEY (year_id) REFERENCES year_dim (year_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_gen_source
        FOREIGN KEY (source_id) REFERENCES energy_source (source_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_gen_positive CHECK (generation_twh IS NULL OR generation_twh >= 0)
);

-- ============================================================
-- 7. policy_event  (one per year, optional)
-- ============================================================
CREATE TABLE policy_event (
    event_id   SERIAL       PRIMARY KEY,
    year_id    INTEGER      NOT NULL,
    event_name VARCHAR(200),
    event_flag INTEGER      DEFAULT 0,
    CONSTRAINT fk_policy_year
        FOREIGN KEY (year_id) REFERENCES year_dim (year_id)
        ON DELETE CASCADE,
    CONSTRAINT uq_policy_year UNIQUE (year_id),
    CONSTRAINT chk_event_flag CHECK (event_flag IN (0, 1))
);

-- ============================================================
-- 8. economic_indicator  (one per year)
-- ============================================================
CREATE TABLE economic_indicator (
    indicator_id    SERIAL       PRIMARY KEY,
    year_id         INTEGER      NOT NULL,
    gdp_usd         NUMERIC(16,2),
    population      NUMERIC(12,2),
    energy_intensity NUMERIC(6,3),
    CONSTRAINT fk_econ_year
        FOREIGN KEY (year_id) REFERENCES year_dim (year_id)
        ON DELETE CASCADE,
    CONSTRAINT uq_econ_year UNIQUE (year_id),
    CONSTRAINT chk_gdp_positive CHECK (gdp_usd IS NULL OR gdp_usd >= 0),
    CONSTRAINT chk_pop_positive CHECK (population IS NULL OR population >= 0)
);

-- ============================================================
-- INDEXES  (for performance on FK joins and year lookups)
-- ============================================================
CREATE INDEX idx_consumption_year   ON consumption (year_id);
CREATE INDEX idx_consumption_source ON consumption (source_id);
CREATE INDEX idx_emissions_year     ON emissions (year_id);
CREATE INDEX idx_gen_year           ON electricity_generation (year_id);
CREATE INDEX idx_gen_source         ON electricity_generation (source_id);
CREATE INDEX idx_policy_year        ON policy_event (year_id);
CREATE INDEX idx_econ_year          ON economic_indicator (year_id);
CREATE INDEX idx_year_dim_year      ON year_dim (year);

-- ============================================================
-- END OF DDL
-- ============================================================
