import numpy as np
import pandas as pd

def clean_and_scale_input(data: dict) -> np.ndarray:
    """Transforms incoming JSON into a normalized numerical array for the ANN."""
    df = pd.DataFrame([data])
    
    # Simple extraction mapping for demo pipeline consistency
    numeric_features = [
        df['funding_total_usd'].values[0], 
        df['market_size_usd'].values[0], 
        df['team_experience_years'].values[0]
    ]
    
    country_mapped = len(df['country_code'].values[0]) * 0.1
    category_mapped = len(df['category_code'].values[0]) * 0.1
    
    combined_features = numeric_features + [country_mapped, category_mapped]
    return np.array(combined_features).reshape(1, -1)