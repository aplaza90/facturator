from flask import Blueprint
from flask_restful import Api
from facturator.entrypoints.resources.rest_api.payer_routes import Payer, Payers
from facturator.entrypoints.resources.rest_api.order_routes import Order, Orders, OrdersFile
from facturator.entrypoints.resources.rest_api.invoices_routes import Invoices, Pdf
from facturator.service_layer.unit_of_work import AbstractUnitOfWork


def create_api_blueprint(uow: AbstractUnitOfWork):
    api_bp = Blueprint('rest_api', __name__)
    api = Api(api_bp)

    api.add_resource(Payer, '/payers/<id>', resource_class_kwargs={'uow': uow})
    api.add_resource(Payers, '/payers', resource_class_kwargs={'uow': uow})
    api.add_resource(Order, '/orders/<id>', resource_class_kwargs={'uow': uow})
    api.add_resource(Orders, '/orders', resource_class_kwargs={'uow': uow})
    api.add_resource(OrdersFile, '/orders/file', resource_class_kwargs={'uow': uow})
    api.add_resource(Invoices, '/invoices', resource_class_kwargs={'uow': uow})
    api.add_resource(Pdf, '/pdfs', resource_class_kwargs={'uow': uow})

    return api_bp
