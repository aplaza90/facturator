from facturator.domain import model, commands
from facturator.service_layer import file_handler
from facturator.service_layer.invoice_generator import invoice


def add_order(
        cmd: commands.AddOrder,
        uow,
) -> None:
    with uow:

        if not all([cmd.payer_name, cmd.date, cmd.quantity]):
            raise ValueError("All attributes must be provided")
        payer = get_payer_from_name(cmd.payer_name, uow.payers.list_all())

        order = model.InvoiceOrder(
            id=cmd.id,
            payer_name=cmd.payer_name.upper(),
            date=cmd.date,
            quantity=cmd.quantity,
            number=cmd.number
        )
        order.allocate_payer(payer)
        uow.orders.add(order)
        uow.commit()
        return order.to_dict()


def get_orders(uow, payer_name, recursive=False):
    with uow:
        if payer_name:
            all_orders = uow.orders.list_all()
            filtered_orders = [
                order for order in all_orders 
                if payer_name.upper() in order.payer_name.upper()
            ]
            orders = [
                (
                    order.to_dict_recursive() if recursive else order.to_dict()
                ) for order in filtered_orders
            ]
        else:    
            orders = [
                (
                    order.to_dict_recursive() if recursive else order.to_dict()
                ) for order in uow.orders.list_all()
            ]

        return orders


def get_order(uow, id, recursive=False):
    with uow:
        order = uow.orders.get_by_id(id)
        if order:
            return (
                order.to_dict_recursive() if recursive
                else order.to_dict()
            )
        return None


def update_order(uow, cmd):
    with uow:
        order = uow.orders.get_by_id(cmd.id)
        if not order:
            return {}
        if cmd.payer_name:
            order.payer_name = cmd.payer_name.upper() 
            payer = get_payer_from_name(cmd.payer_name, uow.payers.list_all())
            order.allocate_payer(payer)
        order.date = cmd.date if cmd.date else order.date
        order.quantity = cmd.quantity if cmd.quantity else order.quantity
        order.number = cmd.number if cmd.number else order.number
        uow.commit()

        return order.to_dict()


def delete_order(uow, cmd):
    with uow:
        order = uow.orders.get_by_id(cmd.id)
        if not order:
            return None
        uow.orders.delete_by_id(element_id=cmd.id)
        uow.commit()
        return 'Order deleted succesfully'


def add_payer(
        cmd: commands.AddPayer,
        uow,
) -> None:
    with uow:
        payer = model.Payer(
            id=cmd.id,
            name=cmd.name.upper(),
            nif=cmd.nif,
            address=cmd.address,
            zip_code=cmd.zip_code,
            city=cmd.city,
            province=cmd.province
        )
        uow.payers.add(payer)
        uow.commit()
        return payer.to_dict()


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
        uow.payers.delete_by_id(element_id=cmd.id)
        uow.commit()
        return 'Payer deleted succesfully'


def get_payer(uow, id):
    with uow:
        payer = uow.payers.get_by_id(id)
        if payer:    
            return payer.to_dict()
        return None 


def get_payers(uow, name):
    with uow:
        if name:
            all_payers = uow.payers.list_all()
            filtered_payers = [
                payer for payer in all_payers 
                if name.upper() in payer.name.upper()
            ]
            payers = [payer.to_dict() for payer in filtered_payers]
        else:
            payers = [payer.to_dict() for payer in uow.payers.list_all()]

        return payers
  

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
        return [order.to_dict() for order in order_list]


def get_order_context(uow, order_number):
    with uow:
        order = uow.orders.get(order_number)
        order_context = invoice.generate_context(order)
        return order_context

