import os
import sys
import numpy as np
import pandas as pd


#Definging common constant variables for training pipeline
TARGET_COLUMN: str= "Result"
PIPELINE_NAME: str= "Phisherman"
ARTIFACT_DIR: str= "Artifacts"
FILE_NAME: str= "phisingData.csv"
RAW_DATA_FILE_PATH: str = os.path.join("Network_Data", FILE_NAME)

TRAIN_FILE_NAME: str= "train.csv"
TEST_FILE_NAME: str= "test.csv"
SCHEMA_FILE_PATH = os.path.join("data_schema", "schema.yaml")
SAVED_MODEL_DIR: str= os.path.join("saved_models")
FINAL_MODEL_DIR: str = "final_model"

FEATURE_COLUMNS: list[str] = [
    "having_IP_Address",
    "URL_Length",
    "Shortining_Service",
    "having_At_Symbol",
    "double_slash_redirecting",
    "Prefix_Suffix",
    "having_Sub_Domain",
    "SSLfinal_State",
    "Domain_registeration_length",
    "Favicon",
    "port",
    "HTTPS_token",
    "Request_URL",
    "URL_of_Anchor",
    "Links_in_tags",
    "SFH",
    "Submitting_to_email",
    "Abnormal_URL",
    "Redirect",
    "on_mouseover",
    "RightClick",
    "popUpWidnow",
    "Iframe",
    "age_of_domain",
    "DNSRecord",
    "web_traffic",
    "Page_Rank",
    "Google_Index",
    "Links_pointing_to_page",
    "Statistical_report",
]



#Data ingestion related constants start with "DATA_INGESTION" var name
DATA_INGESTION_COLLECTION_NAME: str= "NetworkData"
DATA_INGESTION_DATABSASE_NAME: str= "network_security"
DATA_INGESTION_DIR_NAME: str= "data_ingestion"
DATA_INGESTION_FEATURE_STORE_DIR: str= "feature_store"
DATA_INGESTION_INGESTED_DIR: str= "ingested"
DATA_INGESTION_TRAIN_TEST_SPLIT_RATION: float= 0.2


#Data validation related constants start with "DATA_VALIDATION" var name
DATA_VALIDATION_DIR_NAME: str= "data_validation"
DATA_VALIDATION_VALID_DIR: str= "validated"
DATA_VALIDATION_INVALID_DIR: str= "invalid"
DATA_VALIDATION_DRIFT_REPORT: str= "drift_report"
DATA_VALIDATION_DRIFT_REPORT_FILE_NAME: str= "report.yaml"

#Data transformation related constants start with "DATA_TRANSFORMATION" var name
DATA_TRANSFORMATION_DIR_NAME: str= "data_transformation"
DATA_TRANSFORMATION_TRANSFORMED_DATA_DIR: str= "transformed"
DATA_TRANSFORMATION_TRANSFORMED_OBJECT_DIR: str= "transformed_object"
PREPROCESSING_OBJECT_FILE_NAME: str= "preprocessor.pkl"
FEATURE_DEFAULTS_FILE_NAME: str = "feature_defaults.json"
FINAL_PREPROCESSOR_PATH: str = os.path.join(FINAL_MODEL_DIR, PREPROCESSING_OBJECT_FILE_NAME)
FINAL_FEATURE_DEFAULTS_PATH: str = os.path.join(FINAL_MODEL_DIR, FEATURE_DEFAULTS_FILE_NAME)

#knn imputer to replace missing values
DATA_TRANSFORMATION_IMPUTER_PARAMS: dict={
    "missing_values": np.nan,
    "n_neighbors": 3,
    "weights": "uniform"
}

#Model trainer related constants start with "MODEL_TRAINER" var name
MODEL_TRAINER_DIR_NAME: str= "model_trainer"
MODEL_TRAINER_TRAINED_MODEL_DIR: str= "trained_model"   
MODEL_FILE_NAME: str= "model.pkl"
FINAL_MODEL_PATH: str = os.path.join(FINAL_MODEL_DIR, MODEL_FILE_NAME)
MODEL_TRAINER_EXPECTED_SCORE: float= 0.6
MODEL_TRAINER_OVER_FITTING_UNDER_FITTING_THRESHOLD: float= 0.05


GCS_BUCKET_NAME_ENV: str = "GCS_BUCKET_NAME"
GCS_MODEL_PREFIX_ENV: str = "GCS_MODEL_PREFIX"
DEFAULT_GCS_MODEL_PREFIX: str = "phisherman/models"

DRIFT_REPORT_DIR: str = os.path.join("reports", "drift")
DRIFT_THRESHOLD: float = float(os.getenv("DRIFT_THRESHOLD", "0.35"))
DRIFT_MIN_REFERENCE_FREQUENCY: float = float(os.getenv("DRIFT_MIN_REFERENCE_FREQUENCY", "0.02"))
AUTO_RETRAIN_ON_DRIFT: bool = os.getenv("AUTO_RETRAIN_ON_DRIFT", "true").lower() == "true"
AUTO_RETRAIN_COOLDOWN_SECONDS: int = int(os.getenv("AUTO_RETRAIN_COOLDOWN_SECONDS", "3600"))
