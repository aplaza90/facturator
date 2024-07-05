from flask import Flask
from flask_cors import CORS

from facturator.adapters.database import get_sqlalchemy_session
from facturator.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from facturator.entrypoints.resources.rest_api.api import create_api_blueprint
from facturator.entrypoints.resources.auth.auth_routes import auth_bp
from facturator.entrypoints.resources.rest_api.swagger import create_swagger_blueprint
from facturator.entrypoints.resources.graphql.graphql_api import create_gql_api_blueprint

app = Flask(__name__)
CORS(app)

uow=SqlAlchemyUnitOfWork(get_sqlalchemy_session)

api_bp = create_api_blueprint(uow=uow)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')

# Swagger UI configuration
swagger_bp = create_swagger_blueprint()
app.register_blueprint(swagger_bp)

graphql_api_bp = create_gql_api_blueprint(uow=uow)
app.register_blueprint(graphql_api_bp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
