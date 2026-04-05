import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import init_db
from .routers import config, projects, workflow, execution


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Buildra API",
    description="AI Software Factory Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow all origins in development; restrict via CORS_ORIGINS env var in production
# e.g. CORS_ORIGINS=https://buildra.netlify.app,https://yourdomain.com
_raw_origins = os.getenv("CORS_ORIGINS", "")
allow_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(workflow.router, prefix="/api")
app.include_router(execution.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
