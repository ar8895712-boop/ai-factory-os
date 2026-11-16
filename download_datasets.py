# ==============================================================
# download_datasets.py — Fetch C-MAPSS FD001 & AI4I 2020
# ==============================================================
"""
Downloads the two required datasets into data/raw/:
  1. NASA C-MAPSS FD001 (train, test, RUL files)
  2. UCI AI4I 2020 Predictive Maintenance Dataset

Run with network access:
    python download_datasets.py
"""

from __future__ import annotations

import io
import os
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request

RAW_DIR = Path(__file__).resolve().parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def download_file_direct(urls: list[str], dest: Path, desc: str) -> bool:
    """Download a file trying multiple mirror URLs."""
    if dest.exists() and dest.stat().st_size > 100:
        print(f"  ✅ {dest.name} already exists ({dest.stat().st_size / 1024:.1f} KB), skipping.")
        return True

    for url in urls:
        print(f"  ⬇  Trying: {url}")
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=30) as resp:
                data = resp.read()
            if len(data) > 100:
                dest.write_bytes(data)
                print(f"     ✅ Saved {dest.name} ({len(data) / 1024:.1f} KB)")
                return True
        except Exception as e:
            print(f"     ⚠️ Failed from {url}: {e}")
    return False


def download_cmapss() -> None:
    """Download NASA C-MAPSS FD001 files."""
    print("\n📦 Downloading NASA C-MAPSS FD001...")

    files = {
        "train_FD001.txt": [
            "https://raw.githubusercontent.com/stevenhurwitt/time-series-aerospace/master/train_FD001.txt",
            "https://raw.githubusercontent.com/biswajitsahoo1111/c-mapss-dataset/master/train_FD001.txt",
            "https://raw.githubusercontent.com/albertopari/c-mapss/master/train_FD001.txt",
        ],
        "test_FD001.txt": [
            "https://raw.githubusercontent.com/stevenhurwitt/time-series-aerospace/master/test_FD001.txt",
            "https://raw.githubusercontent.com/biswajitsahoo1111/c-mapss-dataset/master/test_FD001.txt",
            "https://raw.githubusercontent.com/albertopari/c-mapss/master/test_FD001.txt",
        ],
        "RUL_FD001.txt": [
            "https://raw.githubusercontent.com/stevenhurwitt/time-series-aerospace/master/RUL_FD001.txt",
            "https://raw.githubusercontent.com/biswajitsahoo1111/c-mapss-dataset/master/RUL_FD001.txt",
            "https://raw.githubusercontent.com/albertopari/c-mapss/master/RUL_FD001.txt",
        ],
    }

    for fname, urls in files.items():
        download_file_direct(urls, RAW_DIR / fname, fname)


def download_ai4i() -> None:
    """Download UCI AI4I 2020 Predictive Maintenance dataset."""
    print("\n📦 Downloading UCI AI4I 2020 dataset...")
    dest = RAW_DIR / "ai4i2020.csv"
    if dest.exists() and dest.stat().st_size > 100:
        print(f"  ✅ ai4i2020.csv already exists ({dest.stat().st_size / 1024:.1f} KB), skipping.")
        return

    urls = [
        "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip",
        "https://raw.githubusercontent.com/npthe/ai4i2020/main/ai4i2020.csv",
        "https://raw.githubusercontent.com/stefan-j/ai4i-predictive-maintenance/main/ai4i2020.csv",
    ]

    for url in urls:
        print(f"  ⬇  Trying: {url}")
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=30) as resp:
                data = resp.read()

            if url.endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
                    if csv_names:
                        dest.write_bytes(zf.read(csv_names[0]))
                        print(f"     ✅ Extracted ai4i2020.csv ({dest.stat().st_size / 1024:.1f} KB)")
                        return
            elif len(data) > 1000:
                dest.write_bytes(data)
                print(f"     ✅ Saved ai4i2020.csv ({len(data) / 1024:.1f} KB)")
                return
        except Exception as e:
            print(f"     ⚠️ Failed from {url}: {e}")


def verify() -> bool:
    """Check all required files exist."""
    print("\n" + "=" * 50)
    print("  Verification")
    print("=" * 50)
    required = {
        "train_FD001.txt": "C-MAPSS training (100 engines, run to failure)",
        "test_FD001.txt": "C-MAPSS test (100 engines, cut before failure)",
        "RUL_FD001.txt": "C-MAPSS true RUL for test engines",
        "ai4i2020.csv": "AI4I 2020 predictive maintenance",
    }
    all_ok = True
    for fname, desc in required.items():
        path = RAW_DIR / fname
        if path.exists() and path.stat().st_size > 100:
            size_kb = path.stat().st_size / 1024
            print(f"  ✅ {fname:20s} ({size_kb:8.1f} KB) — {desc}")
        else:
            print(f"  ❌ {fname:20s} MISSING — {desc}")
            all_ok = False

    if all_ok:
        print("\n✅ All datasets ready! You can proceed to Phase 1 ML training.")
    else:
        print("\n⚠️  Some files missing.")
    return all_ok


if __name__ == "__main__":
    download_cmapss()
    download_ai4i()
    verify()
