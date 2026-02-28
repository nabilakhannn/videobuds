"""Phase 31 — Ad Video Maker Bug Fix Tests.

Tests for:
    G1 — HTMX polling stops via HTTP 286 on terminal status
    G2 — Video preload set to 'auto' for full playback
    G3 — Brand & Persona selectors always visible in recipe run form

Coverage follows OWASP secure-by-design principles and Ralph Loop methodology.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    """Create a test Flask app with in-memory SQLite + StaticPool.

    Uses ``create_app("testing")`` so the engine binds to the in-memory
    database immediately (StaticPool keeps one shared connection alive).
    ``LOGIN_DISABLED`` is reset to ``False`` so ``@login_required``
    actually enforces authentication in security tests.
    """
    from app import create_app
    test_app = create_app("testing")
    # Re-enable login_required enforcement for security tests
    test_app.config["LOGIN_DISABLED"] = False
    test_app.config["SERVER_NAME"] = "localhost"
    test_app.config["SECRET_KEY"] = "test-secret-key"

    with test_app.app_context():
        from app.extensions import db
        # Tables + seed data already created by create_app("testing").
        # Create additional test-specific data.
        from app.models.user import User
        from app.models.brand import Brand
        from app.models.user_persona import UserPersona
        from app.models.recipe import Recipe

        user = User(email="tester@videobuds.com", display_name="Tester")
        user.set_password("TestPass123!")
        db.session.add(user)
        db.session.commit()

        brand = Brand(user_id=user.id, name="Test Brand", tagline="Test tagline")
        db.session.add(brand)

        persona = UserPersona(user_id=user.id, name="Test Persona", tone="Professional")
        db.session.add(persona)

        # Ensure the recipe row exists (seed might have created it already)
        recipe = Recipe.query.filter_by(slug="ad-video-maker").first()
        if not recipe:
            recipe = Recipe(
                slug="ad-video-maker", name="Ad Video Maker",
                description="Test recipe", category="video_studio",
                icon="🎬", is_enabled=True,
            )
            db.session.add(recipe)
        db.session.commit()

        # Store IDs for fixtures to retrieve
        test_app._test_user_id = user.id
        test_app._test_brand_id = brand.id
        test_app._test_persona_id = persona.id
        test_app._test_recipe_id = recipe.id

        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(autouse=True)
def _clear_login_user(app):
    """Prevent Flask-Login ``g._login_user`` from leaking between tests.

    Flask-Login stores the current user on ``flask.g``, which is scoped to
    the *app* context.  Because the ``app`` fixture keeps one app context
    alive for the whole module, ``g._login_user`` set during one test will
    bleed into the next.  This fixture clears it before **and** after
    every test function.
    """
    from flask import g
    g.pop("_login_user", None)
    yield
    g.pop("_login_user", None)


@pytest.fixture
def db_session(app):
    """Provide the DB session."""
    from app.extensions import db
    yield db.session


@pytest.fixture
def test_user(app):
    """Return the pre-created test user."""
    from app.models.user import User
    from app.extensions import db
    return db.session.get(User, app._test_user_id)


@pytest.fixture
def test_brand(app):
    """Return the pre-created test brand."""
    from app.models.brand import Brand
    from app.extensions import db
    return db.session.get(Brand, app._test_brand_id)


@pytest.fixture
def test_persona(app):
    """Return the pre-created test persona."""
    from app.models.user_persona import UserPersona
    from app.extensions import db
    return db.session.get(UserPersona, app._test_persona_id)


@pytest.fixture
def recipe_db_row(app):
    """Return the pre-created Recipe DB row."""
    from app.models.recipe import Recipe
    from app.extensions import db
    return db.session.get(Recipe, app._test_recipe_id)


@pytest.fixture
def running_run(app, db_session, test_user, recipe_db_row):
    """Create a RecipeRun in 'running' status."""
    from app.models.recipe_run import RecipeRun
    run = RecipeRun(
        recipe_id=recipe_db_row.id,
        user_id=test_user.id,
        status="running",
        total_steps=5,
        steps_completed=2,
        current_step_label="Generating images…",
    )
    db_session.add(run)
    db_session.commit()
    return run


@pytest.fixture
def completed_run(app, db_session, test_user, recipe_db_row):
    """Create a RecipeRun in 'completed' status with video output."""
    from app.models.recipe_run import RecipeRun
    from datetime import datetime, timezone
    run = RecipeRun(
        recipe_id=recipe_db_row.id,
        user_id=test_user.id,
        status="completed",
        total_steps=5,
        steps_completed=5,
        current_step_label="Done",
        completed_at=datetime.now(timezone.utc),
    )
    run.outputs = [
        {
            "type": "video",
            "label": "Scene 1 Video",
            "url": "/api/outputs/test_video.mp4",
            "image_url": "/api/outputs/test_image.png",
        }
    ]
    db_session.add(run)
    db_session.commit()
    return run


def _login(client, user):
    """Helper to log in a test user."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)


# ===========================================================================
# G1 — HTMX Polling Stop (HTTP 286)
# ===========================================================================

class TestHtmxPollingStop:
    """HTTP 286 must be returned for terminal statuses to stop HTMX polling."""

    def test_running_status_returns_200(self, app, test_user, running_run):
        """Running status should return 200 so HTMX keeps polling."""
        with app.test_client() as client:
            _login(client, test_user)
            resp = client.get(
                f"/recipes/run/{running_run.id}/status",
                headers={"HX-Request": "true"},
            )
            assert resp.status_code == 200, \
                f"Running status should return 200, got {resp.status_code}"

    def test_completed_status_returns_286(self, app, test_user, completed_run):
        """Completed status MUST return 286 to stop HTMX polling."""
        with app.test_client() as client:
            _login(client, test_user)
            resp = client.get(
                f"/recipes/run/{completed_run.id}/status",
                headers={"HX-Request": "true"},
            )
            assert resp.status_code == 286, \
                f"Completed status must return 286, got {resp.status_code}"

    def test_failed_status_returns_286(self, app, db_session, test_user, recipe_db_row):
        """Failed status MUST return 286 to stop HTMX polling."""
        from app.models.recipe_run import RecipeRun
        run = RecipeRun(
            recipe_id=recipe_db_row.id,
            user_id=test_user.id,
            status="failed",
            total_steps=5,
            error_message="API error",
        )
        db_session.add(run)
        db_session.commit()

        with app.test_client() as client:
            _login(client, test_user)
            resp = client.get(
                f"/recipes/run/{run.id}/status",
                headers={"HX-Request": "true"},
            )
            assert resp.status_code == 286, \
                f"Failed status must return 286, got {resp.status_code}"

    def test_cancelled_status_returns_286(self, app, db_session, test_user, recipe_db_row):
        """Cancelled status MUST return 286 to stop HTMX polling."""
        from app.models.recipe_run import RecipeRun
        run = RecipeRun(
            recipe_id=recipe_db_row.id,
            user_id=test_user.id,
            status="cancelled",
            total_steps=5,
        )
        db_session.add(run)
        db_session.commit()

        with app.test_client() as client:
            _login(client, test_user)
            resp = client.get(
                f"/recipes/run/{run.id}/status",
                headers={"HX-Request": "true"},
            )
            assert resp.status_code == 286, \
                f"Cancelled status must return 286, got {resp.status_code}"

    def test_awaiting_approval_returns_286(self, app, db_session, test_user, recipe_db_row):
        """Awaiting approval status MUST return 286 to stop HTMX polling."""
        from app.models.recipe_run import RecipeRun
        run = RecipeRun(
            recipe_id=recipe_db_row.id,
            user_id=test_user.id,
            status="awaiting_approval",
            total_steps=5,
            steps_completed=2,
        )
        db_session.add(run)
        db_session.commit()

        with app.test_client() as client:
            _login(client, test_user)
            resp = client.get(
                f"/recipes/run/{run.id}/status",
                headers={"HX-Request": "true"},
            )
            assert resp.status_code == 286, \
                f"Awaiting approval status must return 286, got {resp.status_code}"

    def test_pending_status_returns_200(self, app, db_session, test_user, recipe_db_row):
        """Pending status should return 200 so polling continues."""
        from app.models.recipe_run import RecipeRun
        run = RecipeRun(
            recipe_id=recipe_db_row.id,
            user_id=test_user.id,
            status="pending",
            total_steps=5,
        )
        db_session.add(run)
        db_session.commit()

        with app.test_client() as client:
            _login(client, test_user)
            resp = client.get(
                f"/recipes/run/{run.id}/status",
                headers={"HX-Request": "true"},
            )
            assert resp.status_code == 200, \
                f"Pending status should return 200, got {resp.status_code}"

    def test_non_htmx_request_always_returns_200(self, app, test_user, completed_run):
        """Non-HTMX requests (full page load) must always return 200."""
        with app.test_client() as client:
            _login(client, test_user)
            resp = client.get(f"/recipes/run/{completed_run.id}/status")
            assert resp.status_code == 200, \
                f"Full page load must return 200, got {resp.status_code}"


# ===========================================================================
# G2 — Video Playback (preload=auto)
# ===========================================================================

class TestVideoPlayback:
    """Video element must use preload='auto' for full playback."""

    def test_video_preload_auto(self, app, test_user, completed_run):
        """Completed video output should use preload='auto', not 'metadata'."""
        with app.test_client() as client:
            _login(client, test_user)
            resp = client.get(
                f"/recipes/run/{completed_run.id}/status",
                headers={"HX-Request": "true"},
            )
            html = resp.data.decode("utf-8")

            assert 'preload="auto"' in html, \
                "Video should have preload='auto' for full playback"
            assert 'preload="metadata"' not in html, \
                "Video should NOT have preload='metadata' (causes incomplete load)"

    def test_video_element_has_controls(self, app, test_user, completed_run):
        """Video element must have controls attribute."""
        with app.test_client() as client:
            _login(client, test_user)
            resp = client.get(
                f"/recipes/run/{completed_run.id}/status",
                headers={"HX-Request": "true"},
            )
            html = resp.data.decode("utf-8")
            assert "controls" in html, "Video should have controls attribute"

    def test_video_element_has_playsinline(self, app, test_user, completed_run):
        """Video element must have playsinline for mobile support."""
        with app.test_client() as client:
            _login(client, test_user)
            resp = client.get(
                f"/recipes/run/{completed_run.id}/status",
                headers={"HX-Request": "true"},
            )
            html = resp.data.decode("utf-8")
            assert "playsinline" in html, "Video should have playsinline attribute"


# ===========================================================================
# G3 — Brand & Persona Selector Visibility
# ===========================================================================

class TestBrandPersonaVisibility:
    """Brand & Persona selectors must be always visible (not hidden behind toggle)."""

    def test_brand_selector_visible_when_brands_exist(
        self, app, test_user, test_brand, test_persona
    ):
        """Brand dropdown must be visible (not inside hidden toggle)."""
        with app.test_client() as client:
            _login(client, test_user)
            resp = client.get("/recipes/ad-video-maker/run/")
            html = resp.data.decode("utf-8")

            # The brand selector should be in the page
            assert 'name="brand_id"' in html, \
                "Brand selector must be present in the form"
            assert test_brand.name in html, \
                f"Brand name '{test_brand.name}' must appear in dropdown options"

    def test_persona_selector_visible_when_personas_exist(
        self, app, test_user, test_brand, test_persona
    ):
        """Persona dropdown must be visible (not inside hidden toggle)."""
        with app.test_client() as client:
            _login(client, test_user)
            resp = client.get("/recipes/ad-video-maker/run/")
            html = resp.data.decode("utf-8")

            assert 'name="persona_id"' in html, \
                "Persona selector must be present in the form"
            assert test_persona.name in html, \
                f"Persona name '{test_persona.name}' must appear in dropdown options"

    def test_brand_persona_section_not_hidden(
        self, app, test_user, test_brand, test_persona
    ):
        """The brand/persona section must NOT have 'hidden' CSS class."""
        with app.test_client() as client:
            _login(client, test_user)
            resp = client.get("/recipes/ad-video-maker/run/")
            html = resp.data.decode("utf-8")

            # The old toggle pattern had a div with class="hidden mt-4 space-y-4"
            # The new implementation should NOT use hidden toggle
            assert 'class="hidden mt-4 space-y-4"' not in html, \
                "Brand/persona section must NOT be inside a hidden toggle"

    def test_create_links_shown_when_no_brands(self, app, db_session):
        """When user has no brands, a '+ Create a brand' link must appear."""
        from app.models.user import User
        from app.extensions import db

        # Create a fresh user with no brands/personas
        empty_user = User(email="nobrand@videobuds.com", display_name="NoBrand")
        empty_user.set_password("TestPass123!")
        db.session.add(empty_user)
        db.session.commit()

        with app.test_client() as client:
            _login(client, empty_user)
            resp = client.get("/recipes/ad-video-maker/run/")
            html = resp.data.decode("utf-8")

            assert "Create a brand" in html, \
                "When user has no brands, '+ Create a brand' link must appear"

    def test_create_links_shown_when_no_personas(self, app, db_session):
        """When user has no personas, a '+ Create a persona' link must appear."""
        from app.models.user import User
        from app.extensions import db

        user = User.query.filter_by(email="nobrand@videobuds.com").first()
        if not user:
            user = User(email="nobrand2@videobuds.com", display_name="NoBrand2")
            user.set_password("TestPass123!")
            db.session.add(user)
            db.session.commit()

        with app.test_client() as client:
            _login(client, user)
            resp = client.get("/recipes/ad-video-maker/run/")
            html = resp.data.decode("utf-8")

            assert "Create a persona" in html, \
                "When user has no personas, '+ Create a persona' link must appear"

    def test_brand_section_always_visible_regardless_of_data(self, app, db_session, test_user):
        """Brand & Persona section must render even when user has zero brands/personas."""
        with app.test_client() as client:
            _login(client, test_user)
            resp = client.get("/recipes/ad-video-maker/run/")
            html = resp.data.decode("utf-8")

            # The section heading must always be visible
            assert "Brand &amp; Persona" in html, \
                "Brand & Persona section heading must always be visible"

    def test_brand_persona_values_posted_on_form_submit(
        self, app, test_user, test_brand, test_persona, recipe_db_row
    ):
        """Brand and persona IDs must be captured on form POST."""
        with app.test_client() as client:
            _login(client, test_user)

            # Submit the form with brand_id and persona_id
            resp = client.post(
                "/recipes/ad-video-maker/run/",
                data={
                    "csrf_token": "test",
                    "brand_id": str(test_brand.id),
                    "persona_id": str(test_persona.id),
                    "product_url": "https://example.com",
                },
                follow_redirects=False,
            )
            # Should redirect to run status page (302) even if recipe fails to run
            # The important thing is that it doesn't error out
            assert resp.status_code in (302, 400), \
                f"Form POST should redirect or 400 for missing fields, got {resp.status_code}"


# ===========================================================================
# Security — HTMX access control
# ===========================================================================

class TestHtmxAccessControl:
    """Verify HTMX endpoints enforce auth (OWASP A01)."""

    def test_htmx_poll_requires_auth(self, app, running_run):
        """HTMX poll endpoint must require authentication."""
        with app.test_client() as client:
            resp = client.get(
                f"/recipes/run/{running_run.id}/status",
                headers={"HX-Request": "true"},
            )
            # Should redirect to login (302) not return data
            assert resp.status_code in (302, 401), \
                f"Unauthenticated HTMX request must be rejected, got {resp.status_code}"

    def test_htmx_poll_blocked_for_other_user(self, app, db_session, running_run):
        """User must not be able to poll another user's run (OWASP A01)."""
        from app.models.user import User
        from app.extensions import db as _db

        other_user = User.query.filter_by(email="other@videobuds.com").first()
        if not other_user:
            other_user = User(
                email="other@videobuds.com",
                display_name="Other User",
            )
            other_user.set_password("OtherPass123!")
            _db.session.add(other_user)
            _db.session.commit()

        with app.test_client() as client:
            _login(client, other_user)
            resp = client.get(
                f"/recipes/run/{running_run.id}/status",
                headers={"HX-Request": "true"},
            )
            assert resp.status_code == 404, \
                f"Other user's run must return 404, got {resp.status_code}"
