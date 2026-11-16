# ==============================================================
# backend/main.py — FastAPI application entry point
# ==============================================================
"""
Launches the AI Factory Operating System backend.
Mounts REST APIs, WebSocket streaming endpoints, and initializes
the Digital Twin simulation engine.

Run with:
    uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.database import create_all_tables
from backend.routers import alerts, business, chat, config_router, machines, simulation, websocket, whatif
from backend.services.factory_memory import get_factory_memory
from backend.simulation.engine import get_simulation_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle manager."""
    # ── Startup ───────────────────────────────────────────────────────
    cfg = get_settings()
    print(f"🏭 AI Factory OS starting — seed={cfg.random_seed}")
    create_all_tables()

    # Pre-load ML inference and initialize simulation engine
    engine = get_simulation_engine()
    print(f"✅ Digital Twin Engine loaded with {len(engine.machines_state)} machines.")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────
    print("🏭 AI Factory OS shutting down...")
    engine.pause()


app = FastAPI(
    title="AI Factory Operating System",
    description=(
        "Digital-twin platform for predictive maintenance. "
        "Combines ML models (RUL, anomaly, failure classification) with "
        "a real-time simulation engine, business impact calculator, "
        "self-healing rule engine, and Factory GPT assistant."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

# ── CORS Middleware ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include Routers ──────────────────────────────────────────────────
app.include_router(machines.router)
app.include_router(simulation.router)
app.include_router(alerts.router)
app.include_router(config_router.router)
app.include_router(business.router)      # Phase 4: Business Impact + Self-Healing
app.include_router(whatif.router)        # Phase 5: SimPy What-If Simulator
app.include_router(chat.router)          # Phase 6: Factory GPT + FAISS Memory
app.include_router(websocket.router)


# ── Health checks ─────────────────────────────────────────────────────
@app.get("/api/health", tags=["health"])
def health_check():
    """Detailed health check."""
    cfg = get_settings()
    engine = get_simulation_engine()
    return {
        "status": "healthy",
        "database": cfg.database_url.split("///")[0],
        "machines_configured": len(cfg.machines),
        "simulation_running": engine.is_running,
        "speed_factor": engine.speed_factor,
        "seed": cfg.random_seed,
    }


# ── Optional Production Frontend Static Serving ───────────────────────
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if DIST_DIR.exists() and (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(DIST_DIR / "index.html")
else:
    @app.get("/", tags=["health"])
    def root():
        """Root status endpoint."""
        return {
            "status": "ok",
            "project": "AI Factory Operating System",
            "version": "1.0.0",
            "phase": "Phase 7 (Production Ready — End-to-End Verified Capstone)",
        }
