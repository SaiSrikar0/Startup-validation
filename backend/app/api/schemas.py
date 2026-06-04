from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StartupBase(BaseModel):
    company: str = Field(..., min_length=1, max_length=200, description="Startup name")
    status: str = Field(..., min_length=1, max_length=50, description="Operating status")
    year_founded: int = Field(..., ge=1800, le=2100, description="Year founded")
    description: str = Field(..., min_length=1, max_length=5000, description="Startup description")
    categories: list[str] = Field(default_factory=list, description="Business categories")
    founders: list[str] = Field(default_factory=list, description="Founder names")
    investors: list[str] = Field(default_factory=list, description="Investor names")
    funding_rounds: list[str] = Field(default_factory=list, description="Funding amounts or round values")
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)


class StartupCreate(StartupBase):
    pass


class StartupUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = Field(default=None, min_length=1, max_length=50)
    year_founded: int | None = Field(default=None, ge=1800, le=2100)
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    categories: list[str] | None = None
    founders: list[str] | None = None
    investors: list[str] | None = None
    funding_rounds: list[str] | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)


class StartupRead(StartupBase):
    startup_id: str = Field(..., description="Stable API identifier")


class StartupListResponse(BaseModel):
    items: list[StartupRead]
    total: int
    limit: int
    offset: int


class HealthResponse(BaseModel):
    status: Literal["ok"]
    message: str
    total_startups: int


class SupabaseStatusResponse(BaseModel):
    available: bool
    details: str


class PredictionRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=200)
    categories: list[str] = Field(default_factory=list)
    founders: list[str] = Field(default_factory=list)
    investors: list[str] = Field(default_factory=list)
    year_founded: int | None = Field(default=None, ge=1800, le=2100)
    description: str | None = Field(default=None, max_length=5000)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=50)


class PredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    company: str
    predicted_success: bool
    probability: float = Field(..., ge=0.0, le=1.0)
    confidence: str
    factors: list[str]
    model_name: str = "heuristic-ann-placeholder"


class CompetitionAnalysisRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=200)
    categories: list[str] = Field(default_factory=list)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    top_n: int = Field(default=5, ge=1, le=20)


class CompetitionMatch(BaseModel):
    startup_id: str
    company: str
    score: float = Field(..., ge=0.0, le=1.0)
    shared_categories: list[str]
    reasoning: list[str]


class CompetitionAnalysisResponse(BaseModel):
    company: str
    top_matches: list[CompetitionMatch]
    total_candidates: int


class ErrorResponse(BaseModel):
    detail: str
    extra: dict[str, Any] | None = None
