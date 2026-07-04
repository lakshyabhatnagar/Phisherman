import os
import sys

import pandas as pd
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from starlette.responses import RedirectResponse
from uvicorn import run as app_run

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.pipeline.training_pipeline import TrainingPipeline
from networksecurity.service.drift_service import drift_service
from networksecurity.service.feature_service import (
    FEATURE_COLUMNS,
    FeaturePayload,
    build_feature_record,
    payload_to_dict,
    records_to_dataframe,
)
from networksecurity.service.prediction_service import prediction_service
from networksecurity.service.retraining_service import retraining_service
from networksecurity.service.url_intel_service import URLPayload, enrich_with_reputation


load_dotenv()

app = FastAPI(title="Phisherman API")

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials="*" not in cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["docs"])
async def index():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}


def _predict_dataframe(features_df: pd.DataFrame, background_tasks: BackgroundTasks, stage: str) -> dict:
    drift = drift_service.check(features_df, stage=stage)
    retraining_triggered = False
    if drift.exceeded:
        retraining_triggered = retraining_service.maybe_start(
            background_tasks,
            reason=f"{stage} drift score {drift.score} exceeded {drift.threshold}",
        )

    prediction = prediction_service.predict(features_df)
    return {
        **prediction,
        "drift": {
            "exceeded": drift.exceeded,
            "score": drift.score,
            "threshold": drift.threshold,
            "drifted_features": drift.drifted_features,
            "report_path": drift.report_path,
        },
        "retraining_triggered": retraining_triggered,
    }


@app.post("/predict", tags=["prediction"])
async def predict(payload: FeaturePayload, background_tasks: BackgroundTasks):
    try:
        record, defaulted_fields = build_feature_record(payload_to_dict(payload))
        features_df = records_to_dataframe([record])
        result = _predict_dataframe(features_df, background_tasks, stage="prediction")
        return {
            **result,
            "defaulted_fields": defaulted_fields,
            "features": record,
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logging.error(f"Error in prediction: {e}")
        raise NetworkSecurityException(e, sys)


@app.post("/predict/url", tags=["prediction"])
async def predict_url(payload: URLPayload, background_tasks: BackgroundTasks):
    try:
        extracted_features, reputation_checks = enrich_with_reputation(payload.url)
        record, defaulted_fields = build_feature_record(extracted_features)
        features_df = records_to_dataframe([record])
        result = _predict_dataframe(features_df, background_tasks, stage="url_prediction")
        return {
            **result,
            "url": payload.url,
            "extracted_features": extracted_features,
            "defaulted_fields": defaulted_fields,
            "features": record,
            "reputation_checks": reputation_checks,
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logging.error(f"Error in url prediction: {e}")
        raise NetworkSecurityException(e, sys)


@app.post("/predict/csv", tags=["prediction"])
async def predict_csv(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        incoming_df = pd.read_csv(file.file)
        records = []
        defaulted_fields = []
        for row in incoming_df.to_dict(orient="records"):
            row_features = {key: value for key, value in row.items() if key in FEATURE_COLUMNS}
            record, row_defaulted = build_feature_record(row_features)
            records.append(record)
            defaulted_fields.append(row_defaulted)

        features_df = records_to_dataframe(records)
        drift = drift_service.check(features_df, stage="csv_prediction")
        retraining_triggered = False
        if drift.exceeded:
            retraining_triggered = retraining_service.maybe_start(
                background_tasks,
                reason=f"csv_prediction drift score {drift.score} exceeded {drift.threshold}",
            )

        predictions = []
        for index, record in enumerate(records):
            result = prediction_service.predict(records_to_dataframe([record]))
            predictions.append(
                {
                    **result,
                    "row": index,
                    "defaulted_fields": defaulted_fields[index],
                }
            )

        return {
            "predictions": predictions,
            "drift": {
                "exceeded": drift.exceeded,
                "score": drift.score,
                "threshold": drift.threshold,
                "drifted_features": drift.drifted_features,
                "report_path": drift.report_path,
            },
            "retraining_triggered": retraining_triggered,
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logging.error(f"Error in csv prediction: {e}")
        raise NetworkSecurityException(e, sys)


@app.post("/train", tags=["training"])
async def train_route():
    try:
        train_pipeline = TrainingPipeline()
        artifact = train_pipeline.run_pipeline()
        return {
            "message": "Training pipeline executed successfully.",
            "model_path": artifact.trained_model_file_path,
            "test_f1_score": artifact.test_metric_artifact.f1_score,
        }
    except Exception as e:
        logging.error(f"Error in training pipeline: {e}")
        raise NetworkSecurityException(e, sys)


@app.get("/train", include_in_schema=False)
async def train_route_legacy():
    await train_route()
    return Response("Training pipeline executed successfully.")


if __name__ == "__main__":
    app_run(app,host="0.0.0.0", port=8000)
