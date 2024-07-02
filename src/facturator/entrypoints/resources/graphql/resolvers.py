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
def resolve_get_payer(*_, item_id):
    payer = handlers.get_payer(uow=uow, item_id=item_id)
    if payer:
        return payer
    return None


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
def resolve_update_payer(*_, item_id, input):
    try:
        payer_data = input
        cmd = commands.UpdatePayer(
            id=item_id,
            **payer_data
        )
        payer_dict = handlers.update_payer(uow=uow, cmd=cmd)

        if payer_dict:
            return payer_dict
        
        raise ItemNotFoundError(f"Payer with ID {item_id} not found")
    
    except Exception as e:
        return None


@mutation.field("deletePayer")
def resolve_delete_payer(*_, item_id):
    try:
        cmd = commands.DeletePayer(id=item_id)
        result = handlers.delete_payer(uow=uow, cmd=cmd)
        if result:
            return f"Payer with ID {item_id} deleted successfully"
        
        raise ItemNotFoundError(f"Payer with ID {item_id} not found")
    
    except Exception as e:
        return f"Error deleting payer: {str(e)}"


@query.field("getOrder")
def resolve_get_order(*_, item_id):
    order = handlers.get_order(uow=uow, item_id=item_id, recursive=True)
    if order:
        return order
    return None


@query.field("getOrders")
def resolve_get_orders(*_, payer_name=None):
    orders = handlers.get_orders(uow=uow, payer_name=payer_name, recursive=True)
    return orders


@mutation.field("createOrder")
def resolve_create_order(*_, input):
    order_id = str(uuid.uuid4())
    cmd = commands.AddOrder(
        id=order_id,
        payer_name=input.get('payer_name'),
        date=input.get('date'),
        quantity=input.get('quantity'),
        number=input.get('number')
    )
    order = handlers.add_order(cmd=cmd, uow=uow, recursive=True)
    return order


@mutation.field("updateOrder")
def resolve_update_order(*_, item_id, input):
    try:
        order_data = input
        cmd = commands.UpdateOrder(
            id=item_id,
            **order_data
        )
        order_dict = handlers.update_order(
            uow=uow, cmd=cmd, recursive=True
        )

        if order_dict:
            return order_dict
        
        raise ItemNotFoundError(f"Payer with ID {item_id} not found")
    
    except Exception as e:
        return None


@mutation.field("deleteOrder")
def resolve_delete_order(*_, item_id):
    try:
        cmd = commands.DeleteOrder(id=item_id)
        result = handlers.delete_order(uow=uow, cmd=cmd)
        if result:
            return f"Order with ID {item_id} deleted successfully"
        
        raise ItemNotFoundError(f"Order with ID {item_id} not found")
    
    except Exception as e:
        return f"Error deleting order: {str(e)}"


schema_path = Path(__file__).parent / "schema.graphql"
type_defs = schema_path.read_text(encoding='utf-8')

schema = make_executable_schema(type_defs, query, mutation)

explorer_html = ExplorerGraphiQL().html(None)
