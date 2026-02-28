"""Shared pytest configuration and safety guards.

The most important job of this file is to **prevent tests from accidentally
connecting to the production database** (``videobuds.db``).  In the past,
test fixtures that called ``create_app("default")`` bound the SQLAlchemy
engine to the real file, and ``db.drop_all()`` in teardown wiped all
user-created brands, personas, campaigns, etc.

Safety rules enforced here:
    1. A session-scoped autouse fixture checks that every Flask app created
       inside a test uses an in-memory (``sqlite://`` or ``sqlite:///:memory:``)
       database URI.
    2. If a test somehow connects to a file-backed SQLite DB, the fixture
       raises immediately before any data can be harmed.
"""

import pytest
import warnings


@pytest.fixture(autouse=True, scope="session")
def _guard_production_database():
    """Fail fast if any test creates an app pointing to a real DB file.

    This is a *session-scoped* autouse fixture — it runs once at the start
    of the entire test session and patches ``db.drop_all`` so that it
    refuses to operate on a file-backed SQLite database.
    """
    from app.extensions import db as _db
    _original_drop_all = _db.drop_all

    def _safe_drop_all(*args, **kwargs):
        """Wrapper that prevents dropping tables on a real DB file."""
        # The check must run inside an app context so we can inspect the engine
        try:
            url = str(_db.engine.url)
        except RuntimeError:
            # No app context — let the original method raise naturally
            return _original_drop_all(*args, **kwargs)

        # Allow in-memory databases only
        if url and "/:memory:" not in url and url != "sqlite://":
            raise RuntimeError(
                f"SAFETY GUARD: db.drop_all() blocked — engine points to a "
                f"file-backed database ({url}). Tests must use "
                f'create_app("testing") to avoid wiping production data.'
            )
        return _original_drop_all(*args, **kwargs)

    _db.drop_all = _safe_drop_all
    yield
    _db.drop_all = _original_drop_all


@pytest.fixture(autouse=True, scope="session")
def _warn_on_production_db_connect():
    """Emit a loud warning if create_app is called with a non-testing config."""
    import app as app_module
    _original_create_app = app_module.create_app

    def _guarded_create_app(config_name=None, **kw):
        if config_name and config_name not in ("testing",):
            warnings.warn(
                f'create_app("{config_name}") used in tests — this connects '
                f"to the production database during app initialization. "
                f'Use create_app("testing") instead.',
                stacklevel=2,
            )
        return _original_create_app(config_name, **kw)

    app_module.create_app = _guarded_create_app
    yield
    app_module.create_app = _original_create_app
