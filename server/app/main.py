import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import engine, Base, get_db
from app.schemas.base import HealthResponse, APIResponse
from app.seed import seed_database
from app.api.sos import router as sos_router
from app.api.tickets import router as tickets_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager: Runs on startup and shutdown."""
    print(f"[STARTUP] Initializing {settings.PROJECT_NAME} v{settings.VERSION}...")
    # Initialize SQLite database schema
    Base.metadata.create_all(bind=engine)
    # Seed demonstration data
    seed_database()
    yield
    print("[SHUTDOWN] TyphoonLink engine shutting down cleanly.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Mission-critical disaster dispatch and emergency triage engine for coastal cyclone corridors. "
        "Provides REST endpoints for citizen SOS beacons, offline-synced triage queues, and volunteer coordination."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware to support static Stitch prototype frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(sos_router, prefix="/api")
app.include_router(tickets_router, prefix="/api")


@app.get("/api/status", tags=["General"])
def root_status():
    """Root metadata and system status."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "online",
        "docs": "/docs",
        "notice": (
            "[DEMONSTRATION PLATFORM] TyphoonLink is a disaster response simulation prototype. "
            "All seeded shelter occupancies, water levels, and squad telemetry are simulated demonstration data."
        ),
    }


@app.get("/api/health", response_model=HealthResponse, tags=["General"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint: verifies SQLite database connection."""
    # Execute a lightweight probe query
    db.execute(text("SELECT 1"))
    return HealthResponse(
        status="operational",
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        database_connected=True,
        notice="[DEMONSTRATION PLATFORM] All seeded telemetry is simulated.",
    )


# Mount Static Frontend Prototype Directory for Unified All-in-One Deployment
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../stitch_typhoon_link_sos"))

favicon_path = os.path.join(frontend_dir, "favicon.ico")
if os.path.exists(favicon_path):
    @app.get("/favicon.ico", include_in_schema=False)
    def favicon():
        return FileResponse(favicon_path)

if os.path.exists(frontend_dir):
    @app.get("/", include_in_schema=False)
    def root_redirect():
        """Redirect root to the citizen emergency dispatcher prototype."""
        return RedirectResponse(url="/citizen_offline_sos_dispatcher_simplified/code.html")

    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
