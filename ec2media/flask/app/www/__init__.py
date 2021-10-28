from flask import Flask


def init_app(app: Flask):
    from .views import www_bp
    app.register_blueprint(www_bp)
