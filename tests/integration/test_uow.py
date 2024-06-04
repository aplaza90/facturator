from datetime import datetime
from sqlalchemy import text
import pytest

import random
import string

from facturator.domain import model
from facturator.service_layer import unit_of_work, handlers
from facturator.adapters import orm


def generate_random_payer_data(name):
    # Generate random data for the fields
    address = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) + " " + " ".join(
        random.choices(string.ascii_letters.capitalize(), k=5))
    zip_code = ''.join(random.choices(string.digits, k=5))
    city = ''.join(random.choices(string.ascii_letters.capitalize(), k=random.randint(5, 10)))
    province = ''.join(random.choices(string.ascii_letters.capitalize(), k=random.randint(5, 10)))
    nif = ''.join(random.choices(string.digits, k=9))

    # Create and return the dictionary
    data = {
        "name": name,
        "nif": nif,
        "address": address,
        "zip_code": zip_code,
        "city": city,
        "province": province
    }
    return data


def insert_payer(session, name, nif, address, zip_code, city, province):
    result = session.execute(
        orm.payers.insert().values(
            name=name,
            nif=nif,
            address=address,
            zip_code=zip_code,
            city=city,
            province=province
        )
    )
    inserted_id = result.inserted_primary_key[0]
    return inserted_id


def insert_payer_complete(
        name,  address, zip_code, city, province, nif, session
):
    payer_id = insert_payer(session, name, nif, address, zip_code, city, province)
    return payer_id


def get_allocated_payer_id(session, name):
    query = text(
        "SELECT p.name FROM orders JOIN payers AS p ON payer_id = p.id"
        " WHERE payer_name = 'pep'"
    )
    [[payer_id]] = session.execute(query, dict(payer_name=name))
    return payer_id


def test_uow_can_allocate_payer_into_order(session_factory):
    session = session_factory()
    insert_payer_complete(
        **generate_random_payer_data('Pepe'),
        session=session
    )
    session.commit()
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        payers = uow.payers.list_all()
        order = model.InvoiceOrder(
            payer_name='pep',
            date=datetime(2022, 1, 1).date(),
            quantity=100,
        )
        order_code_gen = handlers.get_invoice_code_generator(
            fixed_part='INV',
            starting_number=0
        )
        handlers.associate_payer_to_order(order, payers)
        handlers.associate_number_to_invoice(order, order_code_gen)
        uow.orders.add(order)
        uow.commit()
    assert get_allocated_payer_id(session, 'pep') == 'Pepe'


def test_rolls_uncommited_back_by_default(session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        insert_payer_complete(
            **generate_random_payer_data('Random'),
            session=uow.session
        )
    new_session = session_factory()
    rows = new_session.execute(text("SELECT * FROM 'payers'")).all()
    assert rows == []


def test_rolls_back_on_error(session_factory):
    class MyException(Exception):
        pass
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_payer_complete(
                **generate_random_payer_data('Random'),
                session=uow.session
            )
            raise MyException()
    new_session = session_factory()
    rows = new_session.execute(text("SELECT * FROM 'payers'")).all()
    assert rows == []
