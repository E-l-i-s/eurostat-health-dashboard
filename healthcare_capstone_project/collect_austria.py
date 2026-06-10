import pandas as pd

def collect_austria_data():
    # Load the massive dataset
    df = pd.read_csv("healthcare_capstone_project/data/owid_energy.csv")
    
    # Filter for Austria
    austria_df = df[df['country'] == 'Austria'].copy()
    
    # Save the filtered dataset
    austria_df.to_csv("healthcare_capstone_project/data/austria_energy.csv", index=False)
    print(f"Collected {len(austria_df)} records for Austria.")

if __name__ == "__main__":
    collect_austria_data()
