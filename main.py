import sys

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.pipeline.training_pipeline import TrainingPipeline


if __name__ == "__main__":
    try:
        TrainingPipeline().run_pipeline()
    except Exception as e:
        raise NetworkSecurityException(e, sys) from e
