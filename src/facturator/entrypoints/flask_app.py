import os
from pathlib import Path
from flask import Flask, request, render_template, jsonify, send_file, after_this_request
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
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        data = request.json
        cmd = commands.UpdatePayer(
            id=id,
            name=data.get("name"),
            nif=data.get("nif"),
            address=data.get("address"),
            zip_code=data.get("zip_code"),
            city=data.get("city"),
            province=data.get("province"),
        )
        handlers.update_payer(uow, cmd)
        return "ok", 200
    
    def put(self, id):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        data = request.json
        cmd = commands.UpdatePayer(
            id=id,
            name=data["name"],
            nif=data["nif"],
            address=data["address"],
            zip_code=data["zip_code"],
            city=data["city"],
            province=data["province"],
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
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.AddPayer(
            name=request.json["name"],
            nif=request.json["nif"],
            address=request.json["address"],
            zip_code=request.json["zip_code"],
            city=request.json["city"],
            province=request.json["province"],
        )
        messagebus.handle(message=cmd, uow=uow)
        return "OK", 201
    
class Order(Resource):
    def get(self, id):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        orders = handlers.get_order(uow=uow, id=id)
        return jsonify(orders)
    
    def patch(self, id):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        data = request.json
        cmd = commands.UpdateOrder(
            id=id,
            payer_name=data.get("payer_name"),
            date=data.get("date"),
            quantity=data.get("quantity"),
            number=data.get("number")
        )
        handlers.update_order(uow, cmd)
        return "ok", 200
    
    def put(self, id):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        data = request.json
        cmd = commands.UpdateOrder(
            id=id,
            payer_name=data["payer_name"],
            date=data["date"],
            quantity=data["quantity"],
            number=data["number"]
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
        number = request.args.get('number')
        orders = handlers.get_orders(uow=uow, number=number)
        return jsonify(orders)

    def post(self):
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        if request.is_json:
            cmd = commands.AddOrder(
                payer_name=request.json["payer_name"],
                date=request.json["date"],
                quantity=request.json["quantity"],
                number=request.json.get("number"),
            )
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


# @app.route("/get_context", methods=['GET', 'POST'])
# def get_order_context():
#     if request.method == 'POST':
#         order_number = request.json["order_number"]
#         uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
#         context = handlers.get_order_context(uow=uow, order_number=order_number)

#         # Path where the PDF will be generated
#         pdf_dir = Path(__file__).resolve().parent.parent / 'service_layer' / 'invoice_generator'
#         pdf_filename = f'{context["client_name"]}_{context["invoice_date"]}.pdf'
#         pdf_path = os.path.join(pdf_dir, pdf_filename)

#         invoice.create_pdf(context)

#         @after_this_request
#         def remove_file(response):
#             try:
#                 os.remove(pdf_path)
#             except Exception as error:
#                 app.logger.error(f"Error removing or closing downloaded file handle: {error}")
#             return response

#         return send_file(pdf_path, as_attachment=True, download_name=pdf_filename, mimetype='application/pdf')

#     return render_template("get_pdf.html")

api.add_resource(Payer, '/payer/<id>')
api.add_resource(Payers, '/payer')
api.add_resource(Order, '/order/<id>')
api.add_resource(Orders, '/order')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
