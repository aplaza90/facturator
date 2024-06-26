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


class Payer(Resource):
    
    def get(self, id):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        payer = handlers.get_payer(uow=uow, id=id)
        if payer:
            response_data = schemas.PayerItemResponse(**payer)
            return make_response(jsonify(response_data.model_dump()), 200)
        abort(404, description=f"Payer with ID {id} not found")
  
    def patch(self, id):
        try:
            payer_data = schemas.PatchPayer(**request.json)
        except ValidationError as e:
            return {'error': str(e)}, 400
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.UpdatePayer(
            id=id,
            **payer_data.model_dump()
        )
        payer_dict = handlers.update_payer(uow, cmd)

        if payer_dict:
            response_data = schemas.PayerItemResponse(**payer_dict)
            return make_response(jsonify(response_data.model_dump()), 200)
        
        abort(404, description=f"Payer with ID {id} not found")

    def put(self, id):
        try:
            payer_data = schemas.PostPayer(**request.json)
        except ValidationError as e:
            return {'error': str(e)}, 400
        
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.UpdatePayer(
            id=id,
            **payer_data.model_dump()
        )
        payer_dict = handlers.update_payer(uow, cmd)

        if payer_dict:
            response_data = schemas.PayerItemResponse(**payer_dict)
            return make_response(jsonify(response_data.model_dump()), 200)
        
        abort(404, description=f"Payer with ID {id} not found")
    
    def delete(self, id):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.DeletePayer(id=id)
        try:
            result = handlers.delete_payer(uow=uow, cmd=cmd)
        except Exception:
            return "Integrity violation", 406   
        
        if not result:
            abort(404, description=f"Payer with ID {id} not found")

        return "", 204
        
        
class Payers(Resource):
    
    def get(self):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        name = request.args.get('name')
        payers = handlers.get_payers(uow, name)

        response_data = schemas.PayerListResponse(payers=[schemas.PayerItemResponse(**payer) for payer in payers])

        return make_response(jsonify(response_data.model_dump(mode='json')), 200)

    def post(self):
        try:
            payer_data = schemas.PostPayer(**request.json)
        except ValidationError as e:
            return {'error': str(e)}, 400
                
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        payer_id=str(uuid.uuid4())
        cmd = commands.AddPayer(id=payer_id, **payer_data.model_dump())
        payer_dict = messagebus.handle(message=cmd, uow=uow)[0]

        response_data = schemas.PayerItemResponse(**payer_dict)
        return make_response(jsonify(response_data.model_dump()), 201)


class Order(Resource):
    
    def get(self, id):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        order = handlers.get_order(uow=uow, id=id)
        if order:
            response_data = schemas.OrderItemResponse(**order)
            return make_response(jsonify(response_data.model_dump()), 200)
        abort(404, description=f"Order with ID {id} not found")

    def patch(self, id):
        try:
            order_data = schemas.PatchOrder(**request.json)
        except ValidationError as e:
            return {'error': str(e)}, 400
        
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.UpdateOrder(
            id=id,
            **order_data.model_dump()
        )
        order_dict = handlers.update_order(uow, cmd)
        if order_dict:
            response_data = schemas.OrderItemResponse(**order_dict)
            return make_response(jsonify(response_data.model_dump()), 200)
        
        abort(404, description=f"Payer with ID {id} not found")

    def put(self, id):
        try:
            order_data = schemas.PostOrder(**request.json)
        except ValidationError as e:
            return {'error': str(e)}, 400
        
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.UpdateOrder(
            id=id,
            **order_data.model_dump()
        )
        order_dict = handlers.update_order(uow, cmd)

        if order_dict:
            response_data = schemas.OrderItemResponse(**order_dict)
            return make_response(jsonify(response_data.model_dump()), 200)
        
        abort(404, description=f"Payer with ID {id} not found")
    
    def delete(self, id):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.DeleteOrder(id=id)
        try:
            result = handlers.delete_order(uow=uow, cmd=cmd)
        except Exception:
            return 406, "Integrity violation"   
        
        if not result:
            abort(404, description=f"Payer with ID {id} not found")

        return "", 204


class Orders(Resource):
    
    def get(self):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        payer_name = request.args.get('payer_name')
        orders = handlers.get_orders(uow=uow, payer_name=payer_name)

        response_data = schemas.OrderListResponse(orders=[schemas.OrderItemResponse(**order) for order in orders])

        return make_response(jsonify(response_data.model_dump(mode='json')), 200)

    def post(self):  
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        try:
            order_data = schemas.PostOrder(**request.json)
        except ValidationError as e:
            return {'error': str(e)}, 400
        
        order_id = str(uuid.uuid4())
        cmd = commands.AddOrder(order_id, **order_data.model_dump())
        order_dict = messagebus.handle(message=cmd, uow=uow)[0]

        response_data = schemas.OrderItemResponse(**order_dict)
        return make_response(jsonify(response_data.model_dump()), 201)


class OrdersFile(Resource):
    def post(self):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        if 'file' not in request.files:
            return 'No file part in the request', 400

        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400

        cmd = commands.UploadOrders(
            file=file, code_fixed_part='TEST', code_starting_number=0
        )
        orders = messagebus.handle(message=cmd, uow=uow)[0]

        response_data = schemas.OrderListResponse(orders=[schemas.OrderItemResponse(**order) for order in orders])

        return make_response(jsonify(response_data.model_dump(mode='json')), 201)


class Invoices(Resource):
    def get(self):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        number = request.args.get('number')
        context = handlers.get_order_context(uow=uow, order_number=number)
        return jsonify(context)


class Pdf(Resource):
    def get(self):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        number = request.args.get('number')
        context = handlers.get_order_context(uow=uow, order_number=number)

        pdf_dir = Path(__file__).resolve().parent.parent / 'service_layer' / 'invoice_generator'
        pdf_filename = f'{context["client_name"]}_{context["invoice_date"]}.pdf'
        pdf_path = os.path.join(pdf_dir, pdf_filename)

        @after_this_request
        def remove_file(response):
             try:
                os.remove(pdf_path)
             except Exception as error:
                 app.logger.error(f"Error removing or closing downloaded file handle: {error}")
             return response

        invoice.create_pdf(context)
        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename, mimetype='application/pdf')


api.add_resource(Payer, '/payers/<id>')
api.add_resource(Payers, '/payers')
api.add_resource(Order, '/orders/<id>')
api.add_resource(Orders, '/orders')
api.add_resource(OrdersFile, '/orders/file')
api.add_resource(Invoices, '/invoices')
api.add_resource(Pdf, '/pdfs')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
