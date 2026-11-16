# ==============================================================
# tests/test_health_score.py — Health Score & Alert Logic Tests
# ==============================================================
import pytest
from backend.config import get_settings
from backend.ml.inference import MLInferenceEngine


@pytest.fixture
def ml_engine():
    return MLInferenceEngine()


def test_health_score_weights_sum_to_one():
    """Validates that weights in config.yaml sum to 1.0."""
    cfg = get_settings().health_score
    total_weight = cfg.rul_weight + cfg.anomaly_weight + cfg.failure_weight
    assert pytest.approx(total_weight, 0.001) == 1.0


def test_pristine_machine_health_score(ml_engine):
    """Pristine machine with max RUL and near-zero anomaly should have health > 90 and normal status."""
    health, alert = ml_engine.compute_health_score(
        rul_pred=125.0,
        anomaly_score=0.02,
        failure_prob=0.01,
    )
    assert health >= 90.0
    assert alert == "normal"


def test_warning_alert_triggered(ml_engine):
    """Degraded RUL below warning threshold should trigger warning alert."""
    health, alert = ml_engine.compute_health_score(
        rul_pred=45.0,       # below warn.rul_below (50)
        anomaly_score=0.35,
        failure_prob=0.30,
    )
    assert alert in ("warning", "critical")
    assert health < 70.0


def test_critical_alert_triggered(ml_engine):
    """Low RUL and high anomaly score should trigger critical alert."""
    health, alert = ml_engine.compute_health_score(
        rul_pred=10.0,       # below crit.rul_below (20)
        anomaly_score=0.95,  # above crit.anomaly_above (0.9)
        failure_prob=0.90,
    )
    assert alert == "critical"
    assert health <= 30.0


def test_health_score_bounds(ml_engine):
    """Health score should be strictly bounded between 0.0 and 100.0."""
    h_min, _ = ml_engine.compute_health_score(0.0, 1.0, 1.0)
    h_max, _ = ml_engine.compute_health_score(200.0, 0.0, 0.0)
    assert 0.0 <= h_min <= 100.0
    assert 0.0 <= h_max <= 100.0
    assert h_min == 0.0
    assert h_max == 100.0

