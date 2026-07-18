import unittest

from broker.fyers_login import FyersLoginError, access_token_from_response, extract_auth_code


class FyersLoginTests(unittest.TestCase):
    def test_extracts_auth_code_from_redirect_url(self):
        url = "https://example.test/callback?state=xyz&auth_code=one-time-code"
        self.assertEqual(extract_auth_code(url), "one-time-code")

    def test_accepts_raw_auth_code(self):
        self.assertEqual(extract_auth_code("one-time-code"), "one-time-code")

    def test_rejects_redirect_without_code(self):
        with self.assertRaises(FyersLoginError):
            extract_auth_code("https://example.test/callback?state=xyz")

    def test_requires_token_in_exchange_response(self):
        with self.assertRaises(FyersLoginError):
            access_token_from_response({"s": "error", "message": "expired code"})

    def test_returns_token_in_exchange_response(self):
        self.assertEqual(access_token_from_response({"access_token": "token-value"}), "token-value")


if __name__ == "__main__":
    unittest.main()
