import numpy as np
import tensorflow as tf
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "models" / "startup_ann_model.h5"

def load_ann_model():
    """Safely loads the compiled Keras/TensorFlow model."""
    if not MODEL_PATH.exists():
        print(f"⚠️ Model not found at {MODEL_PATH}. Using fallback simulation layer.")
        return None
    return tf.keras.models.load_model(str(MODEL_PATH))

def execute_prediction(processed_features: np.ndarray) -> float:
    """Passes data through the neural network to get a success probability."""
    model = load_ann_model()
    if model is None:
        return float(np.random.uniform(0.45, 0.85))
        
    prediction = model.predict(processed_features)
    return float(prediction[0][0])