"""
similarity_engine.py
====================
Given a query startup (by company name or raw feature dict), returns the
Top-N most similar startups from the dataset, combining:
  1. Same cluster membership (fast pre-filter)
  2. Cosine similarity on the feature matrix (fine-grained ranking)

Usage (standalone):
    from competitor_analysis.similarity_engine import SimilarityEngine
    engine = SimilarityEngine.from_saved_model()
    results = engine.find_similar("Acme Corp", top_n=5)
"""

from __future__ import annotations

import os
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .clustering import (
    CLUSTER_MODEL_PATH,
    build_feature_matrix,
    load_cluster_model,
    predict_cluster,
)

# ---------------------------------------------------------------------------
# SimilarityEngine
# ---------------------------------------------------------------------------


class SimilarityEngine:
    """
    Encapsulates all state needed to answer "find competitors for startup X".

    Parameters
    ----------
    bundle : dict
        The pickle bundle produced by clustering.py (contains model, mlb,
        scaler, df with _cluster column, etc.)
    """

    def __init__(self, bundle: dict) -> None:
        self._bundle = bundle
        self._df: pd.DataFrame = bundle["df"].copy().reset_index(drop=True)

        # Pre-compute feature matrix for ALL startups once
        X_full, _, _, _ = build_feature_matrix(self._df)
        self._X_full: np.ndarray = X_full

        # Normalise rows so cosine similarity = dot product (faster at query time)
        norms = np.linalg.norm(self._X_full, axis=1, keepdims=True)
        norms[norms == 0] = 1.0  # avoid division by zero
        self._X_normed: np.ndarray = self._X_full / norms

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_saved_model(cls, path: str = CLUSTER_MODEL_PATH) -> "SimilarityEngine":
        bundle = load_cluster_model(path)
        if "df" not in bundle:
            raise ValueError(
                "Saved cluster bundle does not contain the dataframe. "
                "Re-run clustering.py so the df is embedded."
            )
        return cls(bundle)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_similar(
        self,
        company_name: str,
        top_n: int = 5,
        same_cluster_only: bool = True,
        exclude_self: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Return the top-N most similar startups to `company_name`.

        Parameters
        ----------
        company_name : str
            Must match the 'Company' column (case-insensitive, stripped).
        top_n : int
            Number of results to return.
        same_cluster_only : bool
            If True, restrict candidates to the same KMeans/DBSCAN cluster
            (faster; falls back to full search if cluster is too small).
        exclude_self : bool
            Whether to exclude the query startup itself from results.

        Returns
        -------
        List of dicts, each containing company metadata + similarity_score.
        """
        query_idx = self._resolve_company(company_name)
        return self._rank_similar(
            query_idx=query_idx,
            top_n=top_n,
            same_cluster_only=same_cluster_only,
            exclude_self=exclude_self,
        )

    def find_similar_by_features(
        self,
        startup_row: pd.Series,
        top_n: int = 5,
        same_cluster_only: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Find similar startups for a startup NOT in the dataset
        (e.g. a new submission via the API).

        Parameters
        ----------
        startup_row : pd.Series
            Must have columns: Categories, Year Founded, and at least one
            funding column.
        """
        # Build a 1-row feature vector using the fitted mlb + scaler
        df_single = startup_row.to_frame().T.reset_index(drop=True)
        from .clustering import _parse_categories, _extract_total_funding

        mlb = self._bundle["mlb"]
        scaler = self._bundle["scaler"]

        cat_lists = _parse_categories(df_single["Categories"])
        cat_matrix = mlb.transform(cat_lists)

        total_funding = _extract_total_funding(df_single).values.reshape(-1, 1)
        total_funding_log = np.log1p(total_funding)
        year = (
            pd.to_numeric(df_single["Year Founded"], errors="coerce")
            .fillna(2010)
            .values.reshape(-1, 1)
        )
        numeric_scaled = scaler.transform(np.hstack([total_funding_log, year]))
        x_query = np.hstack([cat_matrix, numeric_scaled])

        norm = np.linalg.norm(x_query)
        if norm > 0:
            x_query_normed = x_query / norm
        else:
            x_query_normed = x_query

        # Candidate pool
        if same_cluster_only:
            cluster_id = predict_cluster(startup_row, self._bundle)
            candidate_mask = self._df["_cluster"] == cluster_id
            if candidate_mask.sum() < top_n + 1:
                candidate_mask = pd.Series(True, index=self._df.index)
        else:
            candidate_mask = pd.Series(True, index=self._df.index)

        candidate_idxs = np.where(candidate_mask.values)[0]
        X_cands = self._X_normed[candidate_idxs]

        sims = (X_cands @ x_query_normed.T).flatten()
        sorted_local = np.argsort(sims)[::-1][:top_n]

        results = []
        for local_i in sorted_local:
            global_i = candidate_idxs[local_i]
            row = self._df.iloc[global_i]
            results.append(self._row_to_dict(row, float(sims[local_i])))
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_company(self, company_name: str) -> int:
        """Return integer index in self._df, or raise ValueError."""
        name_lower = company_name.strip().lower()
        matches = self._df[self._df["Company"].str.strip().str.lower() == name_lower]
        if matches.empty:
            # Fuzzy fallback: substring match
            matches = self._df[
                self._df["Company"].str.strip().str.lower().str.contains(
                    name_lower, regex=False
                )
            ]
        if matches.empty:
            raise ValueError(
                f"Company '{company_name}' not found in dataset. "
                "Use find_similar_by_features() for unknown startups."
            )
        return int(matches.index[0])

    def _rank_similar(
        self,
        query_idx: int,
        top_n: int,
        same_cluster_only: bool,
        exclude_self: bool,
    ) -> list[dict[str, Any]]:
        query_row = self._df.iloc[query_idx]
        x_query_normed = self._X_normed[query_idx : query_idx + 1]

        # Candidate pool
        if same_cluster_only and "_cluster" in self._df.columns:
            cluster_id = query_row["_cluster"]
            candidate_mask = self._df["_cluster"] == cluster_id
            # Fall back to full dataset if cluster is too small
            if candidate_mask.sum() < top_n + 2:
                candidate_mask = pd.Series(True, index=self._df.index)
        else:
            candidate_mask = pd.Series(True, index=self._df.index)

        candidate_idxs = np.where(candidate_mask.values)[0]
        X_cands = self._X_normed[candidate_idxs]

        sims = (X_cands @ x_query_normed.T).flatten()

        # Sort descending
        sorted_local = np.argsort(sims)[::-1]

        results = []
        for local_i in sorted_local:
            global_i = candidate_idxs[local_i]
            if exclude_self and global_i == query_idx:
                continue
            row = self._df.iloc[global_i]
            results.append(self._row_to_dict(row, float(sims[local_i])))
            if len(results) >= top_n:
                break

        return results

    @staticmethod
    def _row_to_dict(row: pd.Series, score: float) -> dict[str, Any]:
        """Serialize a DataFrame row + similarity score into a plain dict."""
        return {
            "company": row.get("Company", ""),
            "status": row.get("Satus", row.get("Status", "")),
            "year_founded": row.get("Year Founded", None),
            "categories": row.get("Categories", ""),
            "headquarters_city": row.get("Headquarters (City)", ""),
            "headquarters_country": row.get("Headquarters (Country)", ""),
            "description": row.get("Description", ""),
            "investors": row.get("Investors", ""),
            "cluster": int(row["_cluster"]) if "_cluster" in row.index else -1,
            "similarity_score": round(score, 4),
        }