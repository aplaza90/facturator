import datetime
import os
from pathlib import Path
from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from facturator import config
from facturator.adapters import orm
from facturator.service_layer import handlers
from facturator.service_layer import unit_of_work, messagebus
from facturator.service_layer.invoice_generator import invoice
from facturator.domain import commands
from facturator.entrypoints import models

orm.start_mappers()
engine = create_engine(config.get_postgres_uri())
orm.metadata.create_all(engine)
get_session = sessionmaker(bind=engine)
app = Flask(__name__, template_folder='templates')
CORS(app)

api = Api(app)


class Payer(Resource):
    def get(self, id):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        payers = handlers.get_payer(uow=uow, id=id)
        return jsonify(payers)
  
    def patch(self, id):
        try:
            payer_data = models.PatchPayer(**request.json)
        except models.ValidationError as e:
            return {'error': str(e)}, 400
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.UpdatePayer(
            id=id,
            **payer_data.model_dump()
        )
        handlers.update_payer(uow, cmd)
        return "ok", 200
    
    def put(self, id):
        try:
            payer_data = models.PostPayer(**request.json)
        except models.ValidationError as e:
            return {'error': str(e)}, 400
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.UpdatePayer(
            id=id,
            **payer_data.model_dump()
        )
        handlers.update_payer(uow, cmd)
        return "ok", 200
    
    def delete(self, id):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.DeletePayer(id=id)
        try:
            handlers.delete_payer(uow=uow, cmd=cmd)
        except:
            return 406, "Integrity violation"   
        return 200, "OK"
    
class Payers(Resource):
    def get(self):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        name = request.args.get('name')
        payers = handlers.get_payers(uow, name)
        return jsonify(payers)

    def post(self):
        try:
            payer_data = models.PostPayer(**request.json)
        except models.ValidationError as e:
            return {'error': str(e)}, 400
                
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.AddPayer(**payer_data.model_dump())
        messagebus.handle(message=cmd, uow=uow)
        return "OK", 201
    
class Order(Resource):
    def get(self, id):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        orders = handlers.get_order(uow=uow, id=id)
        return jsonify(orders)
    
    def patch(self, id):
        try:
            order_data = models.PatchOrder(**request.json)
        except models.ValidationError as e:
            return {'error': str(e)}, 400
        
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.UpdateOrder(
            id=id,
            **order_data.model_dump()
        )
        handlers.update_order(uow, cmd)
        return "ok", 200
    
    def put(self, id):
        try:
            order_data = models.PostOrder(**request.json)
        except models.ValidationError as e:
            return {'error': str(e)}, 400
        
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.UpdateOrder(
            id=id,
            **order_data.model_dump()
        )
        handlers.update_order(uow, cmd)
        return "ok", 200
    
    def delete(self, id):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.DeleteOrder(id=id)
        try:
            handlers.delete_order(uow=uow, cmd=cmd)
        except:
            return 406, "Integrity violation"   
        return 200, "OK"

class Orders(Resource):
    def get(self):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        payer_name = request.args.get('payer_name')
        orders = handlers.get_orders(uow=uow, payer_name=payer_name)
        return jsonify(orders)

    def post(self):  
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        if request.is_json:
            try:
              order_data = models.PostOrder(**request.json)
            except models.ValidationError as e:
              return {'error': str(e)}, 400
            
            cmd = commands.AddOrder(**order_data.model_dump())
            messagebus.handle(message=cmd, uow=uow)
            return "OK", 201
        
        if 'file' not in request.files:
            return 'No file part in the request', 400

        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400

        cmd = commands.UploadOrders(
            file=file, code_fixed_part='TEST', code_starting_number=0
        )
        messagebus.handle(message=cmd, uow=uow)

        return "OK", 201
    
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


api.add_resource(Payer, '/payer/<id>')
api.add_resource(Payers, '/payer')
api.add_resource(Order, '/order/<id>')
api.add_resource(Orders, '/order')
api.add_resource(Invoices, '/invoice')
api.add_resource(Pdf, '/pdf')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
