from datetime import datetime, timedelta
from pathlib import Path
import uuid

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import yaml
from flask_swagger_ui import get_swaggerui_blueprint
from pydantic import ValidationError

from facturator import config
from facturator.adapters.database import get_session
from facturator.domain import model
from facturator.entrypoints import decorators, schemas
from facturator.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from facturator.entrypoints.resources.api import init_api


app = Flask(__name__, template_folder='templates')
CORS(app)


init_api(app=app, uow=SqlAlchemyUnitOfWork(get_session))


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


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
