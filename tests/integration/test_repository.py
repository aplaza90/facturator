# pylint: disable=protected-access
from sqlalchemy import text
from datetime import date
import uuid

from facturator.domain import model
from facturator.adapters import repository
from facturator.adapters.repository_entity_implementation import OrderImplementation, PayerImplementation


def test_save_order(in_memory_session):
    order =model.InvoiceOrder(
        "order1",
        date=date(2024, 5, 1),
        quantity=200,
        number="B456"
    )
    order_repo = repository.SqlAlchemyRepository(
        in_memory_session,
        OrderImplementation()
    )
    order_repo.add(order)
    in_memory_session.commit()
    query = text('SELECT payer_name FROM "orders"')

    rows = in_memory_session.execute(query)
    assert list(rows) == [('order1',)]


def insert_order(session, name):
    query_in = text(
        "INSERT INTO orders (name)"
        " VALUES (:order_name)"
    )
    session.execute(query_in, {"order_name": name})

    query_out = text("SELECT id FROM orders WHERE name=:order_name")
    [[order_id]] = session.execute(
        query_out,
        dict(order_name=name,),
    )
    return order_id


def insert_payer(session):
    query_in = text(
        "INSERT INTO payers (name)"
        ' VALUES ("payer1")',
    )
    session.execute(query_in)

    query_out = text('SELECT id FROM payers WHERE name=:name')
    [[payer_id]] = session.execute(query_out, dict(name="payer1"))
    return payer_id


def test_add_and_list_payer(in_memory_session):

    sample_payers = [
        model.Payer(
        id=str(uuid.uuid4()),  
        name="Luis Sarmiento",
        nif="123456789A",
        address="123 Main St", 
        zip_code="12345",
        city="Anytown",
        province="CA"
        ),
        model.Payer(
        id=str(uuid.uuid4()),  
        name="Luis Serrano",
        nif="123456789A",
        address="123 Main St", 
        zip_code="12345",
        city="Anytown",
        province="CA"
        )
    ]
    payer_repo = repository.SqlAlchemyRepository(
        in_memory_session,
        PayerImplementation()
    )
    for payer in sample_payers:
        payer_repo.add(payer)
    in_memory_session.commit()
    query = text('SELECT name FROM payers')
    payer_names = in_memory_session.execute(query).fetchall()
    assert payer_names[0] == ('Luis Sarmiento',)
    assert payer_names[1] == ('Luis Serrano',)
    assert payer_repo.list_all() == sample_payers


