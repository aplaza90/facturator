from sqlalchemy import text
from typing import TYPE_CHECKING

from facturator.domain import model, commands, events
from facturator.service_layer import file_handler, unit_of_work
from facturator.service_layer.invoice_generator import invoice

if TYPE_CHECKING:
    from facturator.service_layer import unit_of_work


def add_order(
        cmd: commands.AddOrder,
        uow,  
) -> None:
    with uow:

        if not all([cmd.payer_name, cmd.date, cmd.quantity]):
            raise ValueError("All attributes must be provided")
        payer = get_payer_from_name(cmd.payer_name, uow.payers.list_all())

        order = model.InvoiceOrder(
            payer_name=cmd.payer_name.upper(),
            date=cmd.date,
            quantity=cmd.quantity,
            number=cmd.number
        )
        order.allocate_payer(payer)
        uow.orders.add(order)
        uow.commit()

def get_orders(uow, payer_name):
    with uow:
        if payer_name:
            query = text("SELECT * FROM orders WHERE payer_name LIKE :payer_name")
            rows = uow.session.execute(query, dict(payer_name=f"%{payer_name.upper()}%")).all()
        else:    
            query = text("SELECT * FROM orders")
            rows = uow.session.execute(query).all()
        if rows:
            orders = [row._asdict() for row in rows]
            return orders

        return []
    
def get_order(uow, id):
    with uow:
        query = text("SELECT * FROM orders WHERE id = :id") 
        rows = uow.session.execute(query, {'id': id}).all()
        if rows:
            orders = [row._asdict() for row in rows]
            return orders      
    
    return [{'no': 'data'}]

def update_order(uow, cmd):
    with uow:
        order = uow.orders.get_by_id(cmd.id) 
        if cmd.payer_name:
          order.payer_name = cmd.payer_name 
          payer = get_payer_from_name(cmd.payer_name, uow.payers.list_all())
          order.allocate_payer(payer)
        order.date = cmd.date if cmd.date else order.date
        order.quantity = cmd.quantity if cmd.quantity else order.quantity
        order.number = cmd.number if cmd.number else order.number
        uow.commit()

def delete_order(uow, cmd):
    with uow:
        query_orders = text("DELETE FROM orders WHERE id = :order_id")
        uow.session.execute(query_orders, dict(order_id = cmd.id))
        uow.session.commit()


def add_payer(
        cmd: commands.AddPayer,
        uow,
) -> None:
    with uow:
        
        uow.payers.add(model.Payer(
            id=cmd.id,
            name=cmd.name.upper(),
            nif=cmd.nif,
            address=cmd.address,
            zip_code=cmd.zip_code,
            city=cmd.city,
            province=cmd.province
        ))
        uow.commit()

def update_payer(uow, cmd):
    with uow:
        payer = uow.payers.get_by_id(cmd.id)
        if not payer:
            return{}
        payer.name = cmd.name.upper() if cmd.name else payer.name  
        payer.nif = cmd.nif if cmd.nif else payer.nif
        payer.address = cmd.address if cmd.address else payer.address
        payer.zip_code = cmd.zip_code if cmd.zip_code else payer.zip_code
        payer.city = cmd.city if cmd.city else payer.city
        payer.province = cmd.province if cmd.province else payer.province
        uow.commit()
        return payer.to_dict()

def delete_payer(uow, cmd):
    with uow:
        payer = uow.payers.get_by_id(cmd.id)
        if not payer:
            return None
        query_payers = text("DELETE FROM payers WHERE id = :payer_id")
        uow.session.execute(query_payers, dict(payer_id = cmd.id))
        uow.session.commit()
        return 'Payer deleted succesfully'

def get_payers(uow, name):
    with uow:
        if name:
            query = text("SELECT * FROM payers WHERE name LIKE :name")
            rows = uow.session.execute(query, dict(name=f"%{name.upper()}%")).all()
        else:    
          query = text("SELECT * FROM payers")
          rows = uow.session.execute(query).all()
        if rows:
            payers = [row._asdict() for row in rows]
            return payers

        return []
    
def get_payer(uow, id):
    with uow:
        query = text("SELECT * FROM payers WHERE id = :id") 
        rows = uow.session.execute(query, {'id': id}).all()
        if rows:
            [payer] = [row._asdict() for row in rows]
            return payer      
        
        return None         

def get_payer_from_name(name, payers):
    """
    Retrieves a payer object from a list of payers based on a given name.
    The function will return the first payer whose name contains the
    name parameter

    Args:
        name (str): The name to search for.
        payers (list): A list of payer objects.

    Returns:
        Payer or None: The payer object if found, otherwise None.

    Example:
        >>> payers = [model.Payer(name='Google'), model.Payer(name='Apple Inc.')]
        >>> get_payer_from_name('googl', payers)
        Payer(name='Google')
    """
    for payer in payers:
        if name.lower() in payer.name.lower():
            return payer
    return None


def associate_payer_to_order(order, payers):
    payer = get_payer_from_name(order.payer_name, payers)
    order.allocate_payer(payer)


def get_invoice_code_generator(fixed_part, starting_number=0):
    number = starting_number
    while True:
        number += 1
        yield f"{fixed_part}-{number:04d}"


def associate_number_to_invoice(order, number_generator):
    if order.number is not None:
        raise ValueError(
            "Order number is already associated with an invoice."
        )
    order.number = next(number_generator)


def upload_payment_orders_from_file(cmd, uow):
    file_contents = cmd.file.read()

    with uow:
        inv_code_generator = get_invoice_code_generator(cmd.code_fixed_part, cmd.code_starting_number)
        xml_handler = file_handler.ExcelFileHandler(file_contents)
        order_list = xml_handler.get_orders_from_file()
        for order in order_list:
            associate_payer_to_order(order, uow.payers.list_all())
            associate_number_to_invoice(order, inv_code_generator)
            uow.orders.add(order)
        uow.commit()







def get_order_context(uow, order_number):
    with uow:
        order = uow.orders.get(order_number)
        order_context = invoice.generate_context(order)
        return order_context


def send_repeated_payer_notification(
        event: events.RepeatedPayer,
        uow: unit_of_work.AbstractUnitOfWork
):
    pass
