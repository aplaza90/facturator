from flask import Flask, jsonify, request
from flask_cors import CORS
from ariadne import QueryType, graphql_sync, make_executable_schema

from facturator.adapters.database import get_sqlalchemy_session
from facturator.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from facturator.entrypoints.resources.rest_api.api import create_api_blueprint
from facturator.entrypoints.resources.auth.auth_routes import auth_bp
from facturator.entrypoints.resources.rest_api.swagger import create_swagger_blueprint
from facturator.entrypoints.resources.graphql.graphql_api import graphql_bp

app = Flask(__name__, template_folder='templates')
CORS(app)


api_bp = create_api_blueprint(uow=SqlAlchemyUnitOfWork(get_sqlalchemy_session))
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')

# Swagger UI configuration
swagger_bp = create_swagger_blueprint()
app.register_blueprint(swagger_bp)

app.register_blueprint(graphql_bp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
