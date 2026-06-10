-- ================================================================
-- Physical Database Schema — SQLite
-- Capstone 2: Physical Activity and Chronic Disease Burden
-- ================================================================
-- SQLite syntax. For PostgreSQL, replace INTEGER PRIMARY KEY AUTOINCREMENT
-- with SERIAL, and use NUMERIC(5,1) instead of REAL.

BEGIN TRANSACTION;

-- ---------------------------------------------------------------
-- 1. Country dimension
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Country (
    country_code    VARCHAR(2)  PRIMARY KEY NOT NULL,
    country_name    VARCHAR(50) NOT NULL,
    region          VARCHAR(30),
    CHECK (country_code = UPPER(country_code))
);

-- ---------------------------------------------------------------
-- 2. AgeGroup dimension
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS AgeGroup (
    age_code    VARCHAR(10) PRIMARY KEY NOT NULL,
    label       VARCHAR(30) NOT NULL,
    lower_bound INTEGER,
    upper_bound INTEGER,
    CHECK (lower_bound IS NULL OR lower_bound >= 0),
    CHECK (upper_bound IS NULL OR upper_bound >= lower_bound)
);

-- ---------------------------------------------------------------
-- 3. Sex dimension
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Sex (
    sex_code VARCHAR(1) PRIMARY KEY NOT NULL,
    label    VARCHAR(10) NOT NULL,
    CHECK (sex_code IN ('T', 'M', 'F'))
);

-- ---------------------------------------------------------------
-- 4. IndicatorCategory dimension
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS IndicatorCategory (
    category_code VARCHAR(30) PRIMARY KEY NOT NULL,
    category_name VARCHAR(50) NOT NULL
);

-- ---------------------------------------------------------------
-- 5. DataSource dimension
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DataSource (
    source_code    VARCHAR(15)  PRIMARY KEY NOT NULL,
    full_name      VARCHAR(80)  NOT NULL,
    api_endpoint   VARCHAR(150) NOT NULL,
    retrieval_date DATE
);

-- ---------------------------------------------------------------
-- 6. HealthIndicator dimension
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS HealthIndicator (
    indicator_code  VARCHAR(30)  PRIMARY KEY NOT NULL,
    indicator_label VARCHAR(100) NOT NULL,
    category_code   VARCHAR(30)  NOT NULL,
    source_code     VARCHAR(15)  NOT NULL,
    unit_of_measure VARCHAR(10)  NOT NULL DEFAULT 'PC',
    description     VARCHAR(255),
    FOREIGN KEY (category_code) REFERENCES IndicatorCategory(category_code),
    FOREIGN KEY (source_code) REFERENCES DataSource(source_code)
);

-- ---------------------------------------------------------------
-- 7. SurveyWave dimension
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS SurveyWave (
    wave_id     INTEGER     PRIMARY KEY NOT NULL,
    description VARCHAR(50) NOT NULL,
    year        INTEGER     NOT NULL,
    CHECK (year >= 2000 AND year <= 2030)
);

-- ---------------------------------------------------------------
-- 8. Measurement fact table
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Measurement (
    measurement_id  INTEGER      PRIMARY KEY AUTOINCREMENT,
    country_code    VARCHAR(2)   NOT NULL,
    age_code        VARCHAR(10)  NOT NULL,
    sex_code        VARCHAR(1)   NOT NULL,
    indicator_code  VARCHAR(30)  NOT NULL,
    wave_id         INTEGER      NOT NULL,
    value           REAL         NOT NULL,
    data_suppressed INTEGER      NOT NULL DEFAULT 0,
    is_outlier      INTEGER      NOT NULL DEFAULT 0,
    FOREIGN KEY (country_code)   REFERENCES Country(country_code),
    FOREIGN KEY (age_code)       REFERENCES AgeGroup(age_code),
    FOREIGN KEY (sex_code)       REFERENCES Sex(sex_code),
    FOREIGN KEY (indicator_code) REFERENCES HealthIndicator(indicator_code),
    FOREIGN KEY (wave_id)        REFERENCES SurveyWave(wave_id),
    CHECK (value >= 0 AND value <= 100),
    CHECK (data_suppressed IN (0, 1)),
    CHECK (is_outlier IN (0, 1))
);

-- ---------------------------------------------------------------
-- Indexes for performance
-- ---------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_measurement_country
    ON Measurement(country_code);
CREATE INDEX IF NOT EXISTS idx_measurement_wave
    ON Measurement(wave_id);
CREATE INDEX IF NOT EXISTS idx_measurement_indicator
    ON Measurement(indicator_code);
CREATE INDEX IF NOT EXISTS idx_measurement_sex
    ON Measurement(sex_code);
CREATE INDEX IF NOT EXISTS idx_measurement_age
    ON Measurement(age_code);
CREATE INDEX IF NOT EXISTS idx_measurement_country_wave_indicator
    ON Measurement(country_code, wave_id, indicator_code);
CREATE INDEX IF NOT EXISTS idx_healthindicator_category
    ON HealthIndicator(category_code);

COMMIT;
