import os,sys
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.components.data_ingestion import DataIngestion
from networksecurity.components.data_validation import DataValidation
from networksecurity.components.data_transformation import DataTransformation
from networksecurity.components.model_trainer import ModelTrainer
from networksecurity.entity.config_entity import TrainingPipelineConfig, DataIngestionConfig, DataValidationConfig, DataTransformationConfig, ModelTrainerConfig
from networksecurity.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact, DataTransformationArtifact, ModelTrainerArtifact
from networksecurity.cloud.gcs_storage import GCSModelStorage

class TrainingPipeline:
    def __init__(self):
        self.training_pipeline_config = TrainingPipelineConfig()
        self.gcs_storage = GCSModelStorage()

    def start_data_ingestion(self) -> DataIngestionArtifact:
        try:
            data_ingestion_config = DataIngestionConfig(training_pipeline_config=self.training_pipeline_config)
            logging.info(f"Start data ingestion with config: {data_ingestion_config}")
            data_ingestion = DataIngestion(data_ingestion_config=data_ingestion_config)
            data_ingestion_artifact=data_ingestion.initiate_data_ingestion()
            logging.info(f"Data ingestion completed with artifact: {data_ingestion_artifact}")
            return data_ingestion_artifact
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def start_data_validation(self, data_ingestion_artifact: DataIngestionArtifact) -> DataValidationArtifact:
        try:
            data_validation_config = DataValidationConfig(training_pipeline_config=self.training_pipeline_config)
            logging.info(f"Start data validation with config: {data_validation_config}")
            data_validation = DataValidation(data_validation_config=data_validation_config, data_ingestion_artifact=data_ingestion_artifact)
            data_validation_artifact = data_validation.initiate_data_validation()
            logging.info(f"Data validation completed with artifact: {data_validation_artifact}")
            return data_validation_artifact
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def start_data_transformation(self, data_validation_artifact: DataValidationArtifact) -> DataTransformationArtifact:
        try:
            data_transformation_config = DataTransformationConfig(training_pipeline_config=self.training_pipeline_config)
            logging.info(f"Start data transformation with config: {data_transformation_config}")
            data_transformation = DataTransformation(data_transformation_config=data_transformation_config, data_validation_artifact=data_validation_artifact)
            data_transformation_artifact = data_transformation.initiate_data_transformation()
            logging.info(f"Data transformation completed with artifact: {data_transformation_artifact}")
            return data_transformation_artifact
        except Exception as e:
            raise NetworkSecurityException(e, sys)  
        
    def start_model_trainer(self, data_transformation_artifact: DataTransformationArtifact) -> ModelTrainerArtifact:
        try:
            model_trainer_config = ModelTrainerConfig(training_pipeline_config=self.training_pipeline_config)
            logging.info(f"Start model training with config: {model_trainer_config}")
            model_trainer = ModelTrainer(model_trainer_config=model_trainer_config, data_transformation_artifact=data_transformation_artifact)
            model_trainer_artifact = model_trainer.initiate_model_trainer()
            logging.info(f"Model training completed with artifact: {model_trainer_artifact}")
            return model_trainer_artifact
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def upload_model_artifacts_to_gcs(self):
        try:
            self.gcs_storage.upload_model_artifacts()
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        

    def run_pipeline(self):
        try:
            logging.info("Starting training pipeline...")
            data_ingestion_artifact = self.start_data_ingestion()
            data_validation_artifact = self.start_data_validation(data_ingestion_artifact)
            data_transformation_artifact = self.start_data_transformation(data_validation_artifact)
            model_trainer_artifact = self.start_model_trainer(data_transformation_artifact)
            self.upload_model_artifacts_to_gcs()
            from networksecurity.service.feature_service import load_feature_defaults
            load_feature_defaults.cache_clear()
            logging.info("Training pipeline completed successfully.")
            return model_trainer_artifact
        except Exception as e:
            raise NetworkSecurityException(e, sys)
