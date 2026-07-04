import unittest

from networksecurity.service.url_intel_service import extract_url_features


class UrlIntelServiceTest(unittest.TestCase):
    def test_extracts_obvious_url_features(self):
        features = extract_url_features("http://bit.ly/a@b")

        self.assertEqual(features["SSLfinal_State"], -1)
        self.assertEqual(features["Shortining_Service"], -1)
        self.assertEqual(features["having_At_Symbol"], -1)
        self.assertEqual(features["having_IP_Address"], 1)


if __name__ == "__main__":
    unittest.main()
