from flask import Flask


def init_app(app: Flask):
    from .resources.media import media_bp
    app.register_blueprint(media_bp, url_prefix='/api')
