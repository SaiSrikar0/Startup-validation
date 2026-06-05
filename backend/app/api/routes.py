from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from .supabase_store import (
    list_startups as supabase_list_startups,
    get_startup as supabase_get_startup,
    create_startup as supabase_create_startup,
    update_startup as supabase_update_startup,
    delete_startup as supabase_delete_startup,
    startup_create_to_db,
    startup_update_to_db,
)

from .schemas import (
    CompetitionAnalysisRequest,
    CompetitionAnalysisResponse,
    ErrorResponse,
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
    StartupCreate,
    StartupRead,
    StartupUpdate,
    SupabaseStatusResponse,
)

from .store import store
from ..supabase_client import get_supabase_status

router = APIRouter(prefix="/api", tags=["Startup Analysis"])


# -------------------------
# Health Check
# -------------------------
@router.get(
    "/health",
    response_model=HealthResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Health check",
)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        message="Backend API is ready",
        total_startups=len(supabase_list_startups()),
    )


# -------------------------
# GET ALL STARTUPS
# -------------------------
@router.get(
    "/supabase-status",
    response_model=SupabaseStatusResponse,
    summary="Check Supabase connectivity",
)
def supabase_status() -> SupabaseStatusResponse:
    return SupabaseStatusResponse(**get_supabase_status())


@router.get(
    "/startups",
    summary="List startups",
)
def list_startups():
    return supabase_list_startups()


# -------------------------
# GET STARTUP BY ID
# -------------------------
@router.get(
    "/startups/{startup_id}",
    summary="Get startup by id",
)
def get_startup(startup_id: int):

    startup = supabase_get_startup(startup_id)

    if startup is None:
        raise HTTPException(
            status_code=404,
            detail="Startup not found",
        )

    return startup


# -------------------------
# CREATE STARTUP
# -------------------------
@router.post(
    "/startups",
    response_model=StartupRead,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
    summary="Create startup",
)
def create_startup(payload: StartupCreate):

    db_data = startup_create_to_db(payload)

    startup = supabase_create_startup(db_data)

    if startup is None:
        raise HTTPException(
            status_code=400,
            detail="Failed to create startup",
        )

    return startup


# -------------------------
# UPDATE STARTUP
# -------------------------
@router.put(
    "/startups/{startup_id}",
    response_model=StartupRead,
    responses={404: {"model": ErrorResponse}},
    summary="Update startup",
)
def update_startup(startup_id: int, payload: StartupUpdate):

    updates = startup_update_to_db(payload)

    startup = supabase_update_startup(
        startup_id,
        updates,
    )

    if startup is None:
        raise HTTPException(
            status_code=404,
            detail="Startup not found",
        )

    return startup


# -------------------------
# DELETE STARTUP
# -------------------------
@router.delete(
    "/startups/{startup_id}",
    responses={404: {"model": ErrorResponse}},
    summary="Delete startup",
)
def delete_startup(startup_id: int):

    deleted = supabase_delete_startup(startup_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Startup not found",
        )

    return {
        "message": "Startup deleted successfully"
    }


# -------------------------
# SUCCESS PREDICTION
# -------------------------
@router.post(
    "/predict/success",
    response_model=PredictionResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Predict startup success",
)
def predict_success(payload: PredictionRequest) -> PredictionResponse:
    return store.predict(payload)


# -------------------------
# COMPETITION ANALYSIS
# -------------------------
@router.post(
    "/analysis/competition",
    response_model=CompetitionAnalysisResponse,
    responses={422: {"model": ErrorResponse}},
    summary="Run competition analysis",
)
def competition_analysis(
    payload: CompetitionAnalysisRequest,
) -> CompetitionAnalysisResponse:
    return store.analyze_competition(payload)