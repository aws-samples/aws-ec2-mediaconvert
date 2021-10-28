from flask import Flask
from flask_cors import CORS
from config.config import app_config
from app import www, api


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # order matters
    app.config.from_pyfile('sensitive.py')
    app.config.from_object(app_config[app.config['DEVELOPMENT_STAGE']])

    app.url_map.strict_slashes = False

    www.init_app(app)
    api.init_app(app)

    # enable CORS
    CORS(app)

    return app
