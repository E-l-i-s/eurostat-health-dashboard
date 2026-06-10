# Data Collection Strategy Document

## Methodology
- **Collection Method:** Direct retrieval of the OWID Energy dataset via a secure HTTPS download.
- **Frequency:** One-time retrieval of the most recent historical time-series data.
- **Tools:** 
    - **Python (Pandas):** For filtering the global dataset to focus specifically on Austria.
    - **curl/Invoke-WebRequest:** For reliable file acquisition.
- **Storage Format:** CSV (Comma Separated Values) for raw and processed data.

## Process
1. Download the master `owid-energy-data.csv` file.
2. Filter the dataset to include only rows where `country` is 'Austria'.
3. Handle missing values (NaNs) by removing them or using appropriate imputation (e.g., interpolation for time-series).
4. Validate that the resulting dataset covers the required time period (2000–present) and contains the necessary energy metrics.
