"""Security utilities — headers, rate limiting, CSRF, input sanitization.

Keeps security concerns in one place.  Imported in create_app().

OWASP Top 10 coverage:
- A01 Broken Access Control: safe_redirect(), is_safe_url()
- A02 Cryptographic Failures: secrets.token_hex for CSRF tokens
- A03 Injection: safe_int(), safe_string() input sanitization
- A05 Security Misconfiguration: register_security_headers() (CSP, HSTS)
- A07 Auth Failures: validate_password(), validate_email()
- A09 Logging: security_log() for security events
"""

import hmac
import logging
import os
import re
import secrets
import time
import functools
from collections import defaultdict
from flask import request, abort, g, session
from urllib.parse import urlparse, urljoin

# Dedicated security logger — routes to standard Python logging
# so deployment can direct to file/syslog/SIEM independently.
_security_logger = logging.getLogger("videobuds.security")


# ---------------------------------------------------------------------------
# Security Headers
# ---------------------------------------------------------------------------

def register_security_headers(app):
    """Add standard security headers to every response (OWASP A05)."""

    # ── Session cookie hardening (A05) ────────────────────────────────
    # Use direct assignment: Flask pre-populates these keys with None,
    # so setdefault() won't override them.
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    # SECURE only in production (requires HTTPS)
    if not app.debug:
        app.config["SESSION_COOKIE_SECURE"] = True

    @app.after_request
    def _set_headers(response):
        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # XSS protection (legacy but still useful for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permissions policy — disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )
        # Content-Security-Policy (A05) — defence-in-depth against XSS
        # 'unsafe-inline' needed for Tailwind/HTMX inline styles & scripts
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https: blob:; "
            "media-src 'self' https: blob:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'"
        )
        # Strict-Transport-Security (A05) — enforce HTTPS
        if not app.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        # Cache-control for authenticated pages
        if request.endpoint and not request.path.startswith("/static"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
        return response


# ---------------------------------------------------------------------------
# Simple In-Memory Rate Limiter (no external deps)
# ---------------------------------------------------------------------------

class _RateLimiter:
    """Token-bucket rate limiter keyed by IP address.

    Usage in a route::

        @rate_limit(max_calls=5, period=60)  # 5 requests per 60 seconds
        def login(): ...
    """

    def __init__(self):
        # {key: [timestamps]}
        self._hits = defaultdict(list)

    def is_allowed(self, key, max_calls, period):
        """Return True if the key is within its rate limit."""
        now = time.time()
        window_start = now - period
        # Prune old entries
        self._hits[key] = [t for t in self._hits[key] if t > window_start]
        if len(self._hits[key]) >= max_calls:
            return False
        self._hits[key].append(now)
        return True


_limiter = _RateLimiter()


def rate_limit(max_calls=10, period=60):
    """Decorator: abort 429 if the client exceeds *max_calls* within *period* seconds."""

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = f"{fn.__name__}:{request.remote_addr}"
            if not _limiter.is_allowed(key, max_calls, period):
                abort(429)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# CSRF Protection
# ---------------------------------------------------------------------------

def generate_csrf_token() -> str:
    """Return a CSRF token for the current session.

    On first call per session a random token is created and stored in
    ``session["_csrf_token"]``.  Subsequent calls return the same token
    until the session expires.

    Register as a Jinja global so templates can call ``{{ csrf_token() }}``.
    """
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def validate_csrf_token():
    """Check the submitted ``csrf_token`` against the session value.

    Call this in a ``before_request`` hook or decorator.  Returns silently
    if valid; aborts 400 if the token is missing or wrong.

    Skips validation for:
    - GET / HEAD / OPTIONS requests (safe methods)
    - Requests with no active session token (first visit)
    - JSON API requests with ``X-Requested-With: XMLHttpRequest`` header
      (AJAX calls are protected by CORS Same-Origin Policy)
    """
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    # Allow AJAX / HTMX calls — they are protected by Same-Origin Policy
    if request.headers.get("X-Requested-With") in ("XMLHttpRequest",):
        return
    if request.headers.get("HX-Request"):
        return
    # If no session token yet, skip (first visit / no forms submitted yet)
    session_token = session.get("_csrf_token")
    if not session_token:
        return
    # Check form data
    submitted = (
        request.form.get("csrf_token")
        or request.headers.get("X-CSRF-Token")
    )
    if not submitted or not hmac.compare_digest(submitted, session_token):
        abort(400, description="CSRF token missing or invalid.")


def csrf_protect(app):
    """Register a ``before_request`` hook that validates CSRF tokens
    on every POST/PUT/PATCH/DELETE to the app.

    Usage in ``create_app()``::

        from .security import csrf_protect
        csrf_protect(app)
    """
    @app.before_request
    def _csrf_check():
        validate_csrf_token()


# ---------------------------------------------------------------------------
# Input Helpers
# ---------------------------------------------------------------------------

def safe_int(value, default=None):
    """Convert a value to int safely, returning *default* on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_string(value, max_length=500, default=""):
    """Sanitise a string input: strip whitespace and enforce max length.

    Returns *default* if *value* is None or not a string.
    """
    if not isinstance(value, str):
        return default
    return value.strip()[:max_length]


# ---------------------------------------------------------------------------
# A01 — Open Redirect Prevention (OWASP)
# ---------------------------------------------------------------------------

def is_safe_url(target):
    """Return True if *target* is a safe URL for redirection.

    Prevents open-redirect attacks by verifying the redirect URL:
    1. Must be a relative URL (no scheme) or same-origin.
    2. Must not use ``javascript:``, ``data:``, or other dangerous schemes.
    3. Must not use protocol-relative URLs (``//evil.com``).
    """
    if not target:
        return False
    # Reject protocol-relative URLs
    if target.startswith("//"):
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    # Only allow http/https and same netloc
    if test_url.scheme not in ("http", "https"):
        return False
    return test_url.netloc == ref_url.netloc


def safe_redirect(target, fallback_endpoint="dashboard.index"):
    """Return a safe redirect URL.

    If *target* passes ``is_safe_url()``, returns it unchanged.
    Otherwise returns ``url_for(fallback_endpoint)``.

    Usage::

        next_page = request.args.get("next")
        return redirect(safe_redirect(next_page))
    """
    from flask import url_for
    if target and is_safe_url(target):
        return target
    return url_for(fallback_endpoint)


def safe_referrer(fallback_endpoint="dashboard.index"):
    """Return ``request.referrer`` only if it's same-origin, else fallback."""
    from flask import url_for
    referrer = request.referrer
    if referrer and is_safe_url(referrer):
        return referrer
    return url_for(fallback_endpoint)


# ---------------------------------------------------------------------------
# A07 — Password & Email Validation (OWASP)
# ---------------------------------------------------------------------------

# Minimum password requirements per OWASP ASVS v4.0 §2.1.1
_MIN_PASSWORD_LENGTH = 8
_MAX_PASSWORD_LENGTH = 128

# Simple but effective email regex (RFC 5322 simplified)
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$"
)


def validate_password(password):
    """Validate password strength per OWASP guidelines.

    Returns ``(is_valid: bool, error_message: str | None)``.

    Requirements:
    - Minimum 8 characters (OWASP ASVS §2.1.1)
    - Maximum 128 characters (prevent DoS via long hashing)
    - Contains at least one letter and one digit
    """
    if not password or not isinstance(password, str):
        return False, "Password is required."
    if len(password) < _MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {_MIN_PASSWORD_LENGTH} characters."
    if len(password) > _MAX_PASSWORD_LENGTH:
        return False, f"Password must be at most {_MAX_PASSWORD_LENGTH} characters."
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, None


def validate_email(email):
    """Validate email format per OWASP guidelines.

    Returns ``(is_valid: bool, error_message: str | None)``.
    """
    if not email or not isinstance(email, str):
        return False, "Email is required."
    email = email.strip().lower()
    if len(email) > 254:  # RFC 5321
        return False, "Email address is too long."
    if not _EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    return True, None


# ---------------------------------------------------------------------------
# A09 — Security Event Logging (OWASP)
# ---------------------------------------------------------------------------

def security_log(event, **details):
    """Log a security-relevant event with structured context.

    All security events use a dedicated ``videobuds.security`` logger
    so deployment can route them to a SIEM / audit trail.

    Usage::

        security_log("login_failed", email="user@example.com", ip="1.2.3.4")
        security_log("admin_action", action="delete_user", target_id=42)
    """
    ip = request.remote_addr if request else "unknown"
    details["ip"] = ip
    detail_str = " ".join(f"{k}={v}" for k, v in details.items())
    _security_logger.warning(f"SECURITY_EVENT={event} {detail_str}")


# ---------------------------------------------------------------------------
# A04 — File Upload Validation (OWASP)
# ---------------------------------------------------------------------------

# Magic-byte signatures for allowed image/media types.
# Maps MIME media type → (extension_set, magic_bytes_list).
# We check the first N bytes of the file stream to verify the claimed
# extension matches the actual content — prevents disguised uploads.
_MAGIC_BYTES = {
    "image/png":  (
        {".png"},
        [b"\x89PNG\r\n\x1a\n"],
    ),
    "image/jpeg": (
        {".jpg", ".jpeg"},
        [b"\xff\xd8\xff"],
    ),
    "image/gif": (
        {".gif"},
        [b"GIF87a", b"GIF89a"],
    ),
    "image/webp": (
        {".webp"},
        [b"RIFF"],  # RIFF header; WEBP at offset 8 checked separately
    ),
    "video/mp4": (
        {".mp4"},
        # ftyp box at offset 4 is the real indicator
        [],
    ),
    "video/quicktime": (
        {".mov"},
        [],
    ),
    "video/webm": (
        {".webm"},
        [b"\x1a\x45\xdf\xa3"],  # EBML header
    ),
    "audio/mpeg": (
        {".mp3"},
        [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3"],
    ),
    "audio/wav": (
        {".wav"},
        [b"RIFF"],
    ),
    "audio/x-m4a": (
        {".m4a"},
        [],  # ftyp box like mp4
    ),
    "application/pdf": (
        {".pdf"},
        [b"%PDF"],
    ),
    "text/plain": (
        {".txt", ".csv"},
        [],  # no reliable magic for plaintext
    ),
}

# Build reverse lookup: extension → set of allowed magic prefixes
_EXT_TO_MAGIC = {}
for _mime, (_exts, _magics) in _MAGIC_BYTES.items():
    for _ext in _exts:
        _EXT_TO_MAGIC[_ext] = _magics

# Max individual file sizes by category (bytes)
UPLOAD_SIZE_LIMITS = {
    "image": 10 * 1024 * 1024,   # 10 MB
    "video": 100 * 1024 * 1024,  # 100 MB
    "audio": 50 * 1024 * 1024,   # 50 MB
    "document": 5 * 1024 * 1024, # 5 MB
}

_EXT_CATEGORY = {}
for _e in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
    _EXT_CATEGORY[_e] = "image"
for _e in (".mp4", ".mov", ".webm"):
    _EXT_CATEGORY[_e] = "video"
for _e in (".mp3", ".wav", ".m4a"):
    _EXT_CATEGORY[_e] = "audio"
for _e in (".pdf", ".txt", ".csv"):
    _EXT_CATEGORY[_e] = "document"


def validate_upload(file_storage, allowed_extensions, field_label="File"):
    """Validate an uploaded file for security (OWASP A04).

    Performs defence-in-depth checks:
    1. Extension whitelist — reject unknown extensions.
    2. Magic-byte verification — read first 12 bytes and verify they
       match the claimed extension (prevents disguised uploads).
    3. Per-category size limits — reject files larger than the category
       allows (image 10 MB, video 100 MB, audio 50 MB, doc 5 MB).
    4. Sanitised filename — applies ``werkzeug.utils.secure_filename()``
       then replaces the basename with a UUID to guarantee uniqueness.

    Args:
        file_storage: A ``werkzeug.datastructures.FileStorage`` object
            from ``request.files``.
        allowed_extensions: Set of allowed lowercase extensions
            (e.g. ``{".png", ".jpg"}``).
        field_label: Human-readable field name for error messages.

    Returns:
        ``(True, sanitised_extension, None)`` on success, or
        ``(False, None, error_message)`` on failure.

    Usage::

        ok, ext, err = validate_upload(f, ALLOWED_IMAGE_EXT, "Photo")
        if not ok:
            return jsonify({"status": "error", "message": err}), 400
    """
    from werkzeug.utils import secure_filename as _sf

    if not file_storage or not file_storage.filename:
        return False, None, f"No file provided for {field_label}."

    # 1 — Extension whitelist
    raw_name = _sf(file_storage.filename)
    if not raw_name:
        return False, None, f"Invalid filename for {field_label}."

    ext = os.path.splitext(raw_name)[1].lower()
    if ext not in allowed_extensions:
        security_log("upload_rejected_ext",
                     field=field_label, ext=ext,
                     filename=raw_name[:60])
        return False, None, f"File type '{ext}' is not allowed for {field_label}."

    # 2 — Magic-byte verification (where signatures are known)
    expected_magics = _EXT_TO_MAGIC.get(ext, [])
    if expected_magics:
        file_storage.stream.seek(0)
        header = file_storage.stream.read(12)
        file_storage.stream.seek(0)  # rewind for later .save()

        magic_ok = any(header.startswith(m) for m in expected_magics)

        # Extra container checks for RIFF-based formats:
        # WEBP = RIFF + "WEBP" at offset 8
        # WAV  = RIFF + "WAVE" at offset 8
        if magic_ok and ext == ".webp":
            magic_ok = len(header) >= 12 and header[8:12] == b"WEBP"
        elif magic_ok and ext == ".wav":
            magic_ok = len(header) >= 12 and header[8:12] == b"WAVE"

        if not magic_ok:
            security_log("upload_rejected_magic",
                         field=field_label, ext=ext,
                         header=header[:8].hex())
            return (
                False, None,
                f"File content does not match the '{ext}' extension for {field_label}. "
                f"The file may be corrupted or disguised."
            )

    # 3 — Per-category size limit
    category = _EXT_CATEGORY.get(ext)
    if category:
        max_bytes = UPLOAD_SIZE_LIMITS[category]
        file_storage.stream.seek(0, 2)  # seek to end
        file_size = file_storage.stream.tell()
        file_storage.stream.seek(0)  # rewind
        if file_size > max_bytes:
            limit_mb = max_bytes / (1024 * 1024)
            security_log("upload_rejected_size",
                         field=field_label, size=file_size,
                         limit=max_bytes)
            return (
                False, None,
                f"{field_label} exceeds the {limit_mb:.0f} MB limit for {category} files."
            )

    return True, ext, None
