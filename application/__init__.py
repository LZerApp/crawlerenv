# -*- coding: utf-8 -*-
"""Main application package."""
from flask import Flask
from config import Config


def create_app():
    """Initialize the core application.
    Create application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.
    :param config_object: The configuration object to use.
    """
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)

    with app.app_context():
        from . import blueprints, services
        blueprints.init_app(app)
        services.init_app(app)

        return app
