from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from networksecurity.constants.training_pipeline import (
    DRIFT_MIN_REFERENCE_FREQUENCY,
    DRIFT_REPORT_DIR,
    DRIFT_THRESHOLD,
    FEATURE_COLUMNS,
    RAW_DATA_FILE_PATH,
)
from networksecurity.utils.main_utils.utils import write_yaml_file


@dataclass
class DriftResult:
    exceeded: bool
    score: float
    threshold: float
    report_path: str
    drifted_features: list[str]


class DriftService:
    def __init__(self, reference_path: str = RAW_DATA_FILE_PATH):
        self.reference_path = reference_path
        self._reference_df = None

    def _reference(self) -> pd.DataFrame:
        if self._reference_df is None:
            self._reference_df = pd.read_csv(self.reference_path)[FEATURE_COLUMNS]
        return self._reference_df

    @staticmethod
    def _distribution(series: pd.Series) -> dict[int, float]:
        return {int(key): float(value) for key, value in series.value_counts(normalize=True).to_dict().items()}

    def check(self, current_df: pd.DataFrame, stage: str, threshold: float = DRIFT_THRESHOLD) -> DriftResult:
        reference_df = self._reference()
        feature_reports = {}
        drifted_features = []

        for column in FEATURE_COLUMNS:
            reference_distribution = self._distribution(reference_df[column])
            current_distribution = self._distribution(current_df[column])

            if len(current_df) == 1:
                value = int(current_df[column].iloc[0])
                score = 1.0 - reference_distribution.get(value, 0.0)
                drifted = reference_distribution.get(value, 0.0) < DRIFT_MIN_REFERENCE_FREQUENCY
            else:
                values = set(reference_distribution) | set(current_distribution)
                score = max(
                    abs(current_distribution.get(value, 0.0) - reference_distribution.get(value, 0.0))
                    for value in values
                )
                drifted = score >= threshold

            if drifted:
                drifted_features.append(column)
            feature_reports[column] = {
                "score": float(score),
                "drift_status": bool(drifted),
                "reference_distribution": reference_distribution,
                "current_distribution": current_distribution,
            }

        drift_score = len(drifted_features) / len(FEATURE_COLUMNS)
        exceeded = drift_score >= threshold
        report_path = str(
            Path(DRIFT_REPORT_DIR)
            / f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{stage}_drift.yaml"
        )
        write_yaml_file(
            report_path,
            {
                "stage": stage,
                "threshold": threshold,
                "score": float(drift_score),
                "drift_exceeded": exceeded,
                "drifted_features": drifted_features,
                "features": feature_reports,
            },
            replace=True,
        )
        return DriftResult(
            exceeded=exceeded,
            score=float(drift_score),
            threshold=threshold,
            report_path=report_path,
            drifted_features=drifted_features,
        )


drift_service = DriftService()
