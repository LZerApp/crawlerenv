from flask import Flask
from config import Config


def create_app():
    """Initialize the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)

    with app.app_context():
        from . import blueprints, services
        blueprints.init_app(app)
        services.init_app(app)

        return app
