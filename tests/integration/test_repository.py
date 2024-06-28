# pylint: disable=protected-access
from datetime import date
import uuid
from sqlalchemy import text

from facturator.domain import model
from facturator.adapters import repository
from facturator.adapters.repository_entity_implementation import (
    OrderImplementation,
    PayerImplementation
)

def test_save_order_with_repo_retrieve_with_query(in_memory_session):
    
    order = model.InvoiceOrder(
        payer_name="TEST_PAYER",
        id=str(uuid.uuid4()),
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

    assert list(rows) == [('TEST_PAYER',)]


def test_save_order_with_query_retrieve_with_repo(in_memory_session):
    
    order_id = str(uuid.uuid4())
    payer_name = "TEST_PAYER"
    order_date = "2022-01-01"
    quantity = 200

    query = text(
        f"INSERT INTO orders (id, payer_name, date, quantity) "
        f"VALUES ('{order_id}', '{payer_name}', '{order_date}', {quantity})"
    )

    in_memory_session.execute(query)

    order_repo = repository.SqlAlchemyRepository(
        in_memory_session,
        OrderImplementation()
    )
    order_retrieved = order_repo.get_by_id(order_id)

    assert order_retrieved.payer_name == payer_name


def test_add_and_list_payer(in_memory_session):

    sample_payers = [
        model.Payer(
            id=str(uuid.uuid4()),
            name='TEST_LIST_1',
            nif='1111',
            address='test_addr',
            zip_code='test_zip',
            city='test_city',
            province='test_prov'
        ),
        model.Payer(
            id=str(uuid.uuid4()),
            name='TEST_LIST_2',
            nif='1111',
            address='test_addr',
            zip_code='test_zip',
            city='test_city',
            province='test_prov'
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

    assert payer_names[0] == ('TEST_LIST_1',)
    assert payer_names[1] == ('TEST_LIST_2',)
    assert payer_repo.list_all() == sample_payers


def test_save_payer_with_query_retrieve_with_repo(in_memory_session):
    
    payer_id = str(uuid.uuid4())
    name = "TEST_PAYER"
    nif = "12345678A"
    address = "Some Address"
    zip_code = "12345"
    city = "Some city"
    province = "Some province"


    query = text(
        f"INSERT INTO payers (id, name, nif, address, zip_code, city, province) "
        f"VALUES ('{payer_id}', '{name}', '{nif}', '{address}', '{zip_code}', '{city}', '{province}')"
    )

    in_memory_session.execute(query)

    payer_repo = repository.SqlAlchemyRepository(
        in_memory_session,
        PayerImplementation()
    )
    payer_retrieved = payer_repo.get_by_id(payer_id)

    assert payer_retrieved.name == name