import asyncio
from contextlib import (
    asynccontextmanager,
    suppress,
)
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.services.automatic_sync_service import (
    automatic_resource_sync,
)
from app.api.role_access import router as role_access_router
from app.api.aws_resources import router as aws_router
from app.api.users import router as users_router
from app.api.anomalies import router as anomalies_router
from app.database import get_db
from app.core.config import settings
from app.api.dashboard import router as dashboard_router
from app.api.cost_forecast import router as cost_forecast_router
from app.api.cost_dataset import router as cost_dataset_router
from app.api.optimization import router as optimization_router
from app.api.costs import router as costs_router
from app.api.monitoring import router as monitoring_router
from app.api.resources import router as resources_router
from app.api.ml_data import router as ml_data_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    sync_task = asyncio.create_task(
        automatic_resource_sync()
    )

    try:
        yield

    finally:
        sync_task.cancel()

        with suppress(
            asyncio.CancelledError
        ):
            await sync_task
# STEP 1: Sabse pehle FastAPI application create hogi
app = FastAPI(
    title="CloudCampus AI API",
    description=(
        "Backend API for cloud lab "
        "governance and monitoring"
    ),
    version="0.1.0",
    lifespan=lifespan,
)
# React frontend ko backend APIs access karne dena
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        settings.frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# STEP 3: Application create hone ke baad routers connect honge
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(role_access_router)
app.include_router(aws_router)
app.include_router(cost_forecast_router)
app.include_router(anomalies_router)
app.include_router(dashboard_router)
app.include_router(resources_router)
app.include_router(cost_dataset_router) 
app.include_router(monitoring_router)
app.include_router(costs_router)
app.include_router(optimization_router)
app.include_router(ml_data_router)

# Root endpoint
@app.get(
    "/",
    tags=["System"]
)
def root():
    return {
        "message": "CloudCampus AI backend is running"
    }


# Backend health-check endpoint
@app.get(
    "/api/health",
    tags=["System"]
)
def health_check():
    return {
        "status": "healthy",
        "service": "cloudcampus-backend",
        "version": "0.1.0"
    }


# MySQL connection health-check endpoint
@app.get(
    "/api/health/database",
    tags=["System"]
)
def database_health_check(
    db: Session = Depends(get_db)
):
    result = db.execute(
        text("SELECT 1")
    ).scalar()

    return {
        "status": "healthy",
        "database": "mysql",
        "connection_test": result
    }
