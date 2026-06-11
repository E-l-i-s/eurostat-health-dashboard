# Conceptual & Logical Data Model

## Conceptual Model
The model is designed to represent the multi-dimensional nature of energy data, linking countries and time periods to specific metrics and energy sources.
- **Country** and **Year** are the core dimensions.
- **EnergyMetric** allows for flexible storage of various metrics (e.g., GDP, Population, Carbon Intensity).
- **EnergySource** and **EnergySourceValue** track the specific mix of energy production (e.g., Solar, Wind, Coal).
- **Emissions** and **GDP_Data** provide specialized tables for environmental and economic outcomes.

## Logical Model (3NF)
The model follows 3NF to ensure high performance and data integrity:
1. **Country** (`CountryID`, Name, ISO_Code)
2. **Year** (`YearID`, Year)
3. **EnergyMetric** (`MetricID`, MetricName, Unit)
4. **EnergyValue** (`ValueID`, `CountryID`, `YearID`, `MetricID`, Value)
5. **EnergySource** (`SourceID`, SourceName)
6. **EnergySourceValue** (`SourceValueID`, `CountryID`, `YearID`, `SourceID`, Value)
7. **Emissions** (`EmissionID`, `CountryID`, `YearID`, CO2_Amount)
8. **GDP_Data** (`GDPID`, `CountryID`, `YearID`, GDP_Value)

## Justification
This structure separates the *definition* of a metric from its *value*. This allows us to add new energy metrics (e.g., "Hydrogen consumption") or new energy sources (e.g., "Nuclear") without altering the table structure, ensuring a highly scalable and normalized architecture.
