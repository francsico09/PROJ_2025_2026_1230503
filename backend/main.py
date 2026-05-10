from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import src.database.models

from seed import bootstrap
from src.core.session import engine
from src.database.base.base import Base
from src.modules.auth.controller.auth_controller import router as auth_router
from src.modules.metrics.controller.researcher_metric_controller import router as metrics_router
from src.modules.user.controller.user_controller import router as users_router
from src.modules.extraction.controller.extraction_controller import router as extraction_router
from src.modules.researcher_profile.controller.researcher_profile_controller import router as profile_controller
from src.modules.export.controller.export_controller import router as export_controller

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        print("Starting seeder")
        await bootstrap()
        print("Database successfully populated")
    except Exception as e:
        print(f"CRITICAL SEEDER ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    yield

app = FastAPI(
    title="Research Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://frontend:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,       prefix="/api/v1")
app.include_router(users_router,      prefix="/api/v1")
app.include_router(metrics_router,    prefix="/api/v1")
app.include_router(extraction_router, prefix="/api/v1")
app.include_router(profile_controller, prefix="/api/v1")
app.include_router(export_controller, prefix="/api/v1")