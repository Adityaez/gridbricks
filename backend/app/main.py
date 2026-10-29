"""Main entrypoint for FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Day-Ahead Wind Forecast Intelligence for UK Electricity Procurement desk (January 2026 Historical Pilot)",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for local development and deployed frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "WindSight API is operational. Visit /docs for OpenAPI documentation.",
        "version": settings.VERSION,
        "scope": f"{settings.START_DATE_LIMIT} to {settings.END_DATE_LIMIT}"
    }
