"""Test login URL resolution without requiring a Home Assistant installation."""

import importlib.util
from pathlib import Path
import unittest


# Import the standalone helper without executing the integration's __init__.py.
AUTH_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "fronius_fleet"
    / "auth.py"
)
spec = importlib.util.spec_from_file_location("fronius_fleet_auth", AUTH_PATH)
auth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth)


class LoginURLTests(unittest.TestCase):
    """Cover the URL formats supplied by redirects and login forms."""

    def test_login_form_actions(self):
        page_url = "https://login.fronius.com/authenticationendpoint/login.do?session=123"
        cases = (
            (
                "https://login.fronius.com/commonauth?sessionDataKey=123",
                "https://login.fronius.com/commonauth?sessionDataKey=123",
            ),
            ("../commonauth", "https://login.fronius.com/commonauth"),
            ("/commonauth", "https://login.fronius.com/commonauth"),
            (
                "commonauth",
                "https://login.fronius.com/authenticationendpoint/commonauth",
            ),
            (
                "//login.fronius.com/commonauth",
                "https://login.fronius.com/commonauth",
            ),
            (
                "?retry=true",
                "https://login.fronius.com/authenticationendpoint/login.do?retry=true",
            ),
        )
        for action, expected in cases:
            with self.subTest(action=action):
                result = auth.resolve_login_url(page_url, action)
                self.assertEqual(result, expected)
                self.assertNotIn("login.fronius.comhttps", result)

    def test_callback_keeps_solarweb_host(self):
        callback_url = "https://www.solarweb.com/signin-oidc"
        self.assertEqual(
            auth.resolve_login_url("https://login.fronius.com/commonauth", callback_url),
            callback_url,
        )

    def test_relative_callback_uses_response_host(self):
        self.assertEqual(
            auth.resolve_login_url("https://www.solarweb.com/Account/Login", "../signin-oidc"),
            "https://www.solarweb.com/signin-oidc",
        )

    def test_relative_redirect(self):
        self.assertEqual(
            auth.resolve_login_url(
                "https://www.solarweb.com/Account/ExternalLogin", "/Account/Login"
            ),
            "https://www.solarweb.com/Account/Login",
        )

    def test_missing_url_raises_clear_error(self):
        for target in (None, "", "   "):
            with self.subTest(target=target):
                with self.assertRaisesRegex(ValueError, "URL is missing"):
                    auth.resolve_login_url("https://login.fronius.com/login", target)


if __name__ == "__main__":
    unittest.main()
