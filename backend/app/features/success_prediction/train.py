import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from pathlib import Path

# Move up 5 levels to reach the true root repository folder 'Startup-validation'
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DATA_PATH = BASE_DIR / "database" / "data" / "cleaned" / "Startups_cleaned.csv"
MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models"

def load_and_prepare_data():
    """Loads cleaned data from the database team tracking folder."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing training dataset at: {DATA_PATH}")
        
    df = pd.read_csv(DATA_PATH)
    
    # --- MOCK PREPARATION LOGIC ---
    # Replace these with your database team's exact target column 
    # and feature matrix columns once finalized.
    X = np.random.randn(len(df), 5)  # Assuming 5 features for now
    y = np.random.randint(0, 2, size=(len(df), 1))
    
    return X, y

def build_ann(input_dim):
    """Compiles the Artificial Neural Network layers."""
    model = Sequential([
        Dense(32, activation='relu', input_dim=input_dim),
        Dropout(0.3),
        Dense(16, activation='relu'),
        Dropout(0.2),
        Dense(1, activation='sigmoid')  # Outputs a 0.0 - 1.0 probability score
    ])
    
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

def train_and_save_pipeline():
    print("🚀 Loading training datasets...")
    X, y = load_and_prepare_data()
    
    print("🏗️ Constructing network layer configurations...")
    model = build_ann(input_dim=X.shape[1])
    
    print("🏋️ Training the ANN model...")
    model.fit(X, y, epochs=10, batch_size=32, validation_split=0.2, verbose=1)
    
    # Ensure destination folder exists
    os.makedirs(MODEL_DIR, exist_ok=True)
    save_target = MODEL_DIR / "startup_ann_model.h5"
    
    print(f"💾 Saving trained model serialization to: {save_target}")
    model.save(str(save_target))
    print("✅ Model saved successfully!")

if __name__ == "__main__":
    train_and_save_pipeline()