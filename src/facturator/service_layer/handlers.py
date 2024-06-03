from sqlalchemy import text
from typing import TYPE_CHECKING

from facturator.domain import model, commands, events
from facturator.service_layer import file_handler, unit_of_work
from facturator.service_layer.invoice_generator import invoice

if TYPE_CHECKING:
    from facturator.service_layer import unit_of_work


def add_order(
        uow,
        cmd: commands.AddOrder = None,
) -> None:
    with uow:

        if not all([cmd.payer_name, cmd.date, cmd.quantity, cmd.number]):
            raise ValueError("All attributes must be provided")
        payer = get_payer_from_name(cmd.payer_name, uow.payers.list_all())

        order = model.InvoiceOrder(
            payer_name=cmd.payer_name,
            date=cmd.date,
            quantity=cmd.quantity,
            number=cmd.number
        )
        order.allocate_payer(payer)
        uow.orders.add(order)
        uow.commit()


def add_payer(
        cmd: commands.AddPayer,
        uow,
) -> None:
    with uow:
        complete_address = model.CompleteAddress(
            cmd.address,
            cmd.zip_code,
            cmd.city,
            cmd.province
        )
        uow.payers.add(model.Payer(
            name=cmd.name,
            address=complete_address,
            nif=cmd.nif
        ))
        uow.commit()


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


def get_payers(uow):
    with uow:
        query = text("SELECT * FROM payers")
        rows = uow.session.execute(query).all()
        if rows:
            payers = [row._asdict() for row in rows]
            return payers

        return [{'no': 'data'}]
    
def get_payer(uow, name):
    with uow:
        query = text("SELECT * FROM payers WHERE name = :name") 
        rows = uow.session.execute(query, {'name': name}).all()
        if rows:
            payers = [row._asdict() for row in rows]
            return payers      
        
        return [{'no': 'data'}]

def get_orders(uow):
    with uow:
        query = text("SELECT * FROM orders")
        rows = uow.session.execute(query).all()
        if rows:
            orders = [row._asdict() for row in rows]
            return orders

        return [{'no': 'data'}]
    
def get_order(uow, number):
    with uow:
        query = text("SELECT * FROM orders WHERE number = :number") 
        rows = uow.session.execute(query, {'number': number}).all()
        if rows:
            orders = [row._asdict() for row in rows]
            return orders      
    
    return [{'no': 'data'}]


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
