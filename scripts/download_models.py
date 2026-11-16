# ==============================================================
# scripts/download_models.py — Fetch Pre-Trained Model Weights
# Pulls production weights from GitHub Releases / Hugging Face Hub
# ==============================================================
"""
Usage:
    python scripts/download_models.py [--source github|huggingface]

Downloads trained weights into data/models/:
  - lstm_rul.pt (~230 KB)
  - cnn1d_rul.pt (~50 KB)
  - lstm_autoencoder.pt (~65 KB)
  - xgboost_rul.pkl (~710 KB)
  - isolation_forest.pkl (~1.9 MB)
  - failure_model.pkl (~405 KB)
  - scaler.pkl (~2 KB)
"""

from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from urllib.request import urlopen, Request

MODELS_DIR = Path(__file__).resolve().parent.parent / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Release URL endpoints (Replace with your tagged GitHub release or Hugging Face model repository)
MODEL_REGISTRY = {
    "github": {
        "base_url": "https://github.com/your-username/ai-factory-os/releases/download/v0.1.0-models",
        "files": [
            "lstm_rul.pt",
            "cnn1d_rul.pt",
            "lstm_autoencoder.pt",
            "xgboost_rul.pkl",
            "isolation_forest.pkl",
            "failure_model.pkl",
            "failure_preprocessor.pkl",
            "scaler.pkl",
        ]
    },
    "huggingface": {
        "base_url": "https://huggingface.co/your-username/ai-factory-os-models/resolve/main",
        "files": [
            "lstm_rul.pt",
            "cnn1d_rul.pt",
            "lstm_autoencoder.pt",
            "xgboost_rul.pkl",
            "isolation_forest.pkl",
            "failure_model.pkl",
            "failure_preprocessor.pkl",
            "scaler.pkl",
        ]
    }
}


def download_models(source: str = "github"):
    config = MODEL_REGISTRY.get(source, MODEL_REGISTRY["github"])
    base_url = config["base_url"]
    files = config["files"]

    print(f"📦 Fetching pre-trained weights from {source.upper()} ({base_url})...")

    for filename in files:
        target = MODELS_DIR / filename
        if target.exists() and target.stat().st_size > 100:
            print(f"  ✅ {filename} already present ({target.stat().st_size / 1024:.1f} KB)")
            continue

        url = f"{base_url}/{filename}"
        print(f"  ⬇ Downloading {filename} from {url}...")
        try:
            req = Request(url, headers={"User-Agent": "AIFactoryOS-Downloader/1.0"})
            with urlopen(req, timeout=45) as resp:
                content = resp.read()
            if len(content) > 100:
                target.write_bytes(content)
                print(f"     ✅ Successfully saved {filename} ({len(content) / 1024:.1f} KB)")
        except Exception as e:
            print(f"     ⚠️ Notice: Remote model not reachable at {url} ({e}).")
            print(f"        Ensure you have trained models locally or updated your release endpoint.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download pre-trained weights for AI Factory OS.")
    parser.add_argument("--source", choices=["github", "huggingface"], default="github", help="Model distribution source")
    args = parser.parse_args()
    download_models(args.source)
