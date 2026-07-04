import os
from pathlib import Path
from typing import Optional

from networksecurity.constants.training_pipeline import (
    DEFAULT_GCS_MODEL_PREFIX,
    FINAL_FEATURE_DEFAULTS_PATH,
    FINAL_MODEL_PATH,
    FINAL_PREPROCESSOR_PATH,
    GCS_BUCKET_NAME_ENV,
    GCS_MODEL_PREFIX_ENV,
)
from networksecurity.logging.logger import logging


class GCSModelStorage:
    def __init__(self, bucket_name: Optional[str] = None, prefix: Optional[str] = None):
        self.bucket_name = bucket_name or os.getenv(GCS_BUCKET_NAME_ENV)
        self.prefix = (prefix or os.getenv(GCS_MODEL_PREFIX_ENV, DEFAULT_GCS_MODEL_PREFIX)).strip("/")

    @property
    def configured(self) -> bool:
        return bool(self.bucket_name)

    def _bucket(self):
        if not self.configured:
            raise RuntimeError(f"{GCS_BUCKET_NAME_ENV} is not configured")
        try:
            from google.cloud import storage
        except ImportError as exc:
            raise RuntimeError("Install google-cloud-storage to use GCS artifact storage") from exc
        return storage.Client().bucket(self.bucket_name)

    def _blob_name(self, relative_path: str) -> str:
        relative_path = relative_path.replace(os.sep, "/").lstrip("/")
        return f"{self.prefix}/{relative_path}" if self.prefix else relative_path

    def upload_file(self, local_path: str, relative_path: Optional[str] = None) -> Optional[str]:
        if not self.configured or not os.path.exists(local_path):
            return None
        relative_path = relative_path or local_path
        blob_name = self._blob_name(relative_path)
        self._bucket().blob(blob_name).upload_from_filename(local_path)
        logging.info(f"Uploaded {local_path} to gs://{self.bucket_name}/{blob_name}")
        return blob_name

    def download_file(self, relative_path: str, local_path: str) -> bool:
        if not self.configured:
            return False
        blob_name = self._blob_name(relative_path)
        blob = self._bucket().blob(blob_name)
        if not blob.exists():
            return False
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(local_path)
        logging.info(f"Downloaded gs://{self.bucket_name}/{blob_name} to {local_path}")
        return True

    def upload_model_artifacts(self) -> list[str]:
        uploaded = []
        for path in (FINAL_MODEL_PATH, FINAL_PREPROCESSOR_PATH, FINAL_FEATURE_DEFAULTS_PATH):
            blob_name = self.upload_file(path, path)
            if blob_name:
                uploaded.append(blob_name)
        return uploaded

    def download_model_artifacts(self) -> list[str]:
        downloaded = []
        for path in (FINAL_MODEL_PATH, FINAL_PREPROCESSOR_PATH, FINAL_FEATURE_DEFAULTS_PATH):
            if self.download_file(path, path):
                downloaded.append(path)
        return downloaded
