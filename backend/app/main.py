from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router

app = FastAPI(
    title="Startup Validation API",
    version="0.1.0",
    description="FastAPI backend for startup analysis, CRUD, prediction, and competition insights.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {"message": "Startup Validation API is running"}
