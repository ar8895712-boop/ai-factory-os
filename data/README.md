# Data Directory & Benchmark Provenance

This directory contains the runtime datasets, model weights, and local databases for the **AI Factory Operating System**.

> [!NOTE]
> In accordance with open-source and data governance best practices, raw training datasets, heavy binary weights, and runtime SQLite files are **intentionally excluded from Git version control**.

---

## 1. Datasets Used

The models in this platform are trained and evaluated exclusively on open, peer-reviewed industrial benchmarks:

| Dataset | Provider | Purpose | Primary Files | License |
|---|---|---|---|---|
| **NASA C-MAPSS FD001** | NASA Ames Prognostics CoE | Turbofan RUL forecasting & degradation | `train_FD001.txt`, `test_FD001.txt`, `RUL_FD001.txt` | Public Domain / NASA Open Data |
| **AI4I 2020 Predictive Maintenance** | UCI Machine Learning Repository | Multi-failure CNC milling classification | `ai4i2020.csv` | CC BY 4.0 |
| **SKAB Benchmark** | Skoltech | Industrial water circulation anomaly detection | `skab/*.csv` | MIT |

---

## 2. Automated Download

To automatically download and unpack all required benchmark datasets into `data/raw/`, run:

```bash
python scripts/download_datasets.py
# Or if running from root:
python download_datasets.py
```

---

## 3. Expected Directory Layout

Once downloaded and initialized, your local `data/` directory will look like this:

```
data/
├── raw/                      # Downloaded benchmark files (gitignored)
│   ├── train_FD001.txt
│   ├── test_FD001.txt
│   ├── RUL_FD001.txt
│   └── ai4i2020.csv
├── models/                   # Trained weights & preprocessors (gitignored)
│   ├── lstm_rul.pt
│   ├── cnn1d_rul.pt
│   ├── xgboost_rul.pkl
│   ├── isolation_forest.pkl
│   └── scaler.pkl
├── factory.db                # SQLite demo database (gitignored)
└── README.md                 # This documentation file (tracked)
```

---

## 4. Citation & Reference

- **NASA C-MAPSS**: A. Saxena, K. Goebel, D. Simon, N. Eklund, *"Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation"*, Prognostics & Health Management (PHM08), 2008.
- **UCI AI4I 2020**: S. Matzka, *"Explainable Artificial Intelligence for Predictive Maintenance Applications"*, IEEE ICPS, 2020.
