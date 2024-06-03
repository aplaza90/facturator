import os
from pathlib import Path
from flask import Flask, request, render_template, jsonify, send_file, after_this_request
from flask_cors import CORS
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

@app.route('/order', methods=['GET', 'POST'])
def order():
    uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
    if request.method == 'POST':
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
    number = request.args.get("number")
    if number:
        orders = handlers.get_order(uow=uow, number=number)
        return jsonify(orders), 200
    orders = handlers.get_orders(uow)
    return jsonify(orders), 200


@app.route("/payer", methods=['GET', 'POST'])
def payer():
    uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
    if request.method == 'POST':
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
    name = request.args.get("name")
    if name:
        payers = handlers.get_payer(uow=uow, name=name)
        return jsonify(payers), 200
    payers = handlers.get_payers(uow)
    return jsonify(payers), 200


@app.route("/get_context", methods=['GET', 'POST'])
def get_order_context():
    if request.method == 'POST':
        order_number = request.json["order_number"]
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        context = handlers.get_order_context(uow=uow, order_number=order_number)

        # Path where the PDF will be generated
        pdf_dir = Path(__file__).resolve().parent.parent / 'service_layer' / 'invoice_generator'
        pdf_filename = f'{context["client_name"]}_{context["invoice_date"]}.pdf'
        pdf_path = os.path.join(pdf_dir, pdf_filename)

        invoice.create_pdf(context)

        @after_this_request
        def remove_file(response):
            try:
                os.remove(pdf_path)
            except Exception as error:
                app.logger.error(f"Error removing or closing downloaded file handle: {error}")
            return response

        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename, mimetype='application/pdf')

    return render_template("get_pdf.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
