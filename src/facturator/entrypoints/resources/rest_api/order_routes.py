import uuid

from flask import request, jsonify, make_response, abort
from flask_restful import Resource

from pydantic import ValidationError

from facturator.service_layer import handlers
from facturator.service_layer import messagebus

from facturator.domain import commands
from facturator.entrypoints import schemas
from facturator.service_layer.unit_of_work import AbstractUnitOfWork


class Order(Resource):
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    def get(self, item_id):
        order = handlers.get_order(uow=self.uow, id=item_id)
        if order:
            response_data = schemas.OrderItemResponse(**order)
            return make_response(jsonify(response_data.model_dump()), 200)
        abort(404, description=f"Order with ID {item_id} not found")

    def patch(self, item_id):
        try:
            order_data = schemas.PatchOrder(**request.json)
        except ValidationError as e:
            return {'error': str(e)}, 400

        cmd = commands.UpdateOrder(
            id=item_id,
            **order_data.model_dump()
        )
        order_dict = handlers.update_order(uow=self.uow, cmd=cmd)
        if order_dict:
            response_data = schemas.OrderItemResponse(**order_dict)
            return make_response(jsonify(response_data.model_dump()), 200)

        abort(404, description=f"Payer with ID {item_id} not found")

    def put(self, item_id):
        try:
            order_data = schemas.PostOrder(**request.json)
        except ValidationError as e:
            return {'error': str(e)}, 400

        cmd = commands.UpdateOrder(
            id=item_id,
            **order_data.model_dump()
        )
        order_dict = handlers.update_order(uow=self.uow, cmd=cmd)

        if order_dict:
            response_data = schemas.OrderItemResponse(**order_dict)
            return make_response(jsonify(response_data.model_dump()), 200)

        abort(404, description=f"Payer with ID {item_id} not found")

    def delete(self, item_id):
        cmd = commands.DeleteOrder(id=item_id)
        try:
            result = handlers.delete_order(uow=self.uow, cmd=cmd)
        except Exception:
            return 406, "Integrity violation"

        if not result:
            abort(404, description=f"Payer with ID {item_id} not found")

        return "", 204


class Orders(Resource):
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    def get(self):
        payer_name = request.args.get('payer_name')
        orders = handlers.get_orders(uow=self.uow, payer_name=payer_name)

        response_data = schemas.OrderListResponse(orders=[schemas.OrderItemResponse(**order) for order in orders])

        return make_response(jsonify(response_data.model_dump(mode='json')), 200)

    def post(self):
        try:
            order_data = schemas.PostOrder(**request.json)
        except ValidationError as e:
            return {'error': str(e)}, 400

        order_id = str(uuid.uuid4())
        cmd = commands.AddOrder(order_id, **order_data.model_dump())
        order_dict = messagebus.handle(message=cmd, uow=self.uow)[0]

        response_data = schemas.OrderItemResponse(**order_dict)
        return make_response(jsonify(response_data.model_dump()), 201)


class OrdersFile(Resource):
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    def post(self):
        if 'file' not in request.files:
            return 'No file part in the request', 400

        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400

        cmd = commands.UploadOrders(
            file=file, code_fixed_part='TEST', code_starting_number=0
        )
        orders = messagebus.handle(message=cmd, uow=self.uow)[0]

        response_data = schemas.OrderListResponse(orders=[schemas.OrderItemResponse(**order) for order in orders])

        return make_response(jsonify(response_data.model_dump(mode='json')), 201)
