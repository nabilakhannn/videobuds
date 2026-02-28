"""Register all Flask blueprints."""


def register_blueprints(app):
    from .auth import auth_bp
    from .dashboard import dashboard_bp
    from .brands import brands_bp
    from .campaigns import campaigns_bp
    from .posts import posts_bp
    from .generate import generate_bp
    from .export import export_bp
    from .api import api_bp
    from .recipes import recipes_bp
    from .personas import personas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(brands_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(generate_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(recipes_bp)
    app.register_blueprint(personas_bp)
