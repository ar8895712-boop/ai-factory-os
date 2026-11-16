# Model Evaluation Table

| Model | Dataset | Split | RMSE | NASA Score | F1 | PR-AUC |
|---|---|---|---|---|---|---|
| XGBoost (Window Feats) | C-MAPSS FD001 | Validation | 17.30 | 21276.3 | - | - |
| XGBoost (Window Feats) | C-MAPSS FD001 | Test | 17.07 | 549.4 | - | - |
| 1D-CNN | C-MAPSS FD001 | Validation | 18.89 | 19334.8 | - | - |
| 1D-CNN | C-MAPSS FD001 | Test | 20.09 | 1074.9 | - | - |
| LSTM (2-Layer) | C-MAPSS FD001 | Validation | 41.84 | 529419.0 | - | - |
| LSTM (2-Layer) | C-MAPSS FD001 | Test | 41.87 | 18802.2 | - | - |
| XGBoost Classifier | AI4I 2020 | Validation | - | - | 0.6869 | - |
| XGBoost Classifier | AI4I 2020 | Test | - | - | 0.7200 | 0.7377 |
