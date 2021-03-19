from .main import main_bp


def init_app(app):
    app.register_blueprint(main_bp, url_prefix='/')
