from datetime import datetime, timedelta
from pathlib import Path
import uuid

from flask import Flask, jsonify
from flask_cors import CORS
import yaml
from flask_swagger_ui import get_swaggerui_blueprint

from facturator.adapters.database import get_sqlalchemy_session
from facturator.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from facturator.entrypoints.resources.api import create_api_blueprint
from facturator.entrypoints.resources.auth_routes import auth_bp


app = Flask(__name__, template_folder='templates')
CORS(app)


api_bp = create_api_blueprint(uow=SqlAlchemyUnitOfWork(get_sqlalchemy_session))
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')

# Swagger UI configuration
api_spec = yaml.safe_load((Path(__file__).parent / "api_spec.yaml").read_text())


@app.route('/swagger.json')
def swagger():
    return jsonify(api_spec)


SWAGGER_URL = '/apidocs'
API_URL = '/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Your Flask App"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
