# Dataset Summary

## Overview

The cleaned dataset contains measurements of physical activity insufficiency, chronic disease prevalence, and BMI classification across European countries, drawn from three Eurostat EHIS datasets. The data covers approximately 35 countries across up to three survey waves (2008, 2014, 2019).

## Key Statistics

- **Rows:** ~25,000 measurements after cleaning (actual count depends on API response completeness and suppression patterns)
- **Columns:** 15 standardized fields
- **Time range:** 2008 — 2019 (three EHIS waves)
- **Geographic coverage:** EU member states plus EFTA and candidate countries
- **Indicators:** Physical activity insufficiency, obesity, diabetes, hypertension, cardiovascular disease, BMI categories

## Identified Entities

The data naturally decomposes into these entity groups:

1. **Geographic entities** — Countries identified by ISO 3166-1 alpha-2 codes with associated names
2. **Demographic dimensions** — Sex categories (Total, Male, Female) and age groups (8 standardized brackets from TOTAL to 75+)
3. **Health indicators** — Individual measured indicators grouped into categories (Physical Activity, Chronic Disease, BMI)
4. **Temporal dimension** — Survey waves identified by year (2008, 2014, 2019)
5. **Source provenance** — The original Eurostat dataset code and retrieval metadata
6. **Measurements** — The observed values themselves, linked to all of the above

## Schema vs. NoSQL Rationale

A relational star schema suits this data for three specific reasons. First, the primary query pattern is dimensional aggregation: filter by country, sex, age, and wave, then aggregate indicator values. Star schemas optimize this exact pattern via foreign key joins from a central fact table to narrow dimension tables. Second, the dimension tables are small, stable, and rarely updated — Country has ~35 rows, AgeGroup has ~8, Sex has 3. These fit naturally in indexed relational tables and do not benefit from the flexible schema of a document store. Third, the dashboards in Capstone 3 require cross-indicator queries (e.g., scatter plots of inactivity vs. chronic disease prevalence per country), which demand JOIN operations that are far more efficient in SQL with a star schema than in a denormalized NoSQL collection where each document would redundantly store dimension labels.
