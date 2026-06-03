"""
Member 2 — /predict Endpoint
==============================
Standalone FastAPI app exposing the trained ANN.
Member 1 will mount this router inside the main API.

Run standalone (for testing):
    uvicorn predict_endpoint:app --reload --port 8001
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import numpy as np
import pandas as pd
from pathlib import Path

try:
    from utils.feature_engineering import StartupFeatureEngineer
    from utils.ann_model import load_model
except ModuleNotFoundError:
    from feature_engineering import StartupFeatureEngineer
    from ann_model import load_model


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class StartupInput(BaseModel):
    """
    Raw startup features exactly matching the dataset columns.
    All fields are optional so Member 1 can pass partial records.
    """
    company:        str              = Field(..., example="AcmeTech Inc.")
    status:         Optional[str]    = Field(None, example="Operating")
    year_founded:   Optional[int]    = Field(None, example=2018)
    description:    Optional[str]    = Field(None, example="B2B SaaS platform for logistics")
    categories:     Optional[str]    = Field(None, example="Enterprise Software, Logistics")
    founders:       Optional[str]    = Field(None, example="Alice Smith, Bob Jones")
    investors:      Optional[str]    = Field(None, example="Sequoia Capital, Y Combinator")
    funding_rounds: Optional[str]    = Field(None, example="$500K Seed, $3M Series A",
                                             alias="amounts_raised_in_different_funding_rounds")
    hq_city:        Optional[str]    = Field(None, example="San Francisco")
    hq_state:       Optional[str]    = Field(None, example="CA")
    hq_country:     Optional[str]    = Field(None, example="United States")

    class Config:
        populate_by_name = True


class PredictionResponse(BaseModel):
    company:          str
    success_probability: float = Field(..., description="0–1 probability of success")
    prediction:       str   = Field(..., description="'Success' or 'Failure'")
    confidence:       str   = Field(..., description="'High / Medium / Low'")
    threshold_used:   float = 0.5


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Startup ANN Prediction API",
    description="Member 2 — ANN model for startup success prediction",
    version="1.0.0",
)

# lazy-loaded singletons
_fe:    StartupFeatureEngineer | None = None
_model = None
THRESHOLD = 0.5


def _load_artifacts():
    global _fe, _model
    if _fe is None:
        _fe = StartupFeatureEngineer.load()
    if _model is None:
        _model = load_model()


def _confidence(prob: float) -> str:
    if prob >= 0.80 or prob <= 0.20:
        return "High"
    if prob >= 0.65 or prob <= 0.35:
        return "Medium"
    return "Low"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "module": "member2_ann"}


@app.post("/predict", response_model=PredictionResponse)
def predict(startup: StartupInput):
    """
    Predict success probability for a single startup.

    Member 1 calls this endpoint after fetching startup data from the DB.
    """
    try:
        _load_artifacts()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Model artifacts not available. Run train.py first. ({e})"
        )

    # ── Build a single-row DataFrame matching the raw CSV schema ─────────────
    row = {
        "Company":                                  startup.company,
        "Satus":                                    startup.status or "Unknown",
        "Year Founded":                             startup.year_founded or 2015,
        "Description":                              startup.description or "",
        "Categories":                               startup.categories or "",
        "Founders":                                 startup.founders or "",
        "Investors":                                startup.investors or "",
        "Amounts raised in different funding rounds": startup.funding_rounds or "",
        "Headquarters (City)":                      startup.hq_city or "",
        "Headquarters (US State)":                  startup.hq_state or "",
        "Headquarters (Country)":                   startup.hq_country or "",
    }
    df = pd.DataFrame([row])

    try:
        X = _fe.transform(df)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Feature engineering error: {e}")

    prob  = float(_model.predict(X, verbose=0)[0][0])
    label = "Success" if prob >= THRESHOLD else "Failure"

    return PredictionResponse(
        company=startup.company,
        success_probability=round(prob, 4),
        prediction=label,
        confidence=_confidence(prob),
        threshold_used=THRESHOLD,
    )


@app.post("/predict/batch", response_model=list[PredictionResponse])
def predict_batch(startups: list[StartupInput]):
    """Batch prediction for multiple startups."""
    return [predict(s) for s in startups]


# ── Run standalone ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("predict_endpoint:app", host="0.0.0.0", port=8001, reload=True)
