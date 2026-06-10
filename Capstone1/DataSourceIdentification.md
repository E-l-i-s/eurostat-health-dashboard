# Data Source Identification

## Source Register

| # | Dataset | Eurostat Code | Official URL | Type | Format | Relevance |
|---|---------|---------------|-------------|------|--------|-----------|
| 1 | Physical activity during leisure time | hlth_ehis_pe3 | https://ec.europa.eu/eurostat/databrowser/view/hlth_ehis_pe3/default/table | Structured | JSON:stat (API), CSV (browser) | Direct measure of the primary independent variable — percentage of population meeting or not meeting WHO physical activity guidelines |
| 2 | Self-reported chronic conditions | hlth_ehis_cd1e | https://ec.europa.eu/eurostat/databrowser/view/hlth_ehis_cd1e/default/table | Structured | JSON:stat (API), CSV (browser) | Direct measure of the primary dependent variable — prevalence of diagnosed chronic conditions by type |
| 3 | Body mass index (BMI) classification | hlth_ehis_bm1e | https://ec.europa.eu/eurostat/databrowser/view/hlth_ehis_bm1e/default/table | Structured | JSON:stat (API), CSV (browser) | Enrichment dataset providing obesity prevalence as an additional health outcome and covariate |

## Source Justification

**hlth_ehis_pe3** — Physical activity during leisure time. This dataset captures the percentage of the population in each country, age group, and sex category that reports engaging in sufficient physical activity to meet WHO recommendations. I include it because it provides the primary exposure variable for both case studies. Without this dataset, there is no way to quantify the geographic and demographic distribution of physical inactivity. The data are structured quantitative percentage values derived from survey questionnaires.

**Case Study Relevance:** Primary independent variable for Case Study A (geographic mapping of inactivity burden) and Case Study B (inactivity–chronic disease correlation).

**hlth_ehis_cd1e** — Self-reported chronic morbidity. This dataset reports the percentage of respondents who indicate they have been diagnosed with specific chronic conditions by a medical professional. I include it because it provides the outcome variable for Case Study B and enables direct comparison between inactivity rates and disease prevalence at the country level. The data are structured quantitative prevalence rates broken down by condition type, geography, and demography.

**Case Study Relevance:** Primary dependent variable for Case Study B (chronic disease prevalence as an outcome of physical inactivity).

**hlth_ehis_bm1e** — Body mass index classification. This dataset reports the distribution of BMI categories (underweight, normal, overweight, obese) based on self-reported height and weight. I include it because obesity is both a chronic condition in its own right and an intermediate variable linking physical inactivity to cardiovascular and metabolic disease. The data are structured quantitative percentages across standard WHO BMI cutoffs.

**Case Study Relevance:** Enrichment dataset for Case Study B (obesity as both a covariate and an intermediate outcome in the inactivity–disease pathway).

## Classification Summary

All three datasets are **structured** and **quantitative**. They arrive as rectangular datasets with defined dimensions (country, year, sex, age, indicator) and numerical measurement values. No unstructured or qualitative data sources are used in this project.
