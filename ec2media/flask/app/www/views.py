from flask import current_app as app
from flask import Blueprint

www_bp = Blueprint('www', __name__)


@www_bp.route('/health/')
def health():
    app.logger.info("Server is healthy")
    return {'message': 'Healthy'}
