from functools import lru_cache
import json
import os
from typing import Any, Optional

import pandas as pd
from pydantic import BaseModel

from networksecurity.constants.training_pipeline import FEATURE_COLUMNS, FINAL_FEATURE_DEFAULTS_PATH, RAW_DATA_FILE_PATH


ALLOWED_FEATURE_VALUES = {-1, 0, 1}
LABELS = {0: "phishing", 1: "legitimate", -1: "phishing"}


class FeaturePayload(BaseModel):
    having_IP_Address: Optional[int] = None
    URL_Length: Optional[int] = None
    Shortining_Service: Optional[int] = None
    having_At_Symbol: Optional[int] = None
    double_slash_redirecting: Optional[int] = None
    Prefix_Suffix: Optional[int] = None
    having_Sub_Domain: Optional[int] = None
    SSLfinal_State: Optional[int] = None
    Domain_registeration_length: Optional[int] = None
    Favicon: Optional[int] = None
    port: Optional[int] = None
    HTTPS_token: Optional[int] = None
    Request_URL: Optional[int] = None
    URL_of_Anchor: Optional[int] = None
    Links_in_tags: Optional[int] = None
    SFH: Optional[int] = None
    Submitting_to_email: Optional[int] = None
    Abnormal_URL: Optional[int] = None
    Redirect: Optional[int] = None
    on_mouseover: Optional[int] = None
    RightClick: Optional[int] = None
    popUpWidnow: Optional[int] = None
    Iframe: Optional[int] = None
    age_of_domain: Optional[int] = None
    DNSRecord: Optional[int] = None
    web_traffic: Optional[int] = None
    Page_Rank: Optional[int] = None
    Google_Index: Optional[int] = None
    Links_pointing_to_page: Optional[int] = None
    Statistical_report: Optional[int] = None

    class Config:
        extra = "forbid"


def payload_to_dict(payload: FeaturePayload) -> dict[str, int]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_none=True)
    return payload.dict(exclude_none=True)


@lru_cache(maxsize=1)
def load_feature_defaults() -> dict[str, int]:
    if os.path.exists(FINAL_FEATURE_DEFAULTS_PATH):
        try:
            with open(FINAL_FEATURE_DEFAULTS_PATH) as file:
                saved_defaults = json.load(file)
            return {column: int(saved_defaults.get(column, 0)) for column in FEATURE_COLUMNS}
        except Exception:
            pass

    try:
        df = pd.read_csv(RAW_DATA_FILE_PATH)
    except Exception:
        return {column: 0 for column in FEATURE_COLUMNS}

    defaults = {}
    for column in FEATURE_COLUMNS:
        if column not in df.columns:
            defaults[column] = 0
            continue
        mode = df[column].mode(dropna=True)
        defaults[column] = int(mode.iloc[0]) if not mode.empty else 0
    return defaults


def build_feature_record(values: dict[str, Any]) -> tuple[dict[str, int], list[str]]:
    unknown = sorted(set(values) - set(FEATURE_COLUMNS))
    if unknown:
        raise ValueError(f"Unknown feature(s): {', '.join(unknown)}")

    record = load_feature_defaults().copy()
    provided = {}
    for key, value in values.items():
        if pd.isna(value):
            continue
        try:
            int_value = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{key} must be one of -1, 0, 1")
        if int_value not in ALLOWED_FEATURE_VALUES:
            raise ValueError(f"{key} must be one of -1, 0, 1")
        provided[key] = int_value

    record.update(provided)
    defaulted_fields = [column for column in FEATURE_COLUMNS if column not in provided]
    return record, defaulted_fields


def records_to_dataframe(records: list[dict[str, int]]) -> pd.DataFrame:
    return pd.DataFrame(records, columns=FEATURE_COLUMNS)


def label_for_prediction(prediction: int) -> str:
    return LABELS.get(int(prediction), str(prediction))
