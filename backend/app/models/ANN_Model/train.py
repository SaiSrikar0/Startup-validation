"""
Member 2 — Training Pipeline
==============================
End-to-end script: load data → engineer features → train ANN → evaluate → save.

Run:
    python train.py --data data/Startups.csv --label_col status

Expects Member 3 to have added a binary 'label' column (1=success, 0=failure).
If the column is missing it falls back to a simple heuristic so development
can proceed in parallel.
"""

import argparse
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, f1_score, roc_curve
)

try:
    from utils.feature_engineering import StartupFeatureEngineer
    from utils.ann_model import build_ann, train, save_model, load_model
except ModuleNotFoundError:
    from feature_engineering import StartupFeatureEngineer
    from ann_model import build_ann, train, save_model, load_model

OUTPUTS = Path("outputs")
OUTPUTS.mkdir(exist_ok=True)


# ── Label fallback (until Member 3 delivers labels) ──────────────────────────

def _heuristic_label(df: pd.DataFrame) -> pd.Series:
    """
    Temporary label: 1 if status string suggests active/acquired/ipo.
    Member 3 will replace this with a rigorous definition.
    """
    SUCCESS_KEYWORDS = {"operating", "acquired", "ipo", "public", "active"}
    status = df.get("Satus", df.get("Status", pd.Series(["unknown"] * len(df))))
    return status.fillna("unknown").str.lower().apply(
        lambda s: int(any(kw in s for kw in SUCCESS_KEYWORDS))
    )


# ── Evaluation helpers ────────────────────────────────────────────────────────

def evaluate(model, X_test, y_test, threshold: float = 0.5):
    probs = model.predict(X_test, verbose=0).flatten()
    preds = (probs >= threshold).astype(int)

    auc   = roc_auc_score(y_test, probs)
    f1    = f1_score(y_test, preds, zero_division=0)
    report = classification_report(y_test, preds, target_names=["Failed", "Success"])

    print("\n" + "=" * 60)
    print("  EVALUATION RESULTS")
    print("=" * 60)
    print(f"  AUC-ROC : {auc:.4f}")
    print(f"  F1 Score: {f1:.4f}")
    print(f"\n{report}")

    # ── plots ─────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Confusion matrix
    cm = confusion_matrix(y_test, preds)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=axes[0],
                xticklabels=["Failed", "Success"],
                yticklabels=["Failed", "Success"])
    axes[0].set_title("Confusion Matrix")
    axes[0].set_ylabel("Actual")
    axes[0].set_xlabel("Predicted")

    # ROC curve
    fpr, tpr, _ = roc_curve(y_test, probs)
    axes[1].plot(fpr, tpr, lw=2, label=f"AUC = {auc:.3f}")
    axes[1].plot([0, 1], [0, 1], "k--")
    axes[1].set_xlabel("False Positive Rate")
    axes[1].set_ylabel("True Positive Rate")
    axes[1].set_title("ROC Curve")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(OUTPUTS / "evaluation.png", dpi=150)
    plt.close()
    print(f"[Train] Evaluation plots saved → {OUTPUTS / 'evaluation.png'}")

    # Save metrics JSON
    metrics = {"auc": round(auc, 4), "f1": round(f1, 4)}
    with open(OUTPUTS / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


def plot_history(history):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(history.history["loss"],     label="Train Loss")
    axes[0].plot(history.history["val_loss"], label="Val Loss")
    axes[0].set_title("Loss")
    axes[0].legend()

    axes[1].plot(history.history["auc"],     label="Train AUC")
    axes[1].plot(history.history["val_auc"], label="Val AUC")
    axes[1].set_title("AUC")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(OUTPUTS / "training_history.png", dpi=150)
    plt.close()
    print(f"[Train] Training history saved → {OUTPUTS / 'training_history.png'}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main(data_path: str, label_col: str = "label", test_size: float = 0.2):
    print(f"\n[Train] Loading data from {data_path}")
    df = pd.read_csv(data_path, encoding="latin-1")
    print(f"[Train] Loaded {len(df)} rows, {df.shape[1]} columns")

    # ── Labels ───────────────────────────────────────────────────────────────
    if label_col in df.columns:
        y = df[label_col].astype(int).values
        print(f"[Train] Using '{label_col}' column for labels (from Member 3)")
    else:
        print(f"[Train] '{label_col}' not found — using heuristic labels (temporary)")
        y = _heuristic_label(df).values

    print(f"[Train] Class distribution — 0 (fail): {(y==0).sum()}  |  1 (success): {(y==1).sum()}")

    # ── Feature engineering ───────────────────────────────────────────────────
    fe = StartupFeatureEngineer()
    X  = fe.fit_transform(df)
    fe.save()
    print(f"[Train] Feature matrix shape: {X.shape}")

    # ── Train / val / test split ──────────────────────────────────────────────
    X_trainval, X_test, y_trainval, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_trainval, y_trainval, test_size=0.15, random_state=42, stratify=y_trainval
    )
    print(f"[Train] Split → train:{len(X_train)}  val:{len(X_val)}  test:{len(X_test)}")

    # ── Class weights (from label distribution) ───────────────────────────────
    n_neg, n_pos = (y_train == 0).sum(), (y_train == 1).sum()
    total = n_neg + n_pos
    class_weight = {0: total / (2 * n_neg), 1: total / (2 * n_pos)}

    # ── Build & train ─────────────────────────────────────────────────────────
    model = build_ann(input_dim=X.shape[1])
    model.summary()

    history = train(
        model, X_train, y_train, X_val, y_val,
        class_weight=class_weight,
        epochs=100,
        batch_size=32,
    )

    plot_history(history)

    # ── Evaluate on hold-out test set ─────────────────────────────────────────
    metrics = evaluate(model, X_test, y_test)

    # ── Save final model ──────────────────────────────────────────────────────
    save_model(model)

    print("\n[Train] ✓ Training complete.")
    print(f"         AUC-ROC = {metrics['auc']}   F1 = {metrics['f1']}")
    print("         Artifacts saved under models/ and outputs/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the Startup ANN (Member 2)")
    parser.add_argument("--data",      default="data/Startups.csv", help="Path to the CSV dataset")
    parser.add_argument("--label_col", default="label",             help="Column with binary labels (from Member 3)")
    parser.add_argument("--test_size", type=float, default=0.2,     help="Fraction held out for testing")
    args = parser.parse_args()

    main(args.data, args.label_col, args.test_size)
