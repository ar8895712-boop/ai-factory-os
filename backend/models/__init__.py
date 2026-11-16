# ==============================================================
# backend/models/__init__.py — Import all ORM models so
# Base.metadata sees them when create_all_tables() runs.
# ==============================================================

from backend.models.machine import Machine            # noqa: F401
from backend.models.sensor import Sensor              # noqa: F401
from backend.models.reading import Reading            # noqa: F401
from backend.models.prediction import Prediction      # noqa: F401
from backend.models.incident import Incident          # noqa: F401
from backend.models.maintenance_log import MaintenanceLog  # noqa: F401
from backend.models.user import User                  # noqa: F401
from backend.models.simulation_result import SimulationResult  # noqa: F401

__all__ = [
    "Machine",
    "Sensor",
    "Reading",
    "Prediction",
    "Incident",
    "MaintenanceLog",
    "User",
    "SimulationResult",
]

