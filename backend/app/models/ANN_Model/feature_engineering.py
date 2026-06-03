"""
Member 2 — Feature Engineering
================================
Handles all preprocessing for the ANN model:
  - Column renaming / standardisation
  - Text-based multi-hot encoding for Categories & Investors
  - Numeric extraction from funding round strings
  - Label encoding for categorical geo-features
  - StandardScaler for numeric columns

Designed to work both standalone (CSV path) and when Member 1
injects a clean pandas DataFrame from the DB layer.
"""

import re
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import LabelEncoder, StandardScaler, MultiLabelBinarizer

# ── column name map (raw CSV → internal names) ──────────────────────────────
COL_MAP = {
    "Company":                                  "company",
    "Satus":                                    "status",          # typo in source
    "Status":                                   "status",
    "Year Founded":                             "year_founded",
    "Description":                              "description",
    "Categories":                               "categories",
    "Founders":                                 "founders",
    "Investors":                                "investors",
    "Amounts raised in different funding rounds": "funding_rounds",
    "Headquarters (City)":                      "hq_city",
    "Headquarters (US State)":                  "hq_state",
    "Headquarters (Country)":                   "hq_country",
}

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


# ── helpers ──────────────────────────────────────────────────────────────────

def _split_tags(raw: pd.Series, sep: str = ",") -> pd.Series:
    """Split a column of comma-separated strings into lists of stripped tokens."""
    return raw.fillna("").apply(
        lambda x: [t.strip().lower() for t in str(x).split(sep) if t.strip()]
    )


def _extract_funding_total(raw: pd.Series) -> pd.Series:
    """
    Parse the free-text 'funding_rounds' column and return the
    **total** USD amount as a float.

    Handles patterns like:
      - '$1.2M Seed, $5M Series A'
      - '1200000'
      - '€2M'
    """
    def _parse(text: str) -> float:
        if pd.isna(text) or str(text).strip() == "":
            return 0.0
        text = str(text).upper()
        # extract all numeric amounts with optional K / M / B suffix
        matches = re.findall(r"[\$€£]?\s*([\d,]+\.?\d*)\s*([KMB]?)", text)
        total = 0.0
        for num_str, suffix in matches:
            try:
                num = float(num_str.replace(",", ""))
                if suffix == "K":
                    num *= 1_000
                elif suffix == "M":
                    num *= 1_000_000
                elif suffix == "B":
                    num *= 1_000_000_000
                total += num
            except ValueError:
                continue
        return total

    return raw.apply(_parse)


def _extract_round_count(raw: pd.Series) -> pd.Series:
    """Count the number of distinct funding rounds mentioned."""
    ROUND_KEYWORDS = [
        "seed", "series a", "series b", "series c", "series d",
        "pre-seed", "angel", "ipo", "bridge", "convertible",
        "growth", "venture", "grant",
    ]
    def _count(text: str) -> int:
        text = str(text).lower()
        return sum(1 for kw in ROUND_KEYWORDS if kw in text)
    return raw.apply(_count)


# ── main class ───────────────────────────────────────────────────────────────

class StartupFeatureEngineer:
    """
    Fit on training data, transform train / test / live inference data.

    Usage
    -----
    fe = StartupFeatureEngineer()
    X_train = fe.fit_transform(df_train)          # also saves artifacts
    X_test  = fe.transform(df_test)
    fe.save()   # persists everything under models/artifacts/

    # ─ OR ─
    fe2 = StartupFeatureEngineer.load()            # restore for inference
    X_new = fe2.transform(df_new)
    """

    # top-N most frequent categories / investors to keep as features
    TOP_CATEGORIES = 50
    TOP_INVESTORS  = 30

    def __init__(self):
        self.scaler        = StandardScaler()
        self.mlb_cat       = MultiLabelBinarizer()
        self.mlb_inv       = MultiLabelBinarizer()
        self.le_state      = LabelEncoder()
        self.le_country    = LabelEncoder()
        self._fitted       = False
        self._top_cats: list  = []
        self._top_invs: list  = []
        self.feature_names_: list = []

    # ── internal ─────────────────────────────────────────────────────────────

    def _rename(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns={k: v for k, v in COL_MAP.items() if k in df.columns})

    def _base_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Derive numeric / geo features that are always present."""
        out = pd.DataFrame(index=df.index)

        # ── Year founded → company age ──────────────────────────────────────
        current_year = 2024
        out["company_age"] = current_year - pd.to_numeric(
            df["year_founded"], errors="coerce"
        ).fillna(current_year - 5)

        # ── Funding ─────────────────────────────────────────────────────────
        out["funding_total_log"] = np.log1p(_extract_funding_total(df["funding_rounds"]))
        out["round_count"]       = _extract_round_count(df["funding_rounds"])

        # ── Geo: label-encoded ───────────────────────────────────────────────
        out["hq_state"]   = df["hq_state"].fillna("Unknown")
        out["hq_country"] = df["hq_country"].fillna("Unknown")

        # ── Founders: count ──────────────────────────────────────────────────
        out["founder_count"] = (
            df["founders"].fillna("").apply(lambda x: len([f for f in str(x).split(",") if f.strip()]))
        )

        return out

    def _get_top_n(self, series_of_lists: pd.Series, n: int) -> list:
        from collections import Counter
        all_tags = [tag for lst in series_of_lists for tag in lst]
        return [tag for tag, _ in Counter(all_tags).most_common(n)]

    # ── public API ────────────────────────────────────────────────────────────

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        df = self._rename(df.copy())

        base = self._base_features(df)

        # ── Categories multi-hot ─────────────────────────────────────────────
        cat_lists  = _split_tags(df["categories"])
        self._top_cats = self._get_top_n(cat_lists, self.TOP_CATEGORIES)
        filtered_cats  = cat_lists.apply(lambda lst: [t for t in lst if t in self._top_cats])
        self.mlb_cat.fit(filtered_cats)
        cat_arr = self.mlb_cat.transform(filtered_cats)

        # ── Investors multi-hot ──────────────────────────────────────────────
        inv_lists  = _split_tags(df["investors"])
        self._top_invs = self._get_top_n(inv_lists, self.TOP_INVESTORS)
        filtered_invs  = inv_lists.apply(lambda lst: [t for t in lst if t in self._top_invs])
        self.mlb_inv.fit(filtered_invs)
        inv_arr = self.mlb_inv.transform(filtered_invs)

        # ── Geo encoding ─────────────────────────────────────────────────────
        base["hq_state"]   = self.le_state.fit_transform(base["hq_state"])
        base["hq_country"] = self.le_country.fit_transform(base["hq_country"])

        # ── Assemble & scale ─────────────────────────────────────────────────
        numeric = base.values.astype(float)
        X = np.hstack([numeric, cat_arr, inv_arr])
        X = self.scaler.fit_transform(X)

        # ── Record feature names ─────────────────────────────────────────────
        self.feature_names_ = (
            list(base.columns)
            + [f"cat_{c}" for c in self.mlb_cat.classes_]
            + [f"inv_{i}" for i in self.mlb_inv.classes_]
        )

        self._fitted = True
        return X

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Call fit_transform first (or load saved artifacts).")

        df = self._rename(df.copy())
        base = self._base_features(df)

        cat_lists     = _split_tags(df["categories"])
        filtered_cats = cat_lists.apply(lambda lst: [t for t in lst if t in self._top_cats])
        cat_arr       = self.mlb_cat.transform(filtered_cats)

        inv_lists     = _split_tags(df["investors"])
        filtered_invs = inv_lists.apply(lambda lst: [t for t in lst if t in self._top_invs])
        inv_arr       = self.mlb_inv.transform(filtered_invs)

        # unseen labels → "Unknown" mapping for geo
        def _safe_le(encoder, series):
            known = set(encoder.classes_)
            return series.apply(lambda x: x if x in known else encoder.classes_[0])

        base["hq_state"]   = self.le_state.transform(_safe_le(self.le_state,   base["hq_state"]))
        base["hq_country"] = self.le_country.transform(_safe_le(self.le_country, base["hq_country"]))

        numeric = base.values.astype(float)
        X = np.hstack([numeric, cat_arr, inv_arr])
        return self.scaler.transform(X)

    # ── persistence ──────────────────────────────────────────────────────────

    def save(self, directory: Path = ARTIFACTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.scaler,    directory / "scaler.pkl")
        joblib.dump(self.mlb_cat,   directory / "mlb_cat.pkl")
        joblib.dump(self.mlb_inv,   directory / "mlb_inv.pkl")
        joblib.dump(self.le_state,  directory / "le_state.pkl")
        joblib.dump(self.le_country, directory / "le_country.pkl")
        meta = {
            "top_cats": self._top_cats,
            "top_invs": self._top_invs,
            "feature_names": self.feature_names_,
        }
        with open(directory / "fe_meta.json", "w") as f:
            json.dump(meta, f, indent=2)
        print(f"[FeatureEngineer] Artifacts saved to {directory}")

    @classmethod
    def load(cls, directory: Path = ARTIFACTS_DIR) -> "StartupFeatureEngineer":
        fe = cls()
        fe.scaler     = joblib.load(directory / "scaler.pkl")
        fe.mlb_cat    = joblib.load(directory / "mlb_cat.pkl")
        fe.mlb_inv    = joblib.load(directory / "mlb_inv.pkl")
        fe.le_state   = joblib.load(directory / "le_state.pkl")
        fe.le_country = joblib.load(directory / "le_country.pkl")
        with open(directory / "fe_meta.json") as f:
            meta = json.load(f)
        fe._top_cats      = meta["top_cats"]
        fe._top_invs      = meta["top_invs"]
        fe.feature_names_ = meta["feature_names"]
        fe._fitted = True
        print(f"[FeatureEngineer] Artifacts loaded from {directory}")
        return fe
