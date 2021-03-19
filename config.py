from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

ENV_VARIABLE = {
    'SERVER_URL': environ.get('SERVER_URL', ''),
    'SERVER_TOKEN': environ.get('SERVER_TOKEN', '')
}


class Config:
    """Base config."""
    DEBUG = False
    TESTING = False
    SCHEDULER_API_ENABLED = True
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'


class ProductionConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    DATABASE_URI = environ.get('PROD_DATABASE_URI')
    UPLOAD_TOKEN = environ.get('PROD_UPLOAD_TOKEN')


class DevelopmentConfig(Config):
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = True
    DATABASE_URI = environ.get('DEV_DATABASE_URI')
    UPLOAD_TOKEN = environ.get('DEV_UPLOAD_TOKEN')


class TestingConfig(Config):
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = True
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
