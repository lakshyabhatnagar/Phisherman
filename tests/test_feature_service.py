import unittest

from networksecurity.constants.training_pipeline import FEATURE_COLUMNS
from networksecurity.service.feature_service import build_feature_record, records_to_dataframe


class FeatureServiceTest(unittest.TestCase):
    def test_partial_input_gets_defaults(self):
        record, defaulted_fields = build_feature_record({"having_IP_Address": -1})

        self.assertEqual(record["having_IP_Address"], -1)
        self.assertEqual(set(record), set(FEATURE_COLUMNS))
        self.assertIn("URL_Length", defaulted_fields)
        self.assertEqual(record["Shortining_Service"], 1)

    def test_bad_value_fails(self):
        with self.assertRaises(ValueError):
            build_feature_record({"having_IP_Address": 99})

    def test_dataframe_order(self):
        record, _ = build_feature_record({"having_IP_Address": -1})
        df = records_to_dataframe([record])

        self.assertEqual(list(df.columns), FEATURE_COLUMNS)


if __name__ == "__main__":
    unittest.main()
