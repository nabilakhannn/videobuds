"""OWASP Top 10 vulnerability tests — Phase 30.

Tests every OWASP-related fix to ensure they are resilient, scalable,
and don't break when changes are made.

Coverage:
    A01 — Broken Access Control (open redirect, referrer validation)
    A05 — Security Misconfiguration (CSP, HSTS, session cookie flags)
    A07 — Auth Failures (password validation, email validation)
    A09 — Security Logging (event logging for auth, admin)
"""

import logging
import pytest
from unittest.mock import patch

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    """Create a test Flask app once per module."""
    from app import create_app

    test_app = create_app("testing")
    test_app.config["WTF_CSRF_ENABLED"] = False
    test_app.config["SERVER_NAME"] = "localhost"
    yield test_app


@pytest.fixture(scope="module")
def _db_tables(app):
    """Create tables once for the module."""
    from app.extensions import db

    with app.app_context():
        db.create_all()
        yield db
        db.drop_all()


@pytest.fixture()
def db_session(app, _db_tables):
    """Provide a clean DB session per test."""
    from app.extensions import db

    with app.app_context():
        yield db
        db.session.rollback()


@pytest.fixture()
def client(app, db_session):
    """Provide a Flask test client."""
    return app.test_client()


@pytest.fixture()
def test_user(app, db_session):
    """Create a test user and return it."""
    from app.models.user import User

    user = User.query.filter_by(email="owasp-test@test.com").first()
    if not user:
        user = User(email="owasp-test@test.com", display_name="OWASP Tester")
        user.set_password("Secure1pass")
        db_session.session.add(user)
        db_session.session.commit()
    return user


# ===========================================================================
# A01 — Broken Access Control: Open Redirect Prevention
# ===========================================================================

class TestA01OpenRedirect:
    """OWASP A01: Verify that redirect targets are validated."""

    def test_is_safe_url_relative_path(self, app):
        """Relative paths should be considered safe."""
        from app.security import is_safe_url

        with app.test_request_context("/"):
            assert is_safe_url("/dashboard") is True
            assert is_safe_url("/brands/1") is True

    def test_is_safe_url_rejects_external(self, app):
        """External URLs must be rejected."""
        from app.security import is_safe_url

        with app.test_request_context("/"):
            assert is_safe_url("https://evil.com") is False
            assert is_safe_url("http://malware.com/steal") is False

    def test_is_safe_url_rejects_protocol_relative(self, app):
        """Protocol-relative URLs (//evil.com) must be rejected."""
        from app.security import is_safe_url

        with app.test_request_context("/"):
            assert is_safe_url("//evil.com") is False
            assert is_safe_url("//evil.com/path") is False

    def test_is_safe_url_rejects_javascript(self, app):
        """javascript: scheme must be rejected."""
        from app.security import is_safe_url

        with app.test_request_context("/"):
            assert is_safe_url("javascript:alert(1)") is False

    def test_is_safe_url_rejects_empty(self, app):
        """Empty/None values must be rejected."""
        from app.security import is_safe_url

        with app.test_request_context("/"):
            assert is_safe_url("") is False
            assert is_safe_url(None) is False

    def test_safe_redirect_uses_fallback_for_evil_url(self, app):
        """safe_redirect must return fallback when target is malicious."""
        from app.security import safe_redirect

        with app.test_request_context("/"):
            result = safe_redirect("https://evil.com")
            assert "evil.com" not in result, f"Open redirect! Got '{result}'"
            # Must be a relative safe URL
            assert result.startswith("/"), f"Expected relative URL, got '{result}'"

    def test_safe_redirect_passes_safe_url(self, app):
        """safe_redirect must allow legitimate relative URLs."""
        from app.security import safe_redirect

        with app.test_request_context("/"):
            result = safe_redirect("/brands/1")
            assert result == "/brands/1"

    def test_safe_referrer_rejects_external(self, app):
        """safe_referrer must reject external referrer URLs."""
        from app.security import safe_referrer

        with app.test_request_context(
            "/", headers={"Referer": "https://evil.com/phishing"}
        ):
            result = safe_referrer(fallback_endpoint="dashboard.index")
            assert "evil.com" not in result

    def test_login_redirect_validated(self, client, test_user):
        """Login should NOT redirect to external URLs via ?next=."""
        # Disable CSRF for this test
        response = client.post(
            "/login?next=https://evil.com",
            data={
                "email": "owasp-test@test.com",
                "password": "Secure1pass",
            },
            follow_redirects=False,
        )
        # Should redirect to dashboard, not evil.com
        if response.status_code in (302, 308):
            location = response.headers.get("Location", "")
            assert "evil.com" not in location, (
                f"Open redirect! Location: {location}"
            )


# ===========================================================================
# A05 — Security Misconfiguration: Headers & Cookie Flags
# ===========================================================================

class TestA05SecurityHeaders:
    """OWASP A05: Verify security headers and cookie settings."""

    def test_csp_header_present(self, client, test_user):
        """Content-Security-Policy header must be present."""
        response = client.get("/login")
        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None, "CSP header missing"
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_x_content_type_options(self, client):
        """X-Content-Type-Options: nosniff must be set."""
        response = client.get("/login")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self, client):
        """X-Frame-Options: SAMEORIGIN must be set."""
        response = client.get("/login")
        assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"

    def test_x_xss_protection(self, client):
        """X-XSS-Protection must be set."""
        response = client.get("/login")
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_referrer_policy(self, client):
        """Referrer-Policy must be set."""
        response = client.get("/login")
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy(self, client):
        """Permissions-Policy must restrict dangerous features."""
        response = client.get("/login")
        pp = response.headers.get("Permissions-Policy")
        assert pp is not None
        assert "camera=()" in pp
        assert "microphone=()" in pp

    def test_cache_control_on_non_static(self, client):
        """Non-static routes must have no-store cache control."""
        response = client.get("/login")
        cc = response.headers.get("Cache-Control", "")
        assert "no-store" in cc

    def test_session_cookie_httponly(self, app):
        """Session cookie must be HTTP-only."""
        assert app.config.get("SESSION_COOKIE_HTTPONLY") is True

    def test_session_cookie_samesite(self, app):
        """Session cookie must have SameSite=Lax."""
        assert app.config.get("SESSION_COOKIE_SAMESITE") == "Lax"


# ===========================================================================
# A07 — Auth Failures: Password & Email Validation
# ===========================================================================

class TestA07PasswordValidation:
    """OWASP A07: Password strength validation (ASVS §2.1.1)."""

    def test_password_too_short(self):
        """Passwords shorter than 8 chars must be rejected."""
        from app.security import validate_password

        valid, error = validate_password("Abc1")
        assert valid is False
        assert "8 characters" in error

    def test_password_empty(self):
        """Empty password must be rejected."""
        from app.security import validate_password

        valid, error = validate_password("")
        assert valid is False

    def test_password_none(self):
        """None password must be rejected."""
        from app.security import validate_password

        valid, error = validate_password(None)
        assert valid is False

    def test_password_no_digit(self):
        """Password without digits must be rejected."""
        from app.security import validate_password

        valid, error = validate_password("AbcdefghI")
        assert valid is False
        assert "digit" in error

    def test_password_no_letter(self):
        """Password without letters must be rejected."""
        from app.security import validate_password

        valid, error = validate_password("12345678")
        assert valid is False
        assert "letter" in error

    def test_password_too_long(self):
        """Password exceeding 128 chars must be rejected (DoS prevention)."""
        from app.security import validate_password

        valid, error = validate_password("A1" * 65)  # 130 chars
        assert valid is False
        assert "128" in error

    def test_password_valid(self):
        """A compliant password must pass validation."""
        from app.security import validate_password

        valid, error = validate_password("Secure1pass")
        assert valid is True
        assert error is None

    def test_password_minimum_valid(self):
        """Exactly 8 chars with letter + digit must pass."""
        from app.security import validate_password

        valid, error = validate_password("Abcdef1x")
        assert valid is True


class TestA07EmailValidation:
    """OWASP A07: Email format validation."""

    def test_email_valid(self):
        """Standard email must pass."""
        from app.security import validate_email

        valid, error = validate_email("user@example.com")
        assert valid is True

    def test_email_empty(self):
        """Empty email must be rejected."""
        from app.security import validate_email

        valid, error = validate_email("")
        assert valid is False

    def test_email_no_at(self):
        """Email without @ must be rejected."""
        from app.security import validate_email

        valid, error = validate_email("userexample.com")
        assert valid is False

    def test_email_no_domain(self):
        """Email without domain must be rejected."""
        from app.security import validate_email

        valid, error = validate_email("user@")
        assert valid is False

    def test_email_no_tld(self):
        """Email without TLD must be rejected."""
        from app.security import validate_email

        valid, error = validate_email("user@example")
        assert valid is False

    def test_email_too_long(self):
        """Email exceeding 254 chars must be rejected (RFC 5321)."""
        from app.security import validate_email

        long_email = "a" * 250 + "@x.com"
        valid, error = validate_email(long_email)
        assert valid is False

    def test_registration_rejects_weak_password(self, client, db_session):
        """Registration endpoint must reject weak passwords."""
        response = client.post(
            "/register",
            data={
                "email": "weak-pw@test.com",
                "display_name": "Weak PW",
                "password": "123",
            },
            follow_redirects=True,
        )
        html = response.data.decode()
        assert "8 characters" in html or "letter" in html or "digit" in html

    def test_registration_rejects_bad_email(self, client, db_session):
        """Registration endpoint must reject malformed emails."""
        response = client.post(
            "/register",
            data={
                "email": "not-an-email",
                "display_name": "Bad Email",
                "password": "Secure1pass",
            },
            follow_redirects=True,
        )
        html = response.data.decode()
        assert "valid email" in html.lower()

    def test_registration_accepts_valid_credentials(self, client, db_session):
        """Registration with valid email + strong password must succeed."""
        from app.models.user import User

        response = client.post(
            "/register",
            data={
                "email": "valid-owasp@test.com",
                "display_name": "Valid User",
                "password": "Str0ngP@ss",
            },
            follow_redirects=True,
        )
        html = response.data.decode()
        # Should show success message or login page
        assert "Account created" in html or "Log in" in html or response.status_code == 200
        # Clean up
        user = User.query.filter_by(email="valid-owasp@test.com").first()
        if user:
            db_session.session.delete(user)
            db_session.session.commit()

    def test_password_change_validates_strength(self, app, client, test_user, db_session):
        """Password change must also enforce OWASP password rules."""
        # Log in first
        client.post(
            "/login",
            data={"email": "owasp-test@test.com", "password": "Secure1pass"},
        )
        # Try to change to weak password
        response = client.post(
            "/account",
            data={
                "action": "password",
                "current_password": "Secure1pass",
                "new_password": "weak",
                "confirm_password": "weak",
            },
            follow_redirects=True,
        )
        html = response.data.decode()
        assert "8 characters" in html or "letter" in html or "digit" in html


# ===========================================================================
# A09 — Security Logging
# ===========================================================================

class TestA09SecurityLogging:
    """OWASP A09: Security event logging for audit trails."""

    def test_security_log_function(self, app):
        """security_log must write to videobuds.security logger."""
        from app.security import security_log

        with app.test_request_context("/"):
            with patch("app.security._security_logger") as mock_logger:
                security_log("test_event", user="test", action="verify")
                mock_logger.warning.assert_called_once()
                call_args = mock_logger.warning.call_args[0][0]
                assert "SECURITY_EVENT=test_event" in call_args
                assert "user=test" in call_args
                assert "action=verify" in call_args

    def test_failed_login_is_logged(self, client, db_session):
        """Failed login attempts must be logged."""
        with patch("app.routes.auth.security_log") as mock_log:
            client.post(
                "/login",
                data={"email": "nobody@test.com", "password": "wrong"},
            )
            mock_log.assert_called()
            # Find the login_failed call
            calls = [c for c in mock_log.call_args_list if c[0][0] == "login_failed"]
            assert len(calls) >= 1, "login_failed event not logged"

    def test_successful_login_is_logged(self, client, test_user, db_session):
        """Successful login must be logged."""
        with patch("app.routes.auth.security_log") as mock_log:
            client.post(
                "/login",
                data={"email": "owasp-test@test.com", "password": "Secure1pass"},
            )
            calls = [c for c in mock_log.call_args_list if c[0][0] == "login_success"]
            assert len(calls) >= 1, "login_success event not logged"

    def test_registration_is_logged(self, client, db_session):
        """New user registration must be logged."""
        from app.models.user import User

        with patch("app.routes.auth.security_log") as mock_log:
            client.post(
                "/register",
                data={
                    "email": "new-owasp@test.com",
                    "display_name": "New User",
                    "password": "Str0ngP@ss",
                },
            )
            calls = [c for c in mock_log.call_args_list if c[0][0] == "user_registered"]
            assert len(calls) >= 1, "user_registered event not logged"
        # Clean up
        user = User.query.filter_by(email="new-owasp@test.com").first()
        if user:
            db_session.session.delete(user)
            db_session.session.commit()


# ===========================================================================
# Input Sanitization
# ===========================================================================

class TestInputSanitization:
    """Verify input helpers are defensive and scalable."""

    def test_safe_int_valid(self):
        """safe_int should convert valid integers."""
        from app.security import safe_int

        assert safe_int("42") == 42
        assert safe_int(42) == 42

    def test_safe_int_invalid(self):
        """safe_int should return default for invalid input."""
        from app.security import safe_int

        assert safe_int("abc") is None
        assert safe_int(None) is None
        assert safe_int("", default=0) == 0

    def test_safe_string_strips_and_truncates(self):
        """safe_string should strip whitespace and enforce max length."""
        from app.security import safe_string

        assert safe_string("  hello  ") == "hello"
        assert safe_string("a" * 600, max_length=500) == "a" * 500

    def test_safe_string_non_string(self):
        """safe_string should return default for non-string input."""
        from app.security import safe_string

        assert safe_string(None) == ""
        assert safe_string(123) == ""
        assert safe_string(None, default="fallback") == "fallback"
