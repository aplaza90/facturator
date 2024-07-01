from flask import Flask
from flask_cors import CORS

from facturator.adapters.database import get_sqlalchemy_session
from facturator.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from facturator.entrypoints.resources.api import create_api_blueprint
from facturator.entrypoints.resources.auth_routes import auth_bp
from facturator.entrypoints.resources.swagger import create_swagger_blueprint


app = Flask(__name__, template_folder='templates')
CORS(app)


api_bp = create_api_blueprint(uow=SqlAlchemyUnitOfWork(get_sqlalchemy_session))
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')

# Swagger UI configuration
swagger_bp = create_swagger_blueprint()
app.register_blueprint(swagger_bp)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
