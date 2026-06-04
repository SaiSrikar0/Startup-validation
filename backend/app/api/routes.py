from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response, status

from .schemas import (
    CompetitionAnalysisRequest,
    CompetitionAnalysisResponse,
    ErrorResponse,
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
    StartupCreate,
    StartupListResponse,
    StartupRead,
    StartupUpdate,
    SupabaseStatusResponse,
)
from .store import store
from ..supabase_client import get_supabase_status

router = APIRouter(prefix="/api", tags=["Startup Analysis"])


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Health check",
)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", message="Backend API is ready", total_startups=len(store.list()))


@router.get(
    "/supabase-status",
    response_model=SupabaseStatusResponse,
    summary="Check Supabase connectivity",
)
def supabase_status() -> SupabaseStatusResponse:
    return SupabaseStatusResponse(**get_supabase_status())


@router.get(
    "/startups",
    response_model=StartupListResponse,
    responses={500: {"model": ErrorResponse}},
    summary="List startups",
)
def list_startups(
    status_filter: str | None = Query(default=None, alias="status"),
    category: str | None = Query(default=None),
    country: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> StartupListResponse:
    items, total = store.search(
        status=status_filter,
        category=category,
        country=country,
        limit=limit,
        offset=offset,
    )
    return StartupListResponse(
        items=[item.to_read_model() for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/startups/{startup_id}",
    response_model=StartupRead,
    responses={404: {"model": ErrorResponse}},
    summary="Get startup by id",
)
def get_startup(startup_id: str) -> StartupRead:
    record = store.get(startup_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Startup '{startup_id}' not found")
    return record.to_read_model()


@router.post(
    "/startups",
    response_model=StartupRead,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
    summary="Create startup",
)
def create_startup(payload: StartupCreate) -> StartupRead:
    return store.add(payload).to_read_model()


@router.put(
    "/startups/{startup_id}",
    response_model=StartupRead,
    responses={404: {"model": ErrorResponse}},
    summary="Update startup",
)
def update_startup(startup_id: str, payload: StartupUpdate) -> StartupRead:
    record = store.update(startup_id, payload)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Startup '{startup_id}' not found")
    return record.to_read_model()


@router.delete(
    "/startups/{startup_id}",
    status_code=status.HTTP_200_OK,
    response_class=Response,
    responses={404: {"model": ErrorResponse}},
    summary="Delete startup",
)
def delete_startup(startup_id: str) -> Response:
    if not store.delete(startup_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Startup '{startup_id}' not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/predict/success",
    response_model=PredictionResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Predict startup success",
)
def predict_success(payload: PredictionRequest) -> PredictionResponse:
    return store.predict(payload)


@router.post(
    "/analysis/competition",
    response_model=CompetitionAnalysisResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Run competition analysis",
)
def competition_analysis(payload: CompetitionAnalysisRequest) -> CompetitionAnalysisResponse:
    return store.analyze_competition(payload)
