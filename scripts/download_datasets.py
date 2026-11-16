# ==============================================================
# scripts/download_datasets.py — Fetch C-MAPSS FD001 & AI4I 2020
# ==============================================================
"""
Downloads the two required datasets into data/raw/:
  1. NASA C-MAPSS FD001 (train, test, RUL files)
  2. UCI AI4I 2020 Predictive Maintenance Dataset

Run with network access:
    python scripts/download_datasets.py
"""

from __future__ import annotations
import io
import os
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def download_file_direct(urls: list[str], dest: Path, desc: str) -> bool:
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
    print("\n📦 Downloading NASA C-MAPSS FD001...")
    files = {
        "train_FD001.txt": [
            "https://raw.githubusercontent.com/hankroark/Turbofan-Engine-Degradation/master/CMAPSSData/train_FD001.txt",
            "https://raw.githubusercontent.com/mitacs-prognostics/cmapss-data/master/train_FD001.txt",
        ],
        "test_FD001.txt": [
            "https://raw.githubusercontent.com/hankroark/Turbofan-Engine-Degradation/master/CMAPSSData/test_FD001.txt",
            "https://raw.githubusercontent.com/mitacs-prognostics/cmapss-data/master/test_FD001.txt",
        ],
        "RUL_FD001.txt": [
            "https://raw.githubusercontent.com/hankroark/Turbofan-Engine-Degradation/master/CMAPSSData/RUL_FD001.txt",
            "https://raw.githubusercontent.com/mitacs-prognostics/cmapss-data/master/RUL_FD001.txt",
        ],
    }

    for fname, urls in files.items():
        dest = RAW_DIR / fname
        download_file_direct(urls, dest, fname)


def download_ai4i() -> None:
    print("\n📦 Downloading UCI AI4I 2020 Predictive Maintenance...")
    dest = RAW_DIR / "ai4i2020.csv"
    urls = [
        "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip",
        "https://raw.githubusercontent.com/ravi-ilabs/ai4i2020/main/ai4i2020.csv",
    ]
    if dest.exists() and dest.stat().st_size > 100:
        print(f"  ✅ {dest.name} already exists ({dest.stat().st_size / 1024:.1f} KB), skipping.")
        return

    # Try direct CSV mirror first
    if download_file_direct([urls[1]], dest, "ai4i2020.csv"):
        return

    # Fallback to UCI zip
    print(f"  ⬇  Downloading zip from UCI: {urls[0]}")
    try:
        req = Request(urls[0], headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=30) as resp:
            zf = zipfile.ZipFile(io.BytesIO(resp.read()))
            for name in zf.namelist():
                if name.endswith(".csv"):
                    dest.write_bytes(zf.read(name))
                    print(f"     ✅ Extracted {dest.name} ({dest.stat().st_size / 1024:.1f} KB)")
                    return
    except Exception as e:
        print(f"     ⚠️ Failed to extract from zip: {e}")


if __name__ == "__main__":
    download_cmapss()
    download_ai4i()
    print("\n🎉 Dataset download routine complete!")
