"""
competitor_endpoint.py
======================
FastAPI router that exposes:

  GET  /competitors?company=<name>&top_n=<int>
  POST /competitors/by-features

Mount this in member1_api/main.py:
    from competitor_analysis.competitor_endpoint import router as competitor_router
    app.include_router(competitor_router, prefix="/competitors", tags=["competitors"])
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from .clustering import CLUSTER_MODEL_PATH
from .similarity_engine import SimilarityEngine

router = APIRouter()

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CompetitorResult(BaseModel):
    company: str
    status: str
    year_founded: Optional[Any] = None
    categories: str
    headquarters_city: str
    headquarters_country: str
    description: str
    investors: str
    cluster: int
    similarity_score: float


class CompetitorResponse(BaseModel):
    query_company: str
    top_n: int
    results: list[CompetitorResult]


class StartupFeaturesRequest(BaseModel):
    """Payload for finding competitors for a startup NOT in the dataset."""

    company_name: str = Field(..., example="My New Startup")
    categories: str = Field(..., example="SaaS, FinTech")
    year_founded: Optional[int] = Field(None, example=2022)
    total_funding: Optional[float] = Field(
        None, description="Total USD raised (raw number)", example=5_000_000
    )
    headquarters_city: Optional[str] = Field(None, example="Hyderabad")
    headquarters_country: Optional[str] = Field(None, example="India")
    top_n: int = Field(5, ge=1, le=50)


class ByFeaturesResponse(BaseModel):
    query_company: str
    top_n: int
    results: list[CompetitorResult]


# ---------------------------------------------------------------------------
# Dependency: cached SimilarityEngine
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _get_engine() -> SimilarityEngine:
    """Load the cluster model once and cache it for the lifetime of the process."""
    model_path = os.environ.get("CLUSTER_MODEL_PATH", CLUSTER_MODEL_PATH)
    try:
        return SimilarityEngine.from_saved_model(path=model_path)
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Cluster model not found: {exc}. "
            "Please train the model first by running: "
            "python -m competitor_analysis.clustering --data <path/to/Startups.csv>"
        ) from exc


def get_engine() -> SimilarityEngine:
    return _get_engine()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("", response_model=CompetitorResponse, summary="Find competitors by company name")
def get_competitors(
    company: str = Query(..., description="Exact or partial company name from the dataset"),
    top_n: int = Query(5, ge=1, le=50, description="Number of similar startups to return"),
    same_cluster_only: bool = Query(
        True,
        description="Restrict candidates to same cluster for speed (falls back automatically)",
    ),
    engine: SimilarityEngine = Depends(get_engine),
) -> CompetitorResponse:
    """
    Return the top-N most similar startups (competitors) for a given company
    that exists in the Startups dataset.
    """
    try:
        results = engine.find_similar(
            company_name=company,
            top_n=top_n,
            same_cluster_only=same_cluster_only,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc

    return CompetitorResponse(
        query_company=company,
        top_n=top_n,
        results=[CompetitorResult(**r) for r in results],
    )


@router.post(
    "/by-features",
    response_model=ByFeaturesResponse,
    summary="Find competitors for a new (unseen) startup",
)
def get_competitors_by_features(
    payload: StartupFeaturesRequest,
    engine: SimilarityEngine = Depends(get_engine),
) -> ByFeaturesResponse:
    """
    Find competitors for a startup that is **not** in the training dataset.
    Accepts raw features and returns the most similar known startups.
    """
    # Build a Series that mirrors the dataset columns
    funding_col_name = "Amounts raised in different funding rounds"
    startup_row = pd.Series(
        {
            "Company": payload.company_name,
            "Categories": payload.categories,
            "Year Founded": payload.year_founded or 2020,
            funding_col_name: payload.total_funding or 0,
            "Headquarters (City)": payload.headquarters_city or "",
            "Headquarters (Country)": payload.headquarters_country or "",
        }
    )

    try:
        results = engine.find_similar_by_features(
            startup_row=startup_row,
            top_n=payload.top_n,
            same_cluster_only=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc

    return ByFeaturesResponse(
        query_company=payload.company_name,
        top_n=payload.top_n,
        results=[CompetitorResult(**r) for r in results],
    )


@router.get(
    "/clusters/summary",
    summary="Summary statistics for each cluster",
)
def cluster_summary(
    engine: SimilarityEngine = Depends(get_engine),
) -> dict:
    """
    Returns per-cluster counts, top categories, and average year founded.
    Useful for understanding the segmentation produced by the model.
    """
    df = engine._df.copy()

    if "_cluster" not in df.columns:
        raise HTTPException(status_code=500, detail="Cluster labels not found in bundle.")

    summary = {}
    for cluster_id, group in df.groupby("_cluster"):
        top_cats = (
            group["Categories"]
            .fillna("")
            .str.split(",")
            .explode()
            .str.strip()
            .value_counts()
            .head(5)
            .to_dict()
        )
        summary[int(cluster_id)] = {
            "count": len(group),
            "avg_year_founded": round(
                pd.to_numeric(group["Year Founded"], errors="coerce").mean(), 1
            ),
            "top_categories": top_cats,
            "sample_companies": group["Company"].head(5).tolist(),
        }

    return {"n_clusters": len(summary), "clusters": summary}