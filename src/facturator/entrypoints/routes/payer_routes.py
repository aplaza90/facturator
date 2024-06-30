
import uuid

from flask import request, jsonify, make_response, abort
from flask_restful import Resource

from pydantic import ValidationError

from facturator.service_layer import handlers
from facturator.service_layer import unit_of_work, messagebus

from facturator.domain import commands
from facturator.entrypoints import schemas
from facturator.entrypoints.flask_app import get_session


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
        payer_id = str(uuid.uuid4())
        cmd = commands.AddPayer(id=payer_id, **payer_data.model_dump())
        payer_dict = messagebus.handle(message=cmd, uow=uow)[0]

        response_data = schemas.PayerItemResponse(**payer_dict)
        return make_response(jsonify(response_data.model_dump()), 201)

