# Logical ERD (3NF)

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
        string country_code PK "ISO 3166-1 alpha-2"
        string country_name "Full country name"
        string region "European region grouping"
    }

    AgeGroup {
        string age_code PK "EHIS age group code"
        string label "Human-readable label"
        int lower_bound "Lower bound in years"
        int upper_bound "Upper bound in years"
    }

    Sex {
        string sex_code PK "T M or F"
        string label "Total Male or Female"
    }

    IndicatorCategory {
        string category_code PK "Unique category identifier"
        string category_name "Physical Activity Chronic Disease or BMI"
    }

    DataSource {
        string source_code PK "Eurostat dataset code"
        string full_name "Full Eurostat dataset name"
        string api_endpoint "API URL for retrieval"
        date retrieval_date "Date data was last retrieved"
    }

    HealthIndicator {
        string indicator_code PK "Unique indicator code"
        string indicator_label "Human-readable indicator name"
        string category_code FK "FK to IndicatorCategory"
        string source_code FK "FK to DataSource"
        string unit_of_measure "PC or other unit"
        string description "Short description"
    }

    SurveyWave {
        int wave_id PK "Survey year ID"
        string description "EHIS Wave 1/2/3"
        int year "Calendar year"
    }

    Measurement {
        int measurement_id PK "Auto-increment PK"
        string country_code FK "FK to Country"
        string age_code FK "FK to AgeGroup"
        string sex_code FK "FK to Sex"
        string indicator_code FK "FK to HealthIndicator"
        int wave_id FK "FK to SurveyWave"
        float value "Percentage value 0-100"
        bool data_suppressed "0=published 1=suppressed"
        bool is_outlier "0=normal 1=outlier"
    }
```

## Normalisation Notes

### 2NF Violation Resolved

**Before:** `HealthIndicator` had `category_name` stored directly alongside `category_code`. This violated 2NF because `category_name` depended on `category_code`, which is only part of a candidate key.

**After:** `category_name` moved to the `IndicatorCategory` table. `HealthIndicator` references it via `category_code` FK.

### 3NF Violation Resolved

**Before:** `Measurement` had `country_name` stored directly alongside `country_code`. This violated 3NF because `country_name` transitively depends on `country_code` via the `Country` entity.

**After:** `country_name` moved to the `Country` table only. `Measurement` references it via `country_code` FK.
