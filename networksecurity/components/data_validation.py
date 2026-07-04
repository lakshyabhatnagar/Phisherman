from networksecurity.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from networksecurity.entity.config_entity import DataValidationConfig
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.constants.training_pipeline import DRIFT_THRESHOLD, FEATURE_COLUMNS, SCHEMA_FILE_PATH
from networksecurity.utils.main_utils.utils import read_yaml_file, write_yaml_file
import pandas as pd
import os, sys

class DataValidation:
    def __init__(self,data_validation_config: DataValidationConfig, data_ingestion_artifact: DataIngestionArtifact):
        try:
            self.data_validation_config=data_validation_config
            self.data_ingestion_artifact=data_ingestion_artifact
            self.schema_config= read_yaml_file(SCHEMA_FILE_PATH)
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    @staticmethod
    def read_data(file_path: str) -> pd.DataFrame:
        try:
            df = pd.read_csv(file_path)
            return df
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def Validate_number_of_columns(self, df: pd.DataFrame) -> bool:
        try:
            number_of_columns=len(self.schema_config["columns"])
            logging.info(f"Required Number of columns in the DataFrame: {number_of_columns}")
            logging.info(f"Number of columns in the Dataframe: {len(df.columns)}")
            if len(df.columns) == number_of_columns: return True
            return False
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def validate_column_names(self, df: pd.DataFrame) -> bool:
        try:
            expected_columns = [list(column.keys())[0] for column in self.schema_config["columns"]]
            return list(df.columns) == expected_columns
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    @staticmethod
    def _distribution(series: pd.Series) -> dict[int, float]:
        return {int(key): float(value) for key, value in series.value_counts(normalize=True).to_dict().items()}

    def detect_dataset_drift(self,base_df,current_df,threshold=DRIFT_THRESHOLD)->bool:
        try:
            status=True
            report={}
            for column in FEATURE_COLUMNS:
                base_distribution = self._distribution(base_df[column])
                current_distribution = self._distribution(current_df[column])
                values = set(base_distribution) | set(current_distribution)
                score = max(
                    abs(current_distribution.get(value, 0.0) - base_distribution.get(value, 0.0))
                    for value in values
                )
                is_found = score >= threshold
                if is_found:
                    status=False
                report.update({column: {
                    "score": float(score),
                    "drift_status": is_found,
                    "base_distribution": base_distribution,
                    "current_distribution": current_distribution,
                }})
            drift_report_dir=self.data_validation_config.drift_report_file_path
            dir_path=os.path.dirname(drift_report_dir)
            os.makedirs(dir_path, exist_ok=True)
            write_yaml_file(drift_report_dir,report)
            return status
        except Exception as e:
            raise NetworkSecurityException(e,sys)
    
    def initiate_data_validation(self)->DataValidationArtifact:
        try:
            logging.info("Starting data validation")
            logging.info(f"Data validation config: {self.data_validation_config}")
            logging.info(f"Data ingestion artifact: {self.data_ingestion_artifact}")

            # Read the training and testing data
            train_file_path=self.data_ingestion_artifact.train_file_path
            test_file_path=self.data_ingestion_artifact.test_file_path

            train_df = DataValidation.read_data(train_file_path)
            test_df = DataValidation.read_data(test_file_path)
            
            # Validate the number of columns
            status = self.Validate_number_of_columns(train_df)
            if not status:
                raise Exception(f"Number of columns in the training data is not as per the schema. Expected: {len(self.schema_config['columns'])}, Found: {len(train_df.columns)}")
            if not self.validate_column_names(train_df):
                raise Exception("Training data columns are not in the schema order")

            status = self.Validate_number_of_columns(test_df)
            if not status:
                raise Exception(f"Number of columns in the testing data is not as per the schema. Expected: {len(self.schema_config['columns'])}, Found: {len(test_df.columns)}")
            if not self.validate_column_names(test_df):
                raise Exception("Testing data columns are not in the schema order")
            
            # Check the data drift
            status=self.detect_dataset_drift(train_df[FEATURE_COLUMNS],test_df[FEATURE_COLUMNS])
            dir_path=os.path.dirname(self.data_validation_config.valid_train_file_path)
            os.makedirs(dir_path,exist_ok=True)

            train_df.to_csv(self.data_validation_config.valid_train_file_path, index=False, header=True)
            test_df.to_csv(self.data_validation_config.valid_test_file_path, index=False, header=True)
        
            data_validation_artifact=DataValidationArtifact(
                validation_status=status,
                valid_train_file_path=self.data_validation_config.valid_train_file_path,
                valid_test_file_path=self.data_validation_config.valid_test_file_path,
                invalid_test_file_path=None,
                invalid_train_file_path=None,
                drift_report_file_path=self.data_validation_config.drift_report_file_path
            )
            return data_validation_artifact
        except Exception as e:
            raise NetworkSecurityException(e,sys)
