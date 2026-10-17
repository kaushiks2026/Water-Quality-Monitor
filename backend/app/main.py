import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.database.session import init_db
from backend.app.api.endpoints import router as sensor_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB tables
    init_db()
    print(f"[{settings.APP_NAME}] Database initialized at {settings.DATABASE_URL}")
    yield
    # Shutdown logic (if any)


app = FastAPI(
    title=settings.APP_NAME,
    description="Automated Water Quality Monitoring & Early-Warning Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local web dashboard and cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ingest and Telemetry API Router
app.include_router(sensor_router, prefix="/api")


@app.get("/health", tags=["System Health"])
def health_check():
    """
    Standard health check endpoint to verify backend service operational status.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "database": settings.DATABASE_URL.split("///")[-1]
    }


# Mount frontend static directory so navigating to http://localhost:8000/ serves the web dashboard
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
