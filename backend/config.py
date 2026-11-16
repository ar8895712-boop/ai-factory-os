# ==============================================================
# backend/config.py — Load config.yaml into a typed Pydantic model
# ==============================================================
"""
Central configuration loader.  Reads config.yaml once at startup and
exposes a typed `Settings` object that every other module imports.

Usage:
    from backend.config import get_settings
    cfg = get_settings()
    print(cfg.business.loss_per_hour)  # 150000
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

# ── Locate project root (the folder containing config.yaml) ──────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


# ── Nested Pydantic sub-models ───────────────────────────────────────

class MachineConfig(BaseModel):
    """One row from config.yaml → machines[]."""
    id: int
    name: str
    type: str
    location: str
    demo_engine_id: Optional[int] = None


class DataSplitConfig(BaseModel):
    total_train_engines: int = 100
    train_count: int = 70
    val_count: int = 15
    demo_count: int = 15
    window_size: int = 30
    rul_clip: int = 125


class HealthScoreConfig(BaseModel):
    rul_weight: float = 0.50
    anomaly_weight: float = 0.30
    failure_weight: float = 0.20


class AlertThreshold(BaseModel):
    health_below: int
    rul_below: int
    anomaly_above: float


class AlertsConfig(BaseModel):
    warning: AlertThreshold
    critical: AlertThreshold


class BusinessConfig(BaseModel):
    currency: str = "INR"
    currency_symbol: str = "₹"
    loss_per_hour: float = 150_000
    planned_maintenance_cost_per_hour: float = 30_000
    energy_tariff_per_kwh: float = 8.50
    machine_power_kw: float = 75
    idle_power_fraction: float = 0.15
    delay_penalty_per_hour: float = 50_000
    daily_production_target: int = 1000
    avg_spare_part_cost: float = 25_000
    emergency_markup: float = 2.5
    technician_hourly_rate: float = 800
    overtime_multiplier: float = 1.5


class SelfHealingAction(BaseModel):
    name: str
    description: str
    speed_reduction: Optional[float] = None
    rul_extension_factor: Optional[float] = None
    min_target_health: Optional[int] = None
    response_time_minutes: Optional[int] = None
    lead_time_hours: Optional[int] = None


class SelfHealingConfig(BaseModel):
    actions: List[SelfHealingAction]


class SimulatorConfig(BaseModel):
    default_sim_hours: int = 168
    machine_mtbf_hours: int = 500
    repair_time_hours: int = 4
    production_rate_per_hour: int = 42


class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_tokens: int = 1024
    system_prompt: str = ""


class EmbeddingsConfig(BaseModel):
    model_name: str = "all-MiniLM-L6-v2"
    faiss_index_path: str = "data/models/incident_index.faiss"
    similarity_top_k: int = 5


class WebSocketConfig(BaseModel):
    broadcast_interval_ms: int = 1000
    max_connections: int = 50


# ── Top-level Settings ──────────────────────────────────────────────

class Settings(BaseModel):
    """
    Complete application settings parsed from config.yaml.
    Every sub-section is strongly typed so we catch config typos early.
    """
    random_seed: int = 42
    database_url: str = "sqlite:///./data/factory.db"
    log_level: str = "INFO"

    machines: List[MachineConfig] = Field(default_factory=list)
    data_splits: DataSplitConfig = Field(default_factory=DataSplitConfig)
    health_score: HealthScoreConfig = Field(default_factory=HealthScoreConfig)
    alerts: AlertsConfig = Field(default_factory=lambda: AlertsConfig(
        warning=AlertThreshold(health_below=60, rul_below=50, anomaly_above=0.7),
        critical=AlertThreshold(health_below=30, rul_below=20, anomaly_above=0.9),
    ))
    business: BusinessConfig = Field(default_factory=BusinessConfig)
    self_healing: SelfHealingConfig = Field(
        default_factory=lambda: SelfHealingConfig(actions=[])
    )
    simulator: SimulatorConfig = Field(default_factory=SimulatorConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    websocket: WebSocketConfig = Field(default_factory=WebSocketConfig)


def _find_config_file() -> Path:
    """
    Resolve config file path in priority order:
    1. Explicit CONFIG_PATH env var (if exists)
    2. PROJECT_ROOT / 'config.yaml' (local customized configuration)
    3. PROJECT_ROOT / 'config.example.yaml' (production fallback if config.yaml is gitignored)
    """
    env_path = os.getenv("CONFIG_PATH")
    if env_path:
        p = Path(env_path)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        if p.exists():
            return p

    default_path = PROJECT_ROOT / "config.yaml"
    if default_path.exists():
        return default_path

    example_path = PROJECT_ROOT / "config.example.yaml"
    if example_path.exists():
        return example_path

    raise FileNotFoundError(
        f"Config file not found. Looked for {env_path or default_path} and {example_path}"
    )


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Read and parse YAML config file."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Singleton loader. Reads config file once per process lifetime.
    Falls back to config.example.yaml if config.yaml is not present.
    Environment variables (e.g. DATABASE_URL, LOG_LEVEL) override YAML values.
    """
    config_path = _find_config_file()
    raw: Dict[str, Any] = _load_yaml(config_path)

    # Allow environment variable overrides in cloud deployments
    if os.getenv("DATABASE_URL"):
        raw["database_url"] = os.getenv("DATABASE_URL")
    if os.getenv("LOG_LEVEL"):
        raw["log_level"] = os.getenv("LOG_LEVEL")

    return Settings(**raw)


# ── Quick sanity check when run directly ─────────────────────────────
if __name__ == "__main__":
    cfg = get_settings()
    print(f"✅ Config loaded — {len(cfg.machines)} machines defined")
    print(f"   Database : {cfg.database_url}")
    print(f"   Seed     : {cfg.random_seed}")
    print(f"   Loss/hr  : {cfg.business.currency_symbol}{cfg.business.loss_per_hour:,.0f}")

