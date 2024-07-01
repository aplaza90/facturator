from flask import Blueprint, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from pathlib import Path
import yaml


SWAGGER_URL = '/apidocs'
API_URL = '/swagger.json'

SWAGGER_CONFIG = {
    'app_name': "Your Flask App"
}


def load_api_spec():
    api_spec_path = Path(__file__).parent.parent / "api_spec.yaml"
    return yaml.safe_load(api_spec_path.read_text())


def create_swagger_blueprint():
    swagger_bp = Blueprint('swagger', __name__)

    @swagger_bp.route('/swagger.json')
    def swagger():
        return jsonify(load_api_spec())

    swagger_ui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config=SWAGGER_CONFIG
    )
    swagger_bp.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

    return swagger_bp
