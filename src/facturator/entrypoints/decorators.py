from functools import wraps
from flask import request, make_response, jsonify
import jwt
from datetime import datetime

from facturator import config
from facturator.domain.model import User


def token_required(session):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = request.cookies.get('token')
            if not token:
                return make_response(jsonify({"message": "A valid token is missing!"}), 401)
            try:
                data = jwt.decode(token, config.get_app_secret_key(), algorithms=['HS256'])
                current_user = session.query(User).filter_by(public_id=data['public_id']).first()
                if not current_user:
                    return make_response(jsonify({"message": "Invalid token!"}), 401)
                
                if 'exp' in data:
                      current_time = datetime.utcnow()
                      if current_time > datetime.fromtimestamp(data['exp']):
                          return make_response(jsonify({"message": "Token has expired!"}), 401)
                      
            except jwt.ExpiredSignatureError:
                return make_response(jsonify({"message": "Token has expired!"}), 401)          
            except jwt.InvalidTokenError:
                return make_response(jsonify({"message": "Invalid token!"}), 401)

            return f(current_user, *args, **kwargs)
        return wrapper
    return decorator
