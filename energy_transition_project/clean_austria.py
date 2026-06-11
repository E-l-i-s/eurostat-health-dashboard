import pandas as pd
import numpy as np

def clean_austria_data(input_path, output_path):
    df = pd.read_csv(input_path)
    
    # 1. Remove rows where essential columns are NaN
    df = df.dropna(subset=['year', 'country'])
    
    # 2. Force all numeric columns to float to ensure interpolation works
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors='ignore')
        except:
            pass
            
    # Re-identify numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    # 3. Interpolate
    df[numeric_cols] = df[numeric_cols].interpolate(method='linear', limit_direction='both')
    
    # 4. Final Fill for any remaining NaNs
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    # 5. Remove duplicates
    df = df.drop_duplicates()
    
    # 6. Ensure data types
    df['year'] = df['year'].astype(int)
    
    df.to_csv(output_path, index=False)
    print(f"Cleaned {len(df)} records.")

if __name__ == "__main__":
    clean_austria_data("energy_transition_project/data/austria_energy.csv", "energy_transition_project/data/austria_energy_cleaned.csv")
