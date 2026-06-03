"""
ML-backed competition analysis for /api/analysis/competition.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import TYPE_CHECKING

import pandas as pd

from .clustering import CLUSTER_MODEL_PATH
from .similarity_engine import SimilarityEngine

if TYPE_CHECKING:
    from ..api.schemas import CompetitionAnalysisRequest, CompetitionAnalysisResponse
    from ..api.store import StartupStore


@lru_cache(maxsize=1)
def get_engine() -> SimilarityEngine:
    model_path = os.environ.get("CLUSTER_MODEL_PATH", CLUSTER_MODEL_PATH)
    return SimilarityEngine.from_saved_model(path=model_path)


def _shared_categories(record_categories: list[str], target: set[str]) -> list[str]:
    return sorted(
        category
        for category in record_categories
        if category.lower() in target
    )


def analyze_with_ml(
    payload: "CompetitionAnalysisRequest",
    store: "StartupStore",
) -> "CompetitionAnalysisResponse":
    from ..api.schemas import CompetitionAnalysisResponse, CompetitionMatch

    engine = get_engine()
    target_categories = {item.lower() for item in payload.categories}

    try:
        raw_results = engine.find_similar(
            payload.company,
            top_n=payload.top_n,
            same_cluster_only=False,
        )
    except ValueError:
        funding_col = "Amounts raised in different funding rounds"
        startup_row = pd.Series(
            {
                "Company": payload.company,
                "Categories": ", ".join(payload.categories),
                "Year Founded": 2020,
                funding_col: 0,
                "Headquarters (City)": payload.city or "",
                "Headquarters (Country)": payload.country or "",
            }
        )
        raw_results = engine.find_similar_by_features(
            startup_row=startup_row,
            top_n=payload.top_n,
            same_cluster_only=False,
        )

    matches: list[CompetitionMatch] = []
    for item in raw_results:
        record = store.find_by_company(item["company"])
        shared = (
            _shared_categories(record.categories, target_categories)
            if record
            else _shared_categories(
                [part.strip() for part in str(item.get("categories", "")).split(",") if part.strip()],
                target_categories,
            )
        )
        reasoning = [
            f"ML cosine similarity: {item['similarity_score']:.1%}",
            f"KMeans cluster: {item.get('cluster', 'n/a')}",
        ]
        if shared:
            reasoning.append(f"Shared categories: {', '.join(shared)}")
        if item.get("headquarters_country"):
            reasoning.append(f"Located in {item['headquarters_country']}")

        matches.append(
            CompetitionMatch(
                startup_id=record.startup_id if record else store.stable_id_for_company(item["company"]),
                company=item["company"],
                score=round(float(item["similarity_score"]), 4),
                shared_categories=shared,
                reasoning=reasoning,
            )
        )

    return CompetitionAnalysisResponse(
        company=payload.company,
        top_matches=matches,
        total_candidates=len(matches),
    )
