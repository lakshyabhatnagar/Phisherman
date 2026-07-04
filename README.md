# Phisherman

An end-to-end phishing risk prediction project built around a FastAPI inference API, a Streamlit demo UI, a retrainable scikit-learn pipeline, MongoDB-backed training data, drift reports, and Google Cloud Storage model artifacts.

This project predicts from extracted URL/security features and can also derive the public URL-shape signals from a submitted link.

## What It Does

- Accepts partial feature input through `POST /predict`.
- Accepts a URL through `POST /predict/url` and extracts simple URL-shape signals.
- Fills missing feature values from the mode of the training dataset.
- Uses Google Safe Browsing for URL reputation when `SAFE_BROWSING_API_KEY` is configured.
- Runs drift checks on prediction input and writes a report under `reports/drift/`.
- Automatically starts background retraining when drift exceeds `DRIFT_THRESHOLD`.
- Supports manual retraining through `POST /train`.
- Saves the latest `final_model/model.pkl` and `final_model/preprocessor.pkl`.
- Uploads model artifacts to Google Cloud Storage when `GCS_BUCKET_NAME` is configured.
- Provides a Streamlit UI with quick inputs and optional advanced feature controls.

## Main Flow

1. `push_data.py` loads `Network_Data/phisingData.csv` into MongoDB.
2. `TrainingPipeline` pulls MongoDB data, splits train/test data, validates schema, checks drift, transforms features, trains models, and saves artifacts.
3. FastAPI loads the saved model/preprocessor once and reloads when files change.
4. Prediction input is converted into the exact 30-column feature vector expected by the saved preprocessor.
5. Drift is checked for every prediction request.
6. If drift exceeds the threshold, retraining starts in the background.

## API

Start the API:

```bash
.venv/bin/uvicorn app:app --reload
```

Predict with partial features:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "having_IP_Address": -1,
    "URL_Length": 1,
    "Shortining_Service": 1,
    "having_At_Symbol": 1,
    "SSLfinal_State": -1
  }'
```

Predict from a URL:

```bash
curl -X POST http://localhost:8000/predict/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/login"}'
```

Manual retraining:

```bash
curl -X POST http://localhost:8000/train
```

Batch CSV prediction:

```bash
curl -X POST http://localhost:8000/predict/csv \
  -F "file=@valid_data/test.csv"
```

## Streamlit

Start Streamlit after the API is running:

```bash
.venv/bin/streamlit run streamlit_app.py
```

The UI asks for a small set of high-signal fields first. Advanced users can override every model feature for more accurate prediction.

For Streamlit Cloud, set `API_URL` in app secrets to the deployed FastAPI backend URL. Do not use `localhost` in production. The sidebar API override is hidden unless `SHOW_API_URL_INPUT=true`.

## Environment Variables

Copy `.env.example` to `.env` for local development. Never commit `.env`, Google service account JSON files, or trained `.pkl` artifacts.

- `MONGO_DB_URL`: MongoDB connection string used by ingestion/training.
- `GCS_BUCKET_NAME`: optional GCS bucket for model artifacts.
- `GCS_MODEL_PREFIX`: optional object prefix, defaults to `phisherman/models`.
- `GOOGLE_APPLICATION_CREDENTIALS`: optional local path to a Google service account JSON file.
- `SAFE_BROWSING_API_KEY`: optional Google Safe Browsing API key for URL reputation checks.
- `CORS_ALLOW_ORIGINS`: comma-separated frontend origins allowed to call the API.
- `DRIFT_THRESHOLD`: fraction of drifted features needed to trigger retraining, defaults to `0.35`.
- `DRIFT_MIN_REFERENCE_FREQUENCY`: single-record rare-value threshold, defaults to `0.02`.
- `AUTO_RETRAIN_ON_DRIFT`: defaults to `true`.
- `AUTO_RETRAIN_COOLDOWN_SECONDS`: defaults to `3600`.
- `ENABLE_MLFLOW`: optional, defaults to `false`.
- `API_URL`: FastAPI backend URL used by Streamlit.
- `SHOW_API_URL_INPUT`: optional local-dev toggle for showing the API URL sidebar input.

## Production

- Runtime: Python `3.12.13`.
- Secrets: set environment variables in the deployment platform, not in Git.
- Model artifacts: keep `model.pkl` and `preprocessor.pkl` in GCS under `GCS_MODEL_PREFIX`; the API downloads them when local files are missing.
- Container: build with `docker build -t phisherman .` and run with the required env vars.
- Health check: `GET /health`.

For local GCS authentication, use Google Application Default Credentials:

```bash
gcloud auth application-default login
```

## Resume Summary

Built Phisherman, a phishing risk prediction platform with FastAPI, Streamlit, scikit-learn, MongoDB, automated drift monitoring, background retraining, and Google Cloud Storage model artifact management.
