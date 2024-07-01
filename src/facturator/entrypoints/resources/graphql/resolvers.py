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


@mutation.field("createPayer")
def resolve_create_payer(*_, name, nif, address, zip_code, city, province):
    payer_id = str(uuid.uuid4())
    cmd = commands.AddPayer(
        id=payer_id,
        name=name,
        nif=nif,
        address=address,
        zip_code=zip_code,
        city=city,
        province=province
    )
    payer_dict = messagebus.handle(message=cmd, uow=uow)[0]
    return payer_dict


schema_path = Path(__file__).parent / "schema.graphql"
type_defs = schema_path.read_text(encoding='utf-8')

schema = make_executable_schema(type_defs, query, mutation)

explorer_html = ExplorerGraphiQL().html(None)
