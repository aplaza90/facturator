from flask_restful import Api
from facturator.entrypoints.resources.payer_routes import Payer, Payers
from facturator.entrypoints.resources.order_routes import Order, Orders, OrdersFile
from facturator.entrypoints.resources.invoices_routes import Invoices, Pdf


def init_api(app):
    api = Api(app)

    api.add_resource(Payer, '/payers/<id>')
    api.add_resource(Payers, '/payers')
    api.add_resource(Order, '/orders/<id>')
    api.add_resource(Orders, '/orders')
    api.add_resource(OrdersFile, '/orders/file')
    api.add_resource(Invoices, '/invoices')
    api.add_resource(Pdf, '/pdfs')
