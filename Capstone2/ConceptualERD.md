# Conceptual ERD

## Physical Activity and Chronic Disease Burden Across Europe

```mermaid
erDiagram
    Country ||--o{ Measurement : "has"
    AgeGroup ||--o{ Measurement : "has"
    Sex ||--o{ Measurement : "has"
    HealthIndicator ||--o{ Measurement : "appears-in"
    SurveyWave ||--o{ Measurement : "contains"
    IndicatorCategory ||--o{ HealthIndicator : "groups"
    DataSource ||--o{ HealthIndicator : "provides"

    Country {
        string country_code PK
        string country_name
        string region
    }

    AgeGroup {
        string age_code PK
        string label
        int lower_bound
        int upper_bound
    }

    Sex {
        string sex_code PK
        string label
    }

    HealthIndicator {
        string indicator_code PK
        string indicator_label
        string category_code FK
        string source_code FK
        string unit_of_measure
    }

    IndicatorCategory {
        string category_code PK
        string category_name
    }

    SurveyWave {
        int wave_id PK
        string description
        int year
    }

    DataSource {
        string source_code PK
        string full_name
        string api_endpoint
        date retrieval_date
    }

    Measurement {
        int measurement_id PK
        string country_code FK
        string age_code FK
        string sex_code FK
        string indicator_code FK
        int wave_id FK
        float value
        bool data_suppressed
        bool is_outlier
    }
```

## Star Schema Description

The data model follows a **star schema** with **Measurement** as the central fact table and seven dimension tables:

| Dimension | Role | Attributes |
|-----------|------|------------|
| Country | Geography | country_code (PK), country_name, region |
| AgeGroup | Demography | age_code (PK), label, lower_bound, upper_bound |
| Sex | Demography | sex_code (PK), label |
| HealthIndicator | Subject matter | indicator_code (PK), indicator_label, unit_of_measure, category_code (FK), source_code (FK) |
| IndicatorCategory | Classification | category_code (PK), category_name |
| SurveyWave | Time | wave_id (PK), description, year |
| DataSource | Provenance | source_code (PK), full_name, api_endpoint |

Two dimensions (IndicatorCategory, DataSource) relate to HealthIndicator rather than directly to Measurement, creating a minor snowflake extension. This is acceptable because these tables change rarely and join depth stays at a maximum of two hops from the fact table.
