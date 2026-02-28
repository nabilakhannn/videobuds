"""Flask application factory."""

import os
from flask import Flask
from .config import config_map
from .extensions import db, login_manager


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="static",
        template_folder="templates",
    )
    app.config.from_object(config_map[config_name])

    # Ensure instance and upload dirs exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["GENERATED_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Custom Jinja filters (extracted to app/filters.py for SRP)
    from .filters import register_filters
    register_filters(app)

    # Inject timedelta into Jinja globals for date arithmetic in templates
    from datetime import timedelta
    app.jinja_env.globals["timedelta"] = timedelta

    # Security headers + CSRF
    from .security import register_security_headers, generate_csrf_token, csrf_protect
    register_security_headers(app)
    csrf_protect(app)

    # Make csrf_token() available in all templates
    app.jinja_env.globals["csrf_token"] = generate_csrf_token

    # Register blueprints
    from .routes import register_blueprints
    register_blueprints(app)

    # Global template context — inject active_brand, brands, and recipe_count for nav
    @app.context_processor
    def inject_global_context():
        from flask_login import current_user as _cu
        ctx = {"brands": [], "active_brand": None, "total_recipe_count": 0}
        if _cu and _cu.is_authenticated:
            from .models import Brand
            ctx["brands"] = Brand.query.filter_by(user_id=_cu.id).order_by(Brand.name).all()
            ctx["active_brand"] = Brand.query.filter_by(user_id=_cu.id, is_active=True).first()
            try:
                from .recipes import recipe_count
                ctx["total_recipe_count"] = recipe_count()
            except Exception:
                ctx["total_recipe_count"] = 0
        return ctx

    # Initialize PostHog analytics (fails silently if not configured)
    from .services.analytics_service import init_posthog
    init_posthog(app.config.get("POSTHOG_API_KEY"), app.config.get("POSTHOG_HOST"))

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def too_many_requests(e):
        from flask import render_template, request
        if request.accept_mimetypes.best == "application/json":
            return {"error": "Too many requests. Please slow down."}, 429
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("errors/500.html"), 500

    # Create tables and seed default admin account
    with app.app_context():
        from . import models  # noqa: F401 — ensure models are imported
        db.create_all()

        # Auto-create admin account if no users exist
        from .models.user import User
        if User.query.count() == 0:
            admin = User(
                email="admin@videobuds.com",
                display_name="Nabila",
                is_admin=True,
            )
            admin.set_password("admin")
            db.session.add(admin)
            db.session.commit()

        # Auto-create test user for admin to preview user experience
        if User.query.filter_by(email="user@videobuds.com").first() is None:
            test_user = User(
                email="user@videobuds.com",
                display_name="Test User",
                is_admin=False,
            )
            test_user.set_password("user")
            db.session.add(test_user)
            db.session.commit()

        # Seed sample Brand + Persona for admin so recipes have context
        _seed_sample_brand_and_persona(db)

    return app


def _seed_sample_brand_and_persona(database):
    """Create one sample Brand and one sample Persona for each user that
    has zero brands.  Runs at startup so the recipe 'Brand / Persona'
    dropdowns always have at least one option for demo/testing.

    Idempotent — skips users who already have data.
    """
    from .models.user import User
    from .models.brand import Brand
    from .models.user_persona import UserPersona

    users_without_brands = (
        User.query
        .outerjoin(Brand, Brand.user_id == User.id)
        .filter(Brand.id.is_(None))
        .all()
    )

    for user in users_without_brands:
        brand = Brand(
            user_id=user.id,
            name="Sample Brand",
            tagline="Your tagline here",
            target_audience="Young professionals aged 25-35",
            visual_style="Modern, clean, minimalist",
            brand_doc="This is a sample brand. Edit it to match your real brand guidelines.",
            is_active=True,
        )
        database.session.add(brand)

    users_without_personas = (
        User.query
        .outerjoin(UserPersona, UserPersona.user_id == User.id)
        .filter(UserPersona.id.is_(None))
        .all()
    )

    for user in users_without_personas:
        persona = UserPersona(
            user_id=user.id,
            name="Default Persona",
            tone="professional",
            voice_style="Clear, confident, and approachable",
            bio="A content creator who values quality and authenticity.",
            industry="General",
            target_audience="Broad consumer audience aged 18-45",
            is_default=True,
        )
        database.session.add(persona)

    database.session.commit()
