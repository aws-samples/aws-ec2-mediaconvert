import os
import secrets

# this means ../config
basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class BaseConfig(object):
    SECRET_KEY = secrets.token_urlsafe(16)


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False

    # flask-restful's error handler does not throw it's error to
    # flask's error handler when DEBUG = False
    # PROPAGATE_EXCEPTIONS = True will resolve this problem
    PROPAGATE_EXCEPTIONS = True


class TestConfig(BaseConfig):
    DEBUG = True
    TESTING = True


app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': TestConfig
}
