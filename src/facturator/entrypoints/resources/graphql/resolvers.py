import uuid
from pathlib import Path

from ariadne import QueryType, MutationType, make_executable_schema, ObjectType
from ariadne.explorer import ExplorerGraphiQL
from facturator.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from facturator.adapters.database import get_sqlalchemy_session
from facturator.service_layer import handlers
from facturator.entrypoints.resources.graphql.exceptions import ItemNotFoundError
from facturator.domain import commands
from facturator.service_layer import messagebus

uow = SqlAlchemyUnitOfWork(get_sqlalchemy_session)

query = QueryType()
mutation = MutationType()

payer_type = ObjectType("Payer")
invoice_order_type = ObjectType("InvoiceOrder")


@query.field("getPayer")
def resolve_get_payer(*_, id):
    payer = handlers.get_payer(uow=uow, id=id)
    if payer:
        return payer.to_dict()
    raise ItemNotFoundError(f'Product with ID {id} not found')


@query.field("getPayers")
def resolve_get_payers(*_, name=None):
    payers = handlers.get_payers(uow, name)
    return payers


@mutation.field("createPayer")
def resolve_create_payer(*_, input):
    payer_id = str(uuid.uuid4())
    cmd = commands.AddPayer(
        id=payer_id,
        name=input.get("name"),
        nif=input.get("nif"),
        address=input.get("address"),
        zip_code=input.get("zip_code"),
        city=input.get("city"),
        province=input.get("province")
    )
    payer_dict = messagebus.handle(message=cmd, uow=uow)[0]
    return payer_dict


@mutation.field("updatePayer")
def resolve_update_payer(*_, id, input):
    try:
        payer_data = input
        cmd = commands.UpdatePayer(
            id=id,
            **payer_data
        )
        payer_dict = handlers.update_payer(uow=uow, cmd=cmd)

        if payer_dict:
            return payer_dict
        
        raise ItemNotFoundError(f"Payer with ID {id} not found")
    
    except Exception as e:
        return f"Error updating payer: {str(e)}"


@mutation.field("deletePayer")
def resolve_delete_payer(*_, id):
    try:
        cmd = commands.DeletePayer(id=id)
        result = handlers.delete_payer(uow=uow, cmd=cmd)
        if result:
            return f"Payer with ID {id} deleted successfully"
        
        raise ItemNotFoundError(f"Payer with ID {id} not found")
    
    except Exception as e:
        return f"Error deleting payer: {str(e)}"    


schema_path = Path(__file__).parent / "schema.graphql"
type_defs = schema_path.read_text(encoding='utf-8')

schema = make_executable_schema(type_defs, query, mutation)

explorer_html = ExplorerGraphiQL().html(None)
