# Physical ERD (SQLite DDL)

## Physical Activity and Chronic Disease Burden Across Europe

```mermaid
erDiagram
    Country ||--o{ Measurement : "country_code"
    AgeGroup ||--o{ Measurement : "age_code"
    Sex ||--o{ Measurement : "sex_code"
    HealthIndicator ||--o{ Measurement : "indicator_code"
    SurveyWave ||--o{ Measurement : "wave_id"
    IndicatorCategory ||--o{ HealthIndicator : "category_code"
    DataSource ||--o{ HealthIndicator : "source_code"

    Country {
        varchar_2 PK "country_code"
        varchar_50 "country_name"
        varchar_30 "region"
    }

    AgeGroup {
        varchar_10 PK "age_code"
        varchar_30 "label"
        int "lower_bound"
        int "upper_bound"
    }

    Sex {
        varchar_1 PK "sex_code"
        varchar_10 "label"
    }

    IndicatorCategory {
        varchar_30 PK "category_code"
        varchar_50 "category_name"
    }

    DataSource {
        varchar_15 PK "source_code"
        varchar_80 "full_name"
        varchar_150 "api_endpoint"
        date "retrieval_date"
    }

    HealthIndicator {
        varchar_30 PK "indicator_code"
        varchar_100 "indicator_label"
        varchar_30 FK "category_code"
        varchar_15 FK "source_code"
        varchar_10 "unit_of_measure"
        varchar_255 "description"
    }

    SurveyWave {
        int PK "wave_id"
        varchar_50 "description"
        int "year"
    }

    Measurement {
        int PK "measurement_id"
        varchar_2 FK "country_code"
        varchar_10 FK "age_code"
        varchar_1 FK "sex_code"
        varchar_30 FK "indicator_code"
        int FK "wave_id"
        real "value"
        int "data_suppressed"
        int "is_outlier"
    }
```

## SQLite DDL Statements

```sql
CREATE TABLE Country (
    country_code  VARCHAR(2)  PRIMARY KEY,
    country_name  VARCHAR(50) NOT NULL,
    region        VARCHAR(30)
);

CREATE TABLE AgeGroup (
    age_code    VARCHAR(10) PRIMARY KEY,
    label       VARCHAR(30) NOT NULL,
    lower_bound INTEGER,
    upper_bound INTEGER
);

CREATE TABLE Sex (
    sex_code VARCHAR(1)  PRIMARY KEY,
    label    VARCHAR(10) NOT NULL
);

CREATE TABLE IndicatorCategory (
    category_code VARCHAR(30) PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL
);

CREATE TABLE DataSource (
    source_code    VARCHAR(15)  PRIMARY KEY,
    full_name      VARCHAR(80)  NOT NULL,
    api_endpoint   VARCHAR(150) NOT NULL,
    retrieval_date DATE
);

CREATE TABLE HealthIndicator (
    indicator_code   VARCHAR(30)  PRIMARY KEY,
    indicator_label  VARCHAR(100) NOT NULL,
    category_code    VARCHAR(30)  NOT NULL REFERENCES IndicatorCategory(category_code),
    source_code      VARCHAR(15)  NOT NULL REFERENCES DataSource(source_code),
    unit_of_measure  VARCHAR(10)  NOT NULL,
    description      VARCHAR(255)
);

CREATE TABLE SurveyWave (
    wave_id     INTEGER     PRIMARY KEY,
    description VARCHAR(50) NOT NULL,
    year        INTEGER     NOT NULL
);

CREATE TABLE Measurement (
    measurement_id  INTEGER     PRIMARY KEY AUTOINCREMENT,
    country_code    VARCHAR(2)  NOT NULL REFERENCES Country(country_code),
    age_code        VARCHAR(10) NOT NULL REFERENCES AgeGroup(age_code),
    sex_code        VARCHAR(1)  NOT NULL REFERENCES Sex(sex_code),
    indicator_code  VARCHAR(30) NOT NULL REFERENCES HealthIndicator(indicator_code),
    wave_id         INTEGER     NOT NULL REFERENCES SurveyWave(wave_id),
    value           REAL        NOT NULL CHECK (value >= 0 AND value <= 100),
    data_suppressed INTEGER     NOT NULL DEFAULT 0,
    is_outlier      INTEGER     NOT NULL DEFAULT 0
);

-- Performance indexes
CREATE INDEX idx_measurement_country ON Measurement(country_code);
CREATE INDEX idx_measurement_indicator ON Measurement(indicator_code);
CREATE INDEX idx_measurement_wave ON Measurement(wave_id);
CREATE INDEX idx_measurement_age ON Measurement(age_code);
CREATE INDEX idx_measurement_sex ON Measurement(sex_code);
CREATE INDEX idx_health_indicator_category ON HealthIndicator(category_code);
CREATE INDEX idx_health_indicator_source ON HealthIndicator(source_code);
```

## Notes

- All tables use `VARCHAR` or `INTEGER` types as supported by SQLite.
- The `Measurement` table has a composite index pattern: individual indexes on each FK column support the star-query join patterns used by the dashboard API.
- The `CHECK` constraint on `Measurement.value` enforces the percentage range (0–100) at the database level.
- The physical model matches the logical 3NF model exactly; no denormalisation was applied because query performance via indexes was adequate.
