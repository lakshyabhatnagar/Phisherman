import time
from threading import Lock

from networksecurity.constants.training_pipeline import AUTO_RETRAIN_COOLDOWN_SECONDS, AUTO_RETRAIN_ON_DRIFT
from networksecurity.logging.logger import logging


class RetrainingService:
    def __init__(self):
        self._lock = Lock()
        self._running = False
        self._last_started_at = 0.0

    def _can_start(self) -> bool:
        if not AUTO_RETRAIN_ON_DRIFT:
            return False
        if self._running:
            return False
        return time.time() - self._last_started_at >= AUTO_RETRAIN_COOLDOWN_SECONDS

    def maybe_start(self, background_tasks, reason: str) -> bool:
        with self._lock:
            if not self._can_start():
                return False
            self._running = True
            self._last_started_at = time.time()
        background_tasks.add_task(self.run_training, reason)
        return True

    def run_training(self, reason: str = "manual") -> None:
        try:
            logging.info(f"Starting training pipeline. reason={reason}")
            from networksecurity.pipeline.training_pipeline import TrainingPipeline

            TrainingPipeline().run_pipeline()
        finally:
            with self._lock:
                self._running = False


retraining_service = RetrainingService()
