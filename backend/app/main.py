from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyze, auth, cases, meta
from app.core.config import settings
from app.data.seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure schema exists and the demo case is present on boot.
    seed()
    yield


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta.router)
app.include_router(cases.router)
app.include_router(analyze.router)
app.include_router(auth.router)


@app.get("/")
def root():
    return {"app": settings.APP_NAME, "docs": "/docs", "health": "/api/health"}
