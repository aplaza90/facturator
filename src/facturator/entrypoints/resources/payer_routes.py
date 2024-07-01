import uuid

from flask import request, jsonify, make_response, abort
from flask_restful import Resource
from pydantic import ValidationError

from facturator.service_layer import handlers
from facturator.service_layer import messagebus
from facturator.domain import commands
from facturator.entrypoints import schemas
from facturator.service_layer.unit_of_work import AbstractUnitOfWork


class Payer(Resource):

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    def get(self, id):
        payer = handlers.get_payer(uow=self.uow, id=id)
        if payer:
            response_data = schemas.PayerItemResponse(**payer)
            return make_response(jsonify(response_data.model_dump()), 200)
        abort(404, description=f"Payer with ID {id} not found")

    def patch(self, id):
        try:
            payer_data = schemas.PatchPayer(**request.json)
        except ValidationError as e:
            return {'error': str(e)}, 400
        cmd = commands.UpdatePayer(
            id=id,
            **payer_data.model_dump()
        )
        payer_dict = handlers.update_payer(self.uow, cmd)

        if payer_dict:
            response_data = schemas.PayerItemResponse(**payer_dict)
            return make_response(jsonify(response_data.model_dump()), 200)

        abort(404, description=f"Payer with ID {id} not found")

    def put(self, id):
        try:
            payer_data = schemas.PostPayer(**request.json)
        except ValidationError as e:
            return {'error': str(e)}, 400

        cmd = commands.UpdatePayer(
            id=id,
            **payer_data.model_dump()
        )
        payer_dict = handlers.update_payer(self.uow, cmd)

        if payer_dict:
            response_data = schemas.PayerItemResponse(**payer_dict)
            return make_response(jsonify(response_data.model_dump()), 200)

        abort(404, description=f"Payer with ID {id} not found")

    def delete(self, id):
        cmd = commands.DeletePayer(id=id)
        try:
            result = handlers.delete_payer(uow=self.uow, cmd=cmd)
        except Exception:
            return "Integrity violation", 406

        if not result:
            abort(404, description=f"Payer with ID {id} not found")

        return "", 204


class Payers(Resource):

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    def get(self):
        name = request.args.get('name')
        payers = handlers.get_payers(self.uow, name)

        response_data = schemas.PayerListResponse(payers=[schemas.PayerItemResponse(**payer) for payer in payers])

        return make_response(jsonify(response_data.model_dump(mode='json')), 200)

    def post(self):
        try:
            payer_data = schemas.PostPayer(**request.json)
        except ValidationError as e:
            return {'error': str(e)}, 400

        payer_id = str(uuid.uuid4())
        cmd = commands.AddPayer(id=payer_id, **payer_data.model_dump())
        payer_dict = messagebus.handle(message=cmd, uow=self.uow)[0]

        response_data = schemas.PayerItemResponse(**payer_dict)
        return make_response(jsonify(response_data.model_dump()), 201)

