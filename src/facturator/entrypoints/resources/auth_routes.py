
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from pydantic import ValidationError

from facturator import config
from facturator.adapters.database import get_sqlalchemy_session
from facturator.domain import model
from facturator.entrypoints import schemas, decorators

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['POST'])
def signup_user():
    try:
        signup_data = schemas.SignUp(**request.json)
    except ValidationError:
        return {'error': 'Invalid Signup data'}, 400
    session = get_sqlalchemy_session()
    hashed_password = generate_password_hash(signup_data.password, method='pbkdf2:sha256')

    user = session.query(model.User).filter_by(username=signup_data.username).first()
    if not user:
        new_user = model.User(
            public_id=str(uuid.uuid4()),
            username=signup_data.username,
            nif=signup_data.nif,
            address=signup_data.address,
            zip_code=signup_data.zip_code,
            city=signup_data.city,
            province=signup_data.province,
            email=signup_data.email,
            password=hashed_password
        )
        session.add(new_user)
        session.commit()

        return jsonify({'message': 'registered successfully'}), 201

    return jsonify({"message": "User already exists!"}), 409


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        login_data = schemas.LogIn(**request.json)
    except ValidationError:
        return {'error': 'Invalid LogIn data'}, 400

    session = get_sqlalchemy_session()
    user = session.query(model.User).filter_by(username=login_data.username).first()
    if not user:
        return make_response('Could not verify user!', 401, {'WWW-Authenticate': 'Basic realm="No user found!"'})

    if check_password_hash(user.password, login_data.password):
        token = jwt.encode(
            {
                'public_id': user.public_id,
                'exp': datetime.utcnow() + timedelta(minutes=30)
            },
            config.get_app_secret_key(),
            'HS256'
        )
        response = make_response(jsonify({'message': 'Login successful'}), 201)
        response.set_cookie('token', token, httponly=True, secure=True, samesite='Strict')
        return response


@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({'message': 'Logged out successfully'}), 200)
    response.delete_cookie('token', path='/')
    return response


@auth_bp.route('/protected', methods=['GET'])
@decorators.token_required(session=get_sqlalchemy_session())
def protected_resource(current_user):
    return make_response(f'Hello {current_user.username}', 200)
