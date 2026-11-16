# ==============================================================
# ml/data_loader.py — C-MAPSS & AI4I Dataset Loader
# ==============================================================
"""
Handles dataset loading, engine-level splits (70/15/15), sensor filtering,
and RUL label generation with piecewise linear clipping (max 125).

Global Rules Enforced:
1. Fixed random seed = 42.
2. Engine-level splits (never random row splits).
3. Leakage assertion before returning.
4. Splits saved to data/splits.json.
5. Array/DataFrame shapes printed at every step.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from ml.leakage_check import check_engine_leakage

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_SPLITS_PATH = PROJECT_ROOT / "data" / "splits.json"

# Column specifications for NASA C-MAPSS
INDEX_COLS = ["engine_id", "cycle"]
SETTING_COLS = ["setting1", "setting2", "setting3"]
SENSOR_COLS = [f"s{i}" for i in range(1, 22)]
ALL_CMAPSS_COLS = INDEX_COLS + SETTING_COLS + SENSOR_COLS

# Sensors with zero or near-zero variance in FD001 (useless for degradation tracking)
CONSTANT_SENSORS = ["s1", "s5", "s10", "s16", "s18", "s19"]
USEFUL_SENSORS = [s for s in SENSOR_COLS if s not in CONSTANT_SENSORS]

RUL_CLIP = 125
RANDOM_SEED = 42


def load_cmapss_raw() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads raw C-MAPSS FD001 text files.
    Returns:
        (train_df, test_df, rul_df)
    """
    train_path = DATA_RAW / "train_FD001.txt"
    test_path = DATA_RAW / "test_FD001.txt"
    rul_path = DATA_RAW / "RUL_FD001.txt"

    assert train_path.exists(), f"Missing {train_path}"
    assert test_path.exists(), f"Missing {test_path}"
    assert rul_path.exists(), f"Missing {rul_path}"

    train_df = pd.read_csv(train_path, sep=r"\s+", header=None, names=ALL_CMAPSS_COLS)
    test_df = pd.read_csv(test_path, sep=r"\s+", header=None, names=ALL_CMAPSS_COLS)
    rul_df = pd.read_csv(rul_path, sep=r"\s+", header=None, names=["true_rul"])

    print(f"📊 [Data Loader] Loaded raw C-MAPSS:")
    print(f"   train_FD001 shape : {train_df.shape} ({train_df['engine_id'].nunique()} engines)")
    print(f"   test_FD001 shape  : {test_df.shape} ({test_df['engine_id'].nunique()} engines)")
    print(f"   RUL_FD001 shape   : {rul_df.shape} (true RUL for test engines)")

    return train_df, test_df, rul_df


def add_piecewise_rul(df: pd.DataFrame, clip_val: int = RUL_CLIP) -> pd.DataFrame:
    """
    Calculates Remaining Useful Life (RUL) for engines that run to failure.
    RUL = max_cycle - current_cycle, clipped at clip_val (125).

    Why piecewise clipping (125)?
    In early engine life, there is no detectable physical wear. Degradation
    signatures only begin emerging after healthy break-in. Capping RUL at 125
    prevents the model from trying to predict meaningless arbitrary numbers
    when sensors are in pristine condition.
    """
    max_cycles = df.groupby("engine_id")["cycle"].max().reset_index()
    max_cycles.rename(columns={"cycle": "max_cycle"}, inplace=True)
    df = df.merge(max_cycles, on="engine_id", how="left")
    df["rul_raw"] = df["max_cycle"] - df["cycle"]
    df["rul"] = np.minimum(df["rul_raw"], clip_val)
    df.drop(columns=["max_cycle", "rul_raw"], inplace=True)
    return df


def get_engine_splits(
    total_engines: int = 100,
    train_n: int = 70,
    val_n: int = 15,
    demo_n: int = 15,
    seed: int = RANDOM_SEED,
) -> Dict[str, List[int]]:
    """
    Splits engine IDs into Train, Val, and Demo-Holdout sets.
    Never shuffles row data; strictly splits whole engine trajectories.
    """
    assert train_n + val_n + demo_n == total_engines, "Splits must sum to total engines."

    rng = np.random.RandomState(seed)
    engine_ids = np.arange(1, total_engines + 1)
    shuffled = rng.permutation(engine_ids)

    train_ids = sorted(shuffled[:train_n].tolist())
    val_ids = sorted(shuffled[train_n : train_n + val_n].tolist())
    demo_ids = sorted(shuffled[train_n + val_n :].tolist())

    # Verify zero leakage
    check_engine_leakage(train_ids, val_ids, demo_ids)

    splits = {
        "train_engines": train_ids,
        "val_engines": val_ids,
        "demo_engines": demo_ids,
    }

    # Save to disk
    DATA_SPLITS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_SPLITS_PATH, "w", encoding="utf-8") as f:
        json.dump(splits, f, indent=2)

    print(f"💾 Saved engine splits to {DATA_SPLITS_PATH.name}:")
    print(f"   Train engines ({len(train_ids)}): {train_ids[:8]} ...")
    print(f"   Val engines   ({len(val_ids)}): {val_ids[:8]} ...")
    print(f"   Demo engines  ({len(demo_ids)}): {demo_ids[:8]} ...")

    return splits


def get_cmapss_splits() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads C-MAPSS and returns partitioned DataFrames with computed RUL:
    Returns:
        (train_df, val_df, demo_df, test_df, rul_df)
    """
    train_raw, test_df, rul_df = load_cmapss_raw()
    train_with_rul = add_piecewise_rul(train_raw)

    splits = get_engine_splits()
    train_ids = splits["train_engines"]
    val_ids = splits["val_engines"]
    demo_ids = splits["demo_engines"]

    # Filter columns: keep only index + useful sensors + rul
    feature_cols = INDEX_COLS + USEFUL_SENSORS + ["rul"]

    train_split = train_with_rul[train_with_rul["engine_id"].isin(train_ids)][feature_cols].copy()
    val_split = train_with_rul[train_with_rul["engine_id"].isin(val_ids)][feature_cols].copy()
    demo_split = train_with_rul[train_with_rul["engine_id"].isin(demo_ids)][feature_cols].copy()

    test_features = INDEX_COLS + USEFUL_SENSORS
    test_split = test_df[test_features].copy()

    print(f"📐 [Shapes after Engine-Level Split]:")
    print(f"   train_split shape : {train_split.shape} (from {len(train_ids)} engines)")
    print(f"   val_split shape   : {val_split.shape} (from {len(val_ids)} engines)")
    print(f"   demo_split shape  : {demo_split.shape} (from {len(demo_ids)} engines)")
    print(f"   test_split shape  : {test_split.shape} (from {test_split['engine_id'].nunique()} engines)")
    print(f"   Active sensors (14) : {USEFUL_SENSORS}")

    return train_split, val_split, demo_split, test_split, rul_df


def load_ai4i() -> pd.DataFrame:
    """
    Loads UCI AI4I 2020 Predictive Maintenance dataset.
    """
    ai4i_path = DATA_RAW / "ai4i2020.csv"
    assert ai4i_path.exists(), f"Missing {ai4i_path}"
    df = pd.read_csv(ai4i_path)
    print(f"📊 [AI4I 2020] Loaded dataset shape: {df.shape}")
    return df

