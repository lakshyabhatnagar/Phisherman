import yaml
import os
import sys
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
import numpy as np
import pickle
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import f1_score
#import dill

def read_yaml_file(file_path: str) -> dict:
    try:
        with open(file_path, 'rb') as yaml_file:
            content = yaml.safe_load(yaml_file)
        return content
    except Exception as e:
        raise NetworkSecurityException(e, sys) from e
    
def write_yaml_file(file_path:str,content:object,replace: bool=False)->None:
    try:
        if replace:
            if os.path.exists(file_path): os.remove(file_path)
        os.makedirs(os.path.dirname(file_path),exist_ok=True)
        with open(file_path, "w") as file:
            yaml.dump(content,file)
    except Exception as e:
        raise NetworkSecurityException(e,sys)
    
def save_numpy_array_data(file_path:str, array:np.array):
    try:
        dir_path=os.path.dirname(file_path)
        os.makedirs(dir_path,exist_ok=True)
        with open(file_path, "wb") as file:
            np.save(file, array)
    except Exception as e:
        raise NetworkSecurityException(e,sys) from e
    
def save_object(file_path:str, obj:object):
    try:
        logging.info(f"Saving object at: {file_path}")
        dir_path=os.path.dirname(file_path)
        os.makedirs(dir_path,exist_ok=True)
        with open(file_path, "wb") as file:
            pickle.dump(obj, file)
        logging.info(f"Object saved at: {file_path}")
    except Exception as e:
        raise NetworkSecurityException(e,sys) from e
    
def load_object(file_path:str) -> object:
    try:
        if not os.path.exists(file_path):
            raise Exception(f"File path: {file_path} does not exist")
        logging.info(f"Loading object from: {file_path}")
        with open(file_path, "rb") as file:
            obj = pickle.load(file)
        logging.info(f"Object loaded from: {file_path}")
        return obj
    except Exception as e:
        raise NetworkSecurityException(e,sys) from e
    
def load_numpy_array_data(file_path:str) -> np.array:
    try:
        if not os.path.exists(file_path):
            raise Exception(f"File path: {file_path} does not exist")
        logging.info(f"Loading numpy array from: {file_path}")
        with open(file_path, "rb") as file:
            array = np.load(file)
        logging.info(f"Numpy array loaded from: {file_path}")
        return array
    except Exception as e:
        raise NetworkSecurityException(e,sys) from e
    
def evaluate_model(x_train,y_train,x_test,y_test,models,params):
    try:
        report = {}
        for i in range(len(list(models))):
            model = list(models.values())[i]
            para=params[list(models.keys())[i]]
            
            gs=GridSearchCV(model,para,cv=3,scoring="f1",n_jobs=-1)
            gs.fit(x_train,y_train)
            model.set_params(**gs.best_params_)
            model.fit(x_train,y_train)

            y_test_pred=model.predict(x_test)
            test_model_score=f1_score(y_test,y_test_pred)

            report[list(models.keys())[i]]=test_model_score
        return report
    except Exception as e:
        raise NetworkSecurityException(e,sys) from e
