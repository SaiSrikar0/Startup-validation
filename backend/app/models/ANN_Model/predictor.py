"""
ANN prediction service used by the unified /api/predict/success endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from .ann_model import load_model
from .feature_engineering import StartupFeatureEngineer

if TYPE_CHECKING:
    from ...api.schemas import PredictionRequest, PredictionResponse

_fe: StartupFeatureEngineer | None = None
_model = None
THRESHOLD = 0.5


def _confidence(prob: float) -> str:
    if prob >= 0.80 or prob <= 0.20:
        return "high"
    if prob >= 0.65 or prob <= 0.35:
        return "medium"
    return "low"


def _load_artifacts() -> None:
    global _fe, _model
    if _fe is None:
        _fe = StartupFeatureEngineer.load()
    if _model is None:
        _model = load_model()


def is_available() -> bool:
    try:
        _load_artifacts()
        return True
    except Exception:
        return False


def _request_to_dataframe(payload: "PredictionRequest") -> pd.DataFrame:
    row = {
        "Company": payload.company,
        "Satus": payload.status or "Unknown",
        "Year Founded": payload.year_founded or 2015,
        "Description": payload.description or "",
        "Categories": ", ".join(payload.categories),
        "Founders": ", ".join(payload.founders),
        "Investors": ", ".join(payload.investors),
        "Amounts raised in different funding rounds": "",
        "Headquarters (City)": payload.city or "",
        "Headquarters (US State)": payload.state or "",
        "Headquarters (Country)": payload.country or "",
    }
    return pd.DataFrame([row])


def _build_factors(payload: "PredictionRequest", prob: float, label: str) -> list[str]:
    factors = [
        f"TensorFlow ANN success probability: {prob:.1%}",
        f"Model verdict: {label}",
    ]
    if payload.status:
        factors.append(f"Status: {payload.status}")
    if payload.categories:
        factors.append(f"Categories: {', '.join(payload.categories)}")
    if payload.founders:
        factors.append(f"Founders on team: {len(payload.founders)}")
    if payload.investors:
        factors.append(f"Investors listed: {len(payload.investors)}")
    if payload.country:
        factors.append(f"Headquarters country: {payload.country}")
    return factors


def predict_with_ann(payload: "PredictionRequest") -> "PredictionResponse":
    from ...api.schemas import PredictionResponse

    _load_artifacts()
    df = _request_to_dataframe(payload)
    features = _fe.transform(df)
    prob = float(_model.predict(features, verbose=0)[0][0])
    label = "Success" if prob >= THRESHOLD else "Failure"

    return PredictionResponse(
        company=payload.company,
        predicted_success=prob >= THRESHOLD,
        probability=round(prob, 4),
        confidence=_confidence(prob),
        factors=_build_factors(payload, prob, label),
        model_name="tensorflow-ann",
    )
