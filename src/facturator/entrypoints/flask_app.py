from datetime import datetime, timedelta
import os
from pathlib import Path
import uuid

from flask import Flask, request, jsonify, send_file, after_this_request, make_response, abort
from flask_cors import CORS
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import yaml
from flask_swagger_ui import get_swaggerui_blueprint
from pydantic import ValidationError

from facturator import config
from facturator.adapters import orm
from facturator.service_layer import handlers
from facturator.service_layer import unit_of_work, messagebus
from facturator.service_layer.invoice_generator import invoice
from facturator.domain import commands, model
from facturator.entrypoints import decorators, schemas

orm.start_mappers()
engine = create_engine(config.get_postgres_uri())
orm.metadata.create_all(engine)
get_session = sessionmaker(bind=engine)
app = Flask(__name__, template_folder='templates')
CORS(app)

api = Api(app)

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


@app.route('/signup', methods=['POST'])
def signup_user():
    try:
        signup_data = schemas.SignUp(**request.json)
    except ValidationError:
        return {'error': 'Invalid Signup data'}, 400
    session = get_session()
    hashed_password = generate_password_hash(signup_data.password, method='pbkdf2:sha256')

    user = session.query(model.User).filter_by(username=signup_data.username).first()
    if not user:
        new_user = model.User(
            public_id=str(uuid.uuid4()),
            username = signup_data.username,
            nif = signup_data.nif,
            address = signup_data.address,
            zip_code = signup_data.zip_code,
            city = signup_data.city,
            province = signup_data.province,
            email = signup_data.email,
            password=hashed_password
        )
        session.add(new_user) 
        session.commit() 

        return jsonify({'message': 'registered successfully'}), 201

    return jsonify({"message": "User already exists!"}), 409


@app.route('/login', methods=['POST'])
def login():
    try:
        login_data = schemas.LogIn(**request.json)
    except ValidationError:
        return {'error': 'Invalid LogIn data'}, 400
    
    session = get_session()
    user = session.query(model.User).filter_by(username=login_data.username).first()
    if not user:
        return make_response('Could not verify user!', 401, {'WWW-Authenticate': 'Basic-realm= "No user found!"'})
    
    if check_password_hash(user.password, login_data.password):
        token = jwt.encode(
            {
                'public_id': user.public_id,
                'exp': datetime.utcnow() + timedelta(minutes=30)
            },
            config.get_app_secret_hey(), 
            'HS256'
        )
        response = make_response(jsonify({'message': 'Login successful'}), 201)
        response.set_cookie('token', token, httponly=True, secure=True, samesite='Strict')
        return response


@app.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({'message': 'Logged out successfully'}), 200)
    
    response.delete_cookie('token', path='/') 
    
    return response    


@app.route('/protected', methods=['GET'])
@decorators.token_required(session=get_session())
def protected_resource(current_user):
    return make_response(f'Hello {current_user.username}', 200)


from facturator.entrypoints.routes.payer_routes import Payers, Payer
from facturator.entrypoints.routes.order_routes import Orders, Order, OrdersFile
from facturator.entrypoints.routes.invoices_routes import Invoices, Pdf

api.add_resource(Payer, '/payers/<id>')
api.add_resource(Payers, '/payers')
api.add_resource(Order, '/orders/<id>')
api.add_resource(Orders, '/orders')
api.add_resource(OrdersFile, '/orders/file')
api.add_resource(Invoices, '/invoices')
api.add_resource(Pdf, '/pdfs')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
