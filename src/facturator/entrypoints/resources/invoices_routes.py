import os
from pathlib import Path

from flask import request, jsonify, after_this_request, send_file
from flask_restful import Resource


from facturator.service_layer import handlers
from facturator.service_layer import unit_of_work

from facturator.entrypoints.flask_app import get_session
from facturator.service_layer.invoice_generator import invoice


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
                 pass
             return response

        invoice.create_pdf(context)
        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename, mimetype='application/pdf')