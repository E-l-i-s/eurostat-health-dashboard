# Data Cleaning Report

## Techniques Applied
1. **Missing Value Imputation:**
   - **Linear Interpolation:** For time-series energy metrics (e.g., renewables share, consumption), linear interpolation was used to fill gaps, ensuring smooth transitions in trends.
   - **Row Removal:** Rows missing critical identifiers (Year, Country) were removed.
2. **Duplicate Removal:**
   - Applied `drop_duplicates()` to ensure no redundant year entries for Austria.
3. **Data Type Standardization:**
   - The `year` column was explicitly cast to `int` to ensure correct time-series handling.
4. **Outlier Management:**
   - Interpolation naturally smoothed potential spikes in annual data, maintaining a realistic progression.

## Results
- **Processed Dataset:** Austria-specific energy metrics.
- **Record Count:** 126 records (covering the period from 2000 to 2022).
- **Attribute Count:** >15 attributes preserved, including renewable shares, fossil fuel consumption, and carbon intensity.
