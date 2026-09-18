# Retail Sales Forecasting - Time Series Project

Time series sales forecasting system for a multi-store retail chain, using the Rossmann Store Sales dataset (Kaggle). Compares a classical statistical approach (SARIMA) against modern gradient-boosted tree models (LightGBM, XGBoost) for demand forecasting, deployed as a live prediction API.

## Live Demo
API: https://timeseries-forecasting-project.onrender.com

## Problem Statement
Retailers need to forecast daily sales per store to plan staffing, inventory, and promotions. This project builds and compares forecasting approaches on the Rossmann Store Sales dataset - 1,115 stores, ~1.02M daily records over ~2.5 years (2013-2015) - with store-level attributes (type, assortment, competition) and daily signals (promotions, holidays).

## Dataset
- Source: Rossmann Store Sales, Kaggle
- train.csv: 1,017,209 rows x 9 columns (daily sales per store)
- store.csv: 1,115 rows (store metadata - type, assortment, competition distance, Promo2)

## Approach

### 1. EDA
- Merged train + store data (1,017,209 rows x 18 columns)
- Handled missing values (CompetitionDistance via median; CompetitionOpen*/Promo2* treated as not applicable and filled with 0/None)
- National daily sales trend plot - confirmed weekly seasonality and a yearly holiday-season spike
- Selected Store 769 as a representative single series for classical modeling

### 2. Classical Time Series Analysis (Store 769)
- Seasonal decomposition (additive, period=7) - confirmed strong weekly seasonality and a mild upward trend
- ADF stationarity test: p=0.0224 (borderline)
- ACF/PACF analysis - slow ACF decay indicated differencing needed
- Fit SARIMA(1,1,1)x(0,1,1,7) after dropping an insignificant seasonal AR term
- Limitation: as a univariate model, SARIMA cannot use Promo/Holiday signals

### 3. Feature Engineering (for ML models, all 1,115 stores)
- Lag features: lag_1, lag_7, lag_14 (grouped by store)
- Rolling window: rolling_mean_7, rolling_std_7 (shift(1) before rolling to prevent data leakage)
- Calendar features: Year, Month, Day, WeekOfYear, IsWeekend
- Label-encoded categoricals: StoreType, Assortment, StateHoliday
- Final dataset: 828,782 rows x 17 features

### 4. Modeling & Comparison
Time-based train/test split (never random shuffle for time series) - last 6 weeks held out as test.

| Model | Scope | MAE | RMSE | MAPE |
|---|---|---|---|---|
| SARIMA(1,1,1)x(0,1,1,7) | Single store, univariate | 1378.47 | 1647.01 | 11.54% |
| LightGBM | All 1,115 stores, multivariate | 648.41 | 933.16 | 9.80% |
| XGBoost (final model) | All 1,115 stores, multivariate | 627.48 | 904.37 | 9.49% |
| XGBoost (Store 769 only, fair comparison) | Single store, multivariate | 905.89 | 1250.01 | 7.41% |

Note: the SARIMA vs ML comparison is not perfectly apples-to-apples - SARIMA was fit on one store with no external features, while the ML models use all stores plus Promo/Holiday/Competition features. For a fairer check, XGBoost was also evaluated on Store 769 alone (same store, same test period) - it still outperforms SARIMA (905.89 vs 1378.47 MAE, a ~34% improvement), confirming the gain isn't purely from pooling stores.

### 5. Hyperparameter Tuning
Tuned XGBoost via RandomizedSearchCV with TimeSeriesSplit (not standard k-fold, to avoid future-data leakage). The tuned model scored slightly worse on held-out test (MAE 635.77) than the untuned default (MAE 627.48) - untuned model kept as final.

### 6. Feature Importance
Top predictors: DayOfWeek, Day, CompetitionDistance, Store, lag_1. IsWeekend had near-zero importance, likely redundant given DayOfWeek.

## Deployment
- Flask API (app.py) serving the tuned XGBoost model
- Since lag/rolling features are history-dependent, a per-store latest feature snapshot is precomputed and used to serve predictions for near-term future dates
- Deployed on Render (free tier) via Gunicorn

## Tech Stack
Python, pandas, numpy, scikit-learn, statsmodels, XGBoost, LightGBM, Flask, Gunicorn, Render

## Limitations & Future Work
- The deployed feature snapshot is frozen at the end of training data - predictions further into the future become progressively less reliable
- SARIMA was only validated on one store
- Residual diagnostics showed non-normal residuals, consistent with the model underfitting holiday/promo spikes
