import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app


class ApiTest(unittest.TestCase):
    def drift(self):
        return SimpleNamespace(exceeded=False, score=0.0, threshold=0.35, drifted_features=[], report_path=None)

    @patch("app.prediction_service.predict", return_value={"prediction": 1, "label": "legitimate", "confidence": 0.9})
    @patch("app.drift_service.check")
    def test_predict_accepts_partial_payload(self, drift_check, _predict):
        drift_check.return_value = self.drift()
        response = TestClient(app).post(
            "/predict",
            json={
                "having_IP_Address": -1,
                "URL_Length": 1,
                "Shortining_Service": 1,
                "having_At_Symbol": 1,
                "SSLfinal_State": -1,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["label"], {"phishing", "legitimate"})
        self.assertEqual(len(data["features"]), 30)
        self.assertEqual(len(data["defaulted_fields"]), 25)
        self.assertIn("drift", data)

    @patch("app.prediction_service.predict", return_value={"prediction": 1, "label": "legitimate", "confidence": 0.9})
    @patch("app.drift_service.check")
    @patch("app.enrich_with_reputation")
    def test_predict_url_extracts_features(self, enrich, drift_check, _predict):
        drift_check.return_value = self.drift()
        enrich.return_value = (
            {"Shortining_Service": -1, "SSLfinal_State": -1},
            [{"provider": "google_safe_browsing", "configured": False}],
        )
        response = TestClient(app).post("/predict/url", json={"url": "http://bit.ly/demo"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["extracted_features"]["Shortining_Service"], -1)
        self.assertEqual(data["extracted_features"]["SSLfinal_State"], -1)
        self.assertIn("reputation_checks", data)


if __name__ == "__main__":
    unittest.main()
