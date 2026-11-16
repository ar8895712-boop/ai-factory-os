# ==============================================================
# tests/test_leakage.py — Unit Tests for Data Leakage Prevention
# ==============================================================
import json
from pathlib import Path
import pytest
from ml.leakage_check import check_engine_leakage

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPLITS_PATH = PROJECT_ROOT / "data" / "splits.json"


def test_leakage_check_passes_on_disjoint_sets():
    """Asserts that disjoint engine ID sets pass without error."""
    train_ids = [1, 2, 3, 4]
    val_ids = [5, 6]
    demo_ids = [7, 8]
    test_ids = [9, 10]
    # Should not raise
    check_engine_leakage(train_ids, val_ids, demo_ids, test_ids)


def test_leakage_check_raises_on_train_val_overlap():
    """Asserts that overlap between train and val triggers AssertionError."""
    train_ids = [1, 2, 3, 4]
    val_ids = [4, 5, 6]  # 4 is shared
    demo_ids = [7, 8]
    with pytest.raises(AssertionError, match="DATA LEAKAGE DETECTED"):
        check_engine_leakage(train_ids, val_ids, demo_ids)


def test_leakage_check_raises_on_train_demo_overlap():
    """Asserts that overlap between train and demo triggers AssertionError."""
    train_ids = [1, 2, 3, 4]
    val_ids = [5, 6]
    demo_ids = [1, 7, 8]  # 1 is shared
    with pytest.raises(AssertionError, match="DATA LEAKAGE DETECTED"):
        check_engine_leakage(train_ids, val_ids, demo_ids)


def test_saved_splits_file_is_leakage_free():
    """Validates the persistent data/splits.json used across all project phases."""
    assert SPLITS_PATH.exists(), f"Missing {SPLITS_PATH}"
    with open(SPLITS_PATH, "r", encoding="utf-8") as f:
        splits = json.load(f)

    train_ids = splits["train_engines"]
    val_ids = splits["val_engines"]
    demo_ids = splits["demo_engines"]

    assert len(train_ids) == 70, f"Expected 70 train engines, got {len(train_ids)}"
    assert len(val_ids) == 15, f"Expected 15 val engines, got {len(val_ids)}"
    assert len(demo_ids) == 15, f"Expected 15 demo engines, got {len(demo_ids)}"

    # Check zero overlap
    check_engine_leakage(train_ids, val_ids, demo_ids)

