# Demo Model Registry

This directory contains lightweight fallback configurations and demo weights allowing **AI Factory Operating System** to initialize immediately after `git clone` without requiring full external weight downloads.

When running in **Demo Mode** (`DEMO_MODE=true` in `.env`):
- The inference engine detects whether full heavy weights are present in `data/models/`.
- If production weights are not yet downloaded, the backend uses lightweight heuristic fallback regression calibrated on NASA C-MAPSS holdout trajectories.
- To download full neural network checkpoints (PyTorch LSTM, 1D-CNN, XGBoost, Isolation Forest), run:
  ```bash
  python scripts/download_models.py
  ```
