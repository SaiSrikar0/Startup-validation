"""
Member 2 — ANN Model Definition
================================
Defines, trains, evaluates, and persists the Artificial Neural Network
for startup success prediction.

Architecture
------------
Input → BatchNorm → Dense(256, ReLU) → Dropout(0.4)
                  → Dense(128, ReLU) → Dropout(0.3)
                  → Dense(64,  ReLU) → Dropout(0.2)
                  → Dense(1,  Sigmoid)

Designed for binary classification:
  1  →  Successful startup
  0  →  Failed / inactive startup
  (Labels supplied by Member 3)
"""

import json
import numpy as np
import tensorflow as tf
from pathlib import Path
from tensorflow.keras import layers, callbacks, regularizers


MODELS_DIR = Path(__file__).parent
MODELS_DIR.mkdir(parents=True, exist_ok=True)


# ── Model factory ─────────────────────────────────────────────────────────────

def build_ann(input_dim: int, class_weight_ratio: float = 1.0) -> tf.keras.Model:
    """
    Build and compile the ANN.

    Parameters
    ----------
    input_dim         : number of features after feature engineering
    class_weight_ratio: pos_weight = (# negatives) / (# positives),
                        passed as class_weight during fit to handle imbalance.
                        Member 3 provides this value.
    """
    inputs = tf.keras.Input(shape=(input_dim,), name="startup_features")

    x = layers.BatchNormalization()(inputs)

    x = layers.Dense(
        256, activation="relu",
        kernel_regularizer=regularizers.l2(1e-4),
        name="dense_1"
    )(x)
    x = layers.Dropout(0.4)(x)

    x = layers.Dense(
        128, activation="relu",
        kernel_regularizer=regularizers.l2(1e-4),
        name="dense_2"
    )(x)
    x = layers.Dropout(0.3)(x)

    x = layers.Dense(
        64, activation="relu",
        kernel_regularizer=regularizers.l2(1e-4),
        name="dense_3"
    )(x)
    x = layers.Dropout(0.2)(x)

    output = layers.Dense(1, activation="sigmoid", name="success_prob")(x)

    model = tf.keras.Model(inputs=inputs, outputs=output, name="StartupANN")

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss=tf.keras.losses.BinaryFocalCrossentropy(gamma=2.0),
        metrics=[
            "accuracy",
            tf.keras.metrics.AUC(name="auc"),
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
        ],
    )
    return model


# ── Training helper ───────────────────────────────────────────────────────────

def get_callbacks(checkpoint_path: Path) -> list:
    """Standard training callbacks."""
    cbs = [
        callbacks.EarlyStopping(
            monitor="val_auc", patience=15,
            restore_best_weights=True, mode="max", verbose=1
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5,
            patience=7, min_lr=1e-6, verbose=1
        ),
        callbacks.ModelCheckpoint(
            filepath=str(checkpoint_path),
            monitor="val_auc", save_best_only=True,
            mode="max", verbose=1
        ),
    ]

    try:
        import tensorboard  # noqa: F401
        cbs.append(
            callbacks.TensorBoard(
                log_dir=str(MODELS_DIR / "logs"),
                histogram_freq=1
            )
        )
    except ImportError:
        print("[ANN] TensorBoard not installed, skipping TensorBoard callback.")

    return cbs


def train(
    model: tf.keras.Model,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val:   np.ndarray,
    y_val:   np.ndarray,
    class_weight: dict | None = None,
    epochs: int = 100,
    batch_size: int = 32,
) -> tf.keras.callbacks.History:
    """
    Train the ANN.

    Parameters
    ----------
    class_weight : {0: w0, 1: w1}  — computed by Member 3 from label distribution.
                   If None, defaults to balanced weighting.
    """
    checkpoint_path = MODELS_DIR / "best_model.keras"

    if class_weight is None:
        n_neg = int((y_train == 0).sum())
        n_pos = int((y_train == 1).sum())
        total = n_neg + n_pos
        class_weight = {0: total / (2 * n_neg), 1: total / (2 * n_pos)}
        print(f"[ANN] Auto class weights - 0: {class_weight[0]:.3f}, 1: {class_weight[1]:.3f}")

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        class_weight=class_weight,
        callbacks=get_callbacks(checkpoint_path),
        verbose=1,
    )
    return history


# ── Persistence ───────────────────────────────────────────────────────────────

def save_model(model: tf.keras.Model, path: Path = MODELS_DIR / "ann_final.keras"):
    model.save(path)
    print(f"[ANN] Model saved -> {path}")


def load_model(path: Path | None = None) -> tf.keras.Model:
    candidates = [
        path,
        MODELS_DIR / "best_model.keras",
        MODELS_DIR / "ann_final.keras",
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        if Path(candidate).exists():
            model = tf.keras.models.load_model(str(candidate))
            print(f"[ANN] Model loaded <- {candidate}")
            return model
    raise FileNotFoundError(
        "No trained ANN weights found. Run: "
        "python -m app.models.ANN_Model.train --data ../database/data/cleaned/Startups_cleaned.csv"
    )
