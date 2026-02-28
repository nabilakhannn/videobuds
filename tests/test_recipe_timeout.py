"""Unit tests for recipe execution timeout (L2 — configurable reaper)."""

import pytest
from datetime import datetime, timedelta, timezone


@pytest.fixture
def app():
    """Create a test Flask app with an in-memory database.

    IMPORTANT: Must use ``create_app("testing")`` so the engine points to an
    in-memory SQLite DB — never the production ``videobuds.db``.  Using
    ``create_app("default")`` would bind the engine to the real file during
    ``create_app()``'s ``db.create_all()`` call, and the subsequent
    ``db.drop_all()`` in teardown would **wipe all production data**.
    """
    from app import create_app
    test_app = create_app("testing")

    from app.extensions import db
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def db_session(app):
    """Provide a DB session within the app context."""
    from app.extensions import db
    with app.app_context():
        yield db.session


@pytest.fixture
def test_recipe_id(app, db_session):
    """Create a Recipe row and return its id."""
    from app.models.recipe import Recipe
    recipe = Recipe(slug="test-recipe", name="Test Recipe")
    db_session.add(recipe)
    db_session.commit()
    return recipe.id


class TestRecipeTimeoutConfig:
    def test_default_timeout_is_30(self, app):
        """Config should default to 30 minutes."""
        assert app.config["RECIPE_TIMEOUT_MINUTES"] == 30

    def test_config_value_is_int(self, app):
        assert isinstance(app.config["RECIPE_TIMEOUT_MINUTES"], int)


class TestReapStaleRuns:
    def _create_running_run(self, db_session, recipe_id, started_minutes_ago, user_id=1):
        """Helper: insert a RecipeRun that started N minutes ago."""
        from app.models.recipe_run import RecipeRun
        run = RecipeRun(
            recipe_id=recipe_id,
            user_id=user_id,
            status="running",
            started_at=datetime.now(timezone.utc) - timedelta(minutes=started_minutes_ago),
            total_steps=3,
            steps_completed=0,
        )
        db_session.add(run)
        db_session.commit()
        return run.id

    def test_stale_run_gets_reaped(self, app, db_session, test_recipe_id):
        """A run exceeding the timeout should be marked as failed."""
        from app.routes.recipes import _reap_stale_runs
        from app.models.recipe_run import RecipeRun

        # Create a run that started 45 min ago (exceeds 30-min default)
        run_id = self._create_running_run(db_session, test_recipe_id, started_minutes_ago=45)

        with app.app_context():
            _reap_stale_runs()

        run = db_session.get(RecipeRun, run_id)
        assert run.status == "failed"
        assert "timed out" in run.error_message.lower()
        assert run.completed_at is not None

    def test_fresh_run_not_reaped(self, app, db_session, test_recipe_id):
        """A run within the timeout window should NOT be reaped."""
        from app.routes.recipes import _reap_stale_runs
        from app.models.recipe_run import RecipeRun

        # Create a run that started 5 min ago (well within 30-min default)
        run_id = self._create_running_run(db_session, test_recipe_id, started_minutes_ago=5)

        with app.app_context():
            _reap_stale_runs()

        run = db_session.get(RecipeRun, run_id)
        assert run.status == "running"  # not reaped

    def test_custom_timeout_via_config(self, app, db_session, test_recipe_id):
        """The reaper should respect RECIPE_TIMEOUT_MINUTES config."""
        from app.routes.recipes import _reap_stale_runs
        from app.models.recipe_run import RecipeRun

        # Create a run that started 15 min ago
        run_id = self._create_running_run(db_session, test_recipe_id, started_minutes_ago=15)

        # Set timeout to 10 minutes — the run should be reaped
        app.config["RECIPE_TIMEOUT_MINUTES"] = 10

        with app.app_context():
            _reap_stale_runs()

        run = db_session.get(RecipeRun, run_id)
        assert run.status == "failed"

    def test_explicit_max_age_overrides_config(self, app, db_session, test_recipe_id):
        """Passing max_age_minutes explicitly should override config."""
        from app.routes.recipes import _reap_stale_runs
        from app.models.recipe_run import RecipeRun

        # Create a run that started 20 min ago
        run_id = self._create_running_run(db_session, test_recipe_id, started_minutes_ago=20)

        # Config says 30 min (so run is fresh), but explicit arg says 10 min
        app.config["RECIPE_TIMEOUT_MINUTES"] = 30

        with app.app_context():
            _reap_stale_runs(max_age_minutes=10)

        run = db_session.get(RecipeRun, run_id)
        assert run.status == "failed"

    def test_completed_run_not_affected(self, app, db_session, test_recipe_id):
        """A completed run should never be reaped, even if old."""
        from app.routes.recipes import _reap_stale_runs
        from app.models.recipe_run import RecipeRun

        run_id = self._create_running_run(db_session, test_recipe_id, started_minutes_ago=120)
        # Manually set to completed
        run = db_session.get(RecipeRun, run_id)
        run.status = "completed"
        db_session.commit()

        with app.app_context():
            _reap_stale_runs()

        run = db_session.get(RecipeRun, run_id)
        assert run.status == "completed"
