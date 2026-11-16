# ==============================================================
# ml/leakage_check.py — Data Leakage Assertion Utility
# ==============================================================
"""
Provides strict assertion checks to guarantee zero data leakage
across engine-level data splits in C-MAPSS and factory datasets.

Why this matters for your viva:
    Engine degradation is a continuous time-series process.
    If engine cycles are randomly split into train and test sets by row,
    the model memorises the future cycles of the *same* engine it is tested on.
    This creates an illusion of high accuracy that immediately fails in the real world.
    Splitting strictly by ENGINE ID ensures the model is evaluated exclusively on
    completely unseen physical machines.
"""

from __future__ import annotations

from typing import Iterable, Set


def check_engine_leakage(
    train_ids: Iterable[int],
    val_ids: Iterable[int],
    demo_ids: Iterable[int],
    test_ids: Iterable[int] | None = None,
) -> None:
    """
    Asserts that no engine ID is shared between train, val, demo, and test sets.

    Raises:
        AssertionError: If any intersection of engine IDs is detected.
    """
    s_train: Set[int] = set(train_ids)
    s_val: Set[int] = set(val_ids)
    s_demo: Set[int] = set(demo_ids)
    s_test: Set[int] = set(test_ids) if test_ids is not None else set()

    # Pairwise disjoint checks
    train_val_overlap = s_train.intersection(s_val)
    assert not train_val_overlap, (
        f"🚨 DATA LEAKAGE DETECTED: {len(train_val_overlap)} engines overlap between "
        f"TRAIN and VALIDATION: {sorted(train_val_overlap)}"
    )

    train_demo_overlap = s_train.intersection(s_demo)
    assert not train_demo_overlap, (
        f"🚨 DATA LEAKAGE DETECTED: {len(train_demo_overlap)} engines overlap between "
        f"TRAIN and DEMO-HOLDOUT: {sorted(train_demo_overlap)}"
    )

    val_demo_overlap = s_val.intersection(s_demo)
    assert not val_demo_overlap, (
        f"🚨 DATA LEAKAGE DETECTED: {len(val_demo_overlap)} engines overlap between "
        f"VALIDATION and DEMO-HOLDOUT: {sorted(val_demo_overlap)}"
    )

    if s_test:
        train_test_overlap = s_train.intersection(s_test)
        assert not train_test_overlap, (
            f"🚨 DATA LEAKAGE DETECTED: {len(train_test_overlap)} engines overlap between "
            f"TRAIN and TEST: {sorted(train_test_overlap)}"
        )
        val_test_overlap = s_val.intersection(s_test)
        assert not val_test_overlap, (
            f"🚨 DATA LEAKAGE DETECTED: {len(val_test_overlap)} engines overlap between "
            f"VALIDATION and TEST: {sorted(val_test_overlap)}"
        )
        demo_test_overlap = s_demo.intersection(s_test)
        assert not demo_test_overlap, (
            f"🚨 DATA LEAKAGE DETECTED: {len(demo_test_overlap)} engines overlap between "
            f"DEMO-HOLDOUT and TEST: {sorted(demo_test_overlap)}"
        )

    print(f"🔒 Leakage Check Passed: {len(s_train)} Train, {len(s_val)} Val, "
          f"{len(s_demo)} Demo, {len(s_test)} Test engines are 100% mutually disjoint.")

