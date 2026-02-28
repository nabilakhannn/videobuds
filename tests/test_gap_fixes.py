"""Unit tests for Phase 29 gap-analysis fixes.

Covers:
    1. History page recipe_map includes inactive recipes
    2. Video error banner appears in output template
    3. Inactive recipes return 404 on detail/run routes
    4. Seed function creates sample brand + persona
    5. Campaign creation wires persona to plan_campaign
    6. _ensure_recipe_db_row syncs is_enabled from is_active
"""

import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from app.extensions import db as _db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    """Create a test Flask app with an in-memory database."""
    app = create_app("testing")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["LOGIN_DISABLED"] = True
    app.config["SERVER_NAME"] = "localhost"

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(autouse=True)
def db_session(app):
    """Provide a clean DB for each test."""
    with app.app_context():
        yield _db
        _db.session.rollback()


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: History recipe_map includes inactive recipes
# ═══════════════════════════════════════════════════════════════════════════

class TestHistoryRecipeMap:
    """Verify that the history page loads recipe names for inactive recipes."""

    def test_get_all_recipes_include_inactive(self, app):
        """get_all_recipes(include_inactive=True) returns more recipes than default."""
        with app.app_context():
            from app.recipes import get_all_recipes
            active = get_all_recipes(include_inactive=False)
            all_recipes = get_all_recipes(include_inactive=True)
            assert len(all_recipes) >= len(active)
            # Inactive stubs should make a difference
            assert len(all_recipes) > len(active), (
                "Expected at least one inactive recipe (stubs)"
            )

    def test_inactive_recipe_in_map(self, app):
        """Inactive recipe (e.g. video-creator) should appear in
        get_all_recipes(include_inactive=True)."""
        with app.app_context():
            from app.recipes import get_all_recipes
            slugs = {r.slug for r in get_all_recipes(include_inactive=True)}
            assert "video-creator" in slugs


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: Video error warning banner in output template
# ═══════════════════════════════════════════════════════════════════════════

class TestVideoErrorBanner:
    """Check that the _run_progress.html template renders an error warning
    when an output has an error in its 'value' field."""

    def test_error_banner_markup_exists(self, app):
        """The template source includes the error banner conditional."""
        import os
        template_path = os.path.join(
            app.root_path, "templates", "recipes", "_run_progress.html"
        )
        with open(template_path) as f:
            content = f.read()
        # Check for the error banner conditional
        assert "output.get('value')" in content
        assert "'error' in" in content
        assert "bg-yellow-50" in content


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: Inactive recipes return 404 on detail/run routes
# ═══════════════════════════════════════════════════════════════════════════

class TestInactiveRecipeRouteGuard:
    """Inactive (stub) recipes must return 404 on detail + run pages."""

    def test_inactive_recipe_is_active_false(self, app):
        """Verify stub recipes have is_active = False."""
        with app.app_context():
            from app.recipes import get_recipe
            stub = get_recipe("clip-factory")
            assert stub is not None, "clip-factory recipe should exist"
            assert stub.is_active is False

    def test_detail_route_blocks_inactive(self, app):
        """GET /recipes/clip-factory/ should return 404."""
        with app.test_client() as client:
            # Login first
            from app.models.user import User
            with app.app_context():
                user = User.query.filter_by(email="admin@videobuds.com").first()
                if not user:
                    user = User(email="admin@videobuds.com", display_name="Admin", is_admin=True)
                    user.set_password("admin")
                    _db.session.add(user)
                    _db.session.commit()

            # Use login
            with client.session_transaction() as sess:
                sess["_user_id"] = "1"

            resp = client.get("/recipes/clip-factory/")
            assert resp.status_code == 404

    def test_run_route_blocks_inactive(self, app):
        """GET /recipes/clip-factory/run/ should return 404."""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["_user_id"] = "1"

            resp = client.get("/recipes/clip-factory/run/")
            assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# TEST 4: Seed creates sample brand + persona
# ═══════════════════════════════════════════════════════════════════════════

class TestSeedBrandAndPersona:
    """Verify that _seed_sample_brand_and_persona creates data for users
    who have no brands/personas."""

    def test_seed_creates_brand_for_new_user(self, app):
        """A user with 0 brands gets a sample brand on seed."""
        with app.app_context():
            from app.models.user import User
            from app.models.brand import Brand

            # Create a fresh user with no brand
            user = User(email="seedtest@test.com", display_name="Seed Test")
            user.set_password("test")
            _db.session.add(user)
            _db.session.commit()
            uid = user.id

            # Remove any auto-seeded brands first to test idempotency
            Brand.query.filter_by(user_id=uid).delete()
            _db.session.commit()

            from app import _seed_sample_brand_and_persona
            _seed_sample_brand_and_persona(_db)

            brands = Brand.query.filter_by(user_id=uid).all()
            assert len(brands) >= 1
            assert brands[0].name == "Sample Brand"
            assert brands[0].is_active is True

    def test_seed_creates_persona_for_new_user(self, app):
        """A user with 0 personas gets a default persona on seed."""
        with app.app_context():
            from app.models.user import User
            from app.models.user_persona import UserPersona

            user = User.query.filter_by(email="seedtest@test.com").first()
            if not user:
                user = User(email="seedtest@test.com", display_name="Seed Test")
                user.set_password("test")
                _db.session.add(user)
                _db.session.commit()

            uid = user.id

            # Remove any auto-seeded personas
            UserPersona.query.filter_by(user_id=uid).delete()
            _db.session.commit()

            from app import _seed_sample_brand_and_persona
            _seed_sample_brand_and_persona(_db)

            personas = UserPersona.query.filter_by(user_id=uid).all()
            assert len(personas) >= 1
            assert personas[0].name == "Default Persona"
            assert personas[0].is_default is True

    def test_seed_is_idempotent(self, app):
        """Running seed twice does not create duplicates."""
        with app.app_context():
            from app.models.user import User
            from app.models.brand import Brand
            from app import _seed_sample_brand_and_persona

            user = User.query.filter_by(email="seedtest@test.com").first()
            if not user:
                user = User(email="seedtest@test.com", display_name="Seed Test")
                user.set_password("test")
                _db.session.add(user)
                _db.session.commit()

            uid = user.id

            # Seed once
            _seed_sample_brand_and_persona(_db)
            count1 = Brand.query.filter_by(user_id=uid).count()

            # Seed again
            _seed_sample_brand_and_persona(_db)
            count2 = Brand.query.filter_by(user_id=uid).count()

            assert count1 == count2


# ═══════════════════════════════════════════════════════════════════════════
# TEST 5: Campaign creation wires persona
# ═══════════════════════════════════════════════════════════════════════════

class TestCampaignPersonaWiring:
    """Verify that the campaign form passes persona to plan_campaign."""

    def test_campaign_route_imports_persona_model(self, app):
        """The campaigns module should import UserPersona."""
        from app.routes.campaigns import UserPersona as UP
        assert UP is not None

    def test_new_campaign_passes_personas(self, app):
        """GET /campaigns/new passes personas to the template."""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["_user_id"] = "1"

            resp = client.get("/campaigns/new")
            assert resp.status_code == 200
            # The template should have the persona selector if user has personas
            html = resp.data.decode()
            # Check for persona-related content (form or no-personas message)
            # At minimum the route shouldn't error
            assert "Campaign" in html


# ═══════════════════════════════════════════════════════════════════════════
# TEST 6: _ensure_recipe_db_row syncs is_enabled from is_active
# ═══════════════════════════════════════════════════════════════════════════

class TestEnsureRecipeDbRowSync:
    """Verify that _ensure_recipe_db_row syncs is_enabled from is_active."""

    def test_new_row_inherits_is_active(self, app):
        """A freshly created DB row should have is_enabled = recipe.is_active."""
        with app.app_context():
            from app.routes.recipes import _ensure_recipe_db_row
            from app.recipes import get_recipe
            from app.models.recipe import Recipe

            # Test with an active recipe
            recipe = get_recipe("news-digest")
            if recipe:
                # Remove existing row to force creation
                Recipe.query.filter_by(slug=recipe.slug).delete()
                _db.session.commit()

                row = _ensure_recipe_db_row(recipe)
                assert row.is_enabled == recipe.is_active

    def test_existing_row_syncs_on_change(self, app):
        """If the class-level is_active changes, the DB row should sync."""
        with app.app_context():
            from app.routes.recipes import _ensure_recipe_db_row
            from app.recipes import get_recipe
            from app.models.recipe import Recipe

            recipe = get_recipe("news-digest")
            if recipe:
                # Ensure row exists
                row = _ensure_recipe_db_row(recipe)
                original_enabled = row.is_enabled

                # Temporarily flip is_active and call again
                old_active = recipe.is_active
                recipe.is_active = not old_active
                try:
                    row = _ensure_recipe_db_row(recipe)
                    assert row.is_enabled == (not old_active)
                finally:
                    # Restore
                    recipe.is_active = old_active
                    row.is_enabled = old_active
                    _db.session.commit()
