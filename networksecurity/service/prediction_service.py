import os
from threading import RLock

import pandas as pd

from networksecurity.cloud.gcs_storage import GCSModelStorage
from networksecurity.constants.training_pipeline import FINAL_MODEL_PATH, FINAL_PREPROCESSOR_PATH
from networksecurity.service.feature_service import label_for_prediction
from networksecurity.utils.main_utils.utils import load_object


class PredictionService:
    def __init__(self):
        self._lock = RLock()
        self._model = None
        self._preprocessor = None
        self._state = None

    def _artifact_state(self) -> tuple[float, float]:
        return (os.path.getmtime(FINAL_MODEL_PATH), os.path.getmtime(FINAL_PREPROCESSOR_PATH))

    def _ensure_artifacts(self) -> None:
        if os.path.exists(FINAL_MODEL_PATH) and os.path.exists(FINAL_PREPROCESSOR_PATH):
            return
        GCSModelStorage().download_model_artifacts()

    def _load(self) -> None:
        self._ensure_artifacts()
        state = self._artifact_state()
        if self._model is not None and self._state == state:
            return
        self._preprocessor = load_object(FINAL_PREPROCESSOR_PATH)
        self._model = load_object(FINAL_MODEL_PATH)
        if hasattr(self._model, "verbose"):
            self._model.verbose = 0
        self._state = state

    def predict(self, features: pd.DataFrame) -> dict:
        with self._lock:
            self._load()
            transformed = self._preprocessor.transform(features)
            raw_prediction = int(self._model.predict(transformed)[0])
            confidence = None
            if hasattr(self._model, "predict_proba"):
                probabilities = self._model.predict_proba(transformed)[0]
                confidence = float(max(probabilities))
            return {
                "prediction": raw_prediction,
                "label": label_for_prediction(raw_prediction),
                "confidence": confidence,
            }


prediction_service = PredictionService()
