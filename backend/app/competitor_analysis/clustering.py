"""
clustering.py
=============
Trains and persists a KMeans cluster model on startup data using
Categories and funding-round features.  Also supports DBSCAN for
exploratory / noise-tolerant clustering.

Usage (standalone):
    python clustering.py --data ../member1_api/data/Startups.csv
"""

import argparse
import ast
import os
import pickle
import re

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
CLUSTER_MODEL_PATH = os.path.join(MODEL_DIR, "cluster_model.pkl")

FUNDING_COLUMNS_PATTERN = re.compile(
    r"amount(s)? raised", re.IGNORECASE
)

N_CLUSTERS_DEFAULT = 8
RANDOM_STATE = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_categories(series: pd.Series) -> list[list[str]]:
    """Return a list-of-lists from a column that may contain comma-separated
    strings or Python-style list literals."""
    result = []
    for val in series.fillna(""):
        val = str(val).strip()
        if val.startswith("["):
            try:
                parsed = ast.literal_eval(val)
                result.append([str(t).strip().lower() for t in parsed if t])
                continue
            except (ValueError, SyntaxError):
                pass
        result.append([t.strip().lower() for t in val.split(",") if t.strip()])
    return result


def _extract_total_funding(df: pd.DataFrame) -> pd.Series:
    """Sum up all funding-round columns into a single numeric series."""
    funding_cols = [c for c in df.columns if FUNDING_COLUMNS_PATTERN.search(c)]

    if not funding_cols:
        return pd.Series(np.zeros(len(df)), index=df.index)

    def _to_float(val):
        if pd.isna(val):
            return 0.0
        # Split by comma to handle multiple funding rounds in one cell
        parts = str(val).split(",")
        total = 0.0
        for part in parts:
            part = part.strip()
            # Remove currency symbols, spaces — keep digits and decimal point only
            cleaned = re.sub(r"[^\d.]", "", part)
            try:
                total += float(cleaned)
            except ValueError:
                pass  # "undisclosed amount" → skip
        return total

    totals = df[funding_cols].applymap(_to_float).sum(axis=1)
    return totals


def build_feature_matrix(df: pd.DataFrame):
    """
    Build a numeric feature matrix from raw startup data.

    Returns
    -------
    X : np.ndarray   shape (n_samples, n_features)
    mlb : MultiLabelBinarizer  (fitted)
    scaler : StandardScaler    (fitted)
    feature_names : list[str]
    """
    # --- Category one-hot encoding ---
    cat_lists = _parse_categories(df["Categories"])
    mlb = MultiLabelBinarizer(sparse_output=False)
    cat_matrix = mlb.fit_transform(cat_lists)
    cat_feature_names = [f"cat_{c}" for c in mlb.classes_]

    # --- Funding total (log-scaled to reduce skew) ---
    total_funding = _extract_total_funding(df).values.reshape(-1, 1)
    # log1p so zeros stay 0
    total_funding_log = np.log1p(total_funding)

    # --- Year Founded (numeric) ---
    year = pd.to_numeric(df["Year Founded"], errors="coerce").fillna(
        df["Year Founded"].mode()[0] if not df["Year Founded"].mode().empty else 2010
    ).values.reshape(-1, 1)

    # --- Concatenate all numeric features (before scaling) ---
    numeric_features = np.hstack([total_funding_log, year])
    scaler = StandardScaler()
    numeric_scaled = scaler.fit_transform(numeric_features)
    numeric_feature_names = ["log_total_funding", "year_founded"]

    X = np.hstack([cat_matrix, numeric_scaled])
    feature_names = cat_feature_names + numeric_feature_names

    return X, mlb, scaler, feature_names


# ---------------------------------------------------------------------------
# KMeans
# ---------------------------------------------------------------------------

def train_kmeans(
    df: pd.DataFrame,
    n_clusters: int = N_CLUSTERS_DEFAULT,
) -> dict:
    """
    Train a KMeans model and return a result bundle.

    Returns
    -------
    dict with keys: model, mlb, scaler, feature_names, labels, inertia
    """
    X, mlb, scaler, feature_names = build_feature_matrix(df)

    km = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init="auto")
    km.fit(X)

    return {
        "model": km,
        "mlb": mlb,
        "scaler": scaler,
        "feature_names": feature_names,
        "labels": km.labels_,
        "inertia": km.inertia_,
        "algorithm": "kmeans",
        "n_clusters": n_clusters,
    }


# ---------------------------------------------------------------------------
# DBSCAN
# ---------------------------------------------------------------------------

def train_dbscan(
    df: pd.DataFrame,
    eps: float = 0.5,
    min_samples: int = 3,
) -> dict:
    """
    Train a DBSCAN model and return a result bundle.
    DBSCAN labels noise points as -1.
    """
    X, mlb, scaler, feature_names = build_feature_matrix(df)

    db = DBSCAN(eps=eps, min_samples=min_samples)
    labels = db.fit_predict(X)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

    return {
        "model": db,
        "mlb": mlb,
        "scaler": scaler,
        "feature_names": feature_names,
        "labels": labels,
        "algorithm": "dbscan",
        "n_clusters": n_clusters,
    }


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def save_cluster_model(bundle: dict, path: str = CLUSTER_MODEL_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"[clustering] Cluster model saved → {path}")


def load_cluster_model(path: str = CLUSTER_MODEL_PATH) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Cluster model not found at '{path}'. "
            "Run clustering.py --data <csv> first."
        )
    with open(path, "rb") as f:
        return pickle.load(f)


# ---------------------------------------------------------------------------
# Predict cluster for a single startup (inference-time)
# ---------------------------------------------------------------------------

def predict_cluster(startup_row: pd.Series, bundle: dict) -> int:
    """
    Predict the cluster label for a single startup row.
    startup_row must contain 'Categories', 'Amounts raised…', 'Year Founded'.
    """
    df_single = startup_row.to_frame().T.reset_index(drop=True)

    mlb: MultiLabelBinarizer = bundle["mlb"]
    scaler: StandardScaler = bundle["scaler"]
    model = bundle["model"]

    cat_lists = _parse_categories(df_single["Categories"])
    cat_matrix = mlb.transform(cat_lists)

    total_funding = _extract_total_funding(df_single).values.reshape(-1, 1)
    total_funding_log = np.log1p(total_funding)

    year = pd.to_numeric(df_single["Year Founded"], errors="coerce").fillna(2010).values.reshape(-1, 1)
    numeric_scaled = scaler.transform(np.hstack([total_funding_log, year]))

    X = np.hstack([cat_matrix, numeric_scaled])

    if bundle["algorithm"] == "kmeans":
        return int(model.predict(X)[0])
    else:
        # DBSCAN has no predict(); use nearest cluster centroid heuristic
        return int(model.fit_predict(X)[0])


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Train startup cluster model")
    parser.add_argument("--data", required=True, help="Path to Startups.csv")
    parser.add_argument("--algorithm", choices=["kmeans", "dbscan"], default="kmeans")
    parser.add_argument("--n_clusters", type=int, default=N_CLUSTERS_DEFAULT)
    parser.add_argument("--eps", type=float, default=0.5, help="DBSCAN eps")
    parser.add_argument("--min_samples", type=int, default=3, help="DBSCAN min_samples")
    parser.add_argument("--output", default=CLUSTER_MODEL_PATH, help="Output .pkl path")
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    print(f"[clustering] Loaded {len(df)} rows from {args.data}")

    if args.algorithm == "kmeans":
        bundle = train_kmeans(df, n_clusters=args.n_clusters)
        print(f"[clustering] KMeans inertia={bundle['inertia']:.2f}, "
              f"clusters={bundle['n_clusters']}")
    else:
        bundle = train_dbscan(df, eps=args.eps, min_samples=args.min_samples)
        print(f"[clustering] DBSCAN found {bundle['n_clusters']} clusters "
              f"(noise points labelled -1)")

    # Attach the dataframe (needed by similarity engine)
    bundle["df"] = df.copy()
    bundle["df"]["_cluster"] = bundle["labels"]

    save_cluster_model(bundle, path=args.output)


if __name__ == "__main__":
    main()