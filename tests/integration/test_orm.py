from facturator.domain import model
from sqlalchemy import text
from datetime import date
import uuid


def test_retrieve_payer(in_memory_session):
    uuid1 = str(uuid.uuid4())
    uuid2 = str(uuid.uuid4())
    uuid3 = str(uuid.uuid4())

    query_payers = text(
        f"INSERT INTO payers (id, name) VALUES "
        f"('{uuid1}' ,'payer1'),"
        f"('{uuid2}' ,'payer2'),"
        f"('{uuid3}' ,'payer3')"
    )
    in_memory_session.execute(query_payers)
  
    expected_payers = [
        model.Payer(id=uuid1, name="payer1"),
        model.Payer(id=uuid2, name="payer2"),
        model.Payer(id=uuid3, name="payer3"),
    ]

    assert in_memory_session.query(model.Payer).all() == expected_payers


def test_saving_payers(in_memory_session):
    new_payer = model.Payer(
        id=str(uuid.uuid4()),
        name="payer1"
    )
    in_memory_session.add(new_payer)
    in_memory_session.commit()

    query = text('SELECT name FROM "payers"')
    rows = list(in_memory_session.execute(query))
    assert rows == [("payer1",)]



def test_retrieving_orders(in_memory_session):
    uuid1 = str(uuid.uuid4())
    uuid2 = str(uuid.uuid4())
    query = text(
        f"INSERT INTO orders (id, payer_name, date, quantity, number) VALUES "
        f"('{uuid1}', 'order1', '2024-04-30', 150, 'A123'),"
        f"('{uuid2}', 'order2', '2024-05-01', 200, 'B456')"
    )

    in_memory_session.execute(query)
    expected = [
        model.InvoiceOrder(
            "order1",
            id=uuid1,
            date='2024-04-30',
            quantity=150,
            number="A123"
        ),
        model.InvoiceOrder(
            "order2",
            id=uuid2,
            date='2024-05-01',
            quantity=200,
            number="B456"
        )
    ]
    assert in_memory_session.query(model.InvoiceOrder).all() == expected


def test_saving_orders(in_memory_session):
    new_order = model.InvoiceOrder(
        "order1",
        id=str(uuid.uuid4()),
        date=date(2024, 5, 1),
        quantity=200,
        number="B456"
    )
    in_memory_session.add(new_order)
    in_memory_session.commit()

    query = text('SELECT payer_name FROM "orders"')
    rows = list(in_memory_session.execute(query))
    assert rows == [("order1",)]


def test_saving_allocations(in_memory_session):
    order = model.InvoiceOrder(
        "order1",
        id=str(uuid.uuid4()),
        date=date(2024, 5, 1),
        quantity=200,
        number="B456"
    )
    payer = model.Payer(id=str(uuid.uuid4()), name="payer1")
    order.allocate_payer(payer)
    in_memory_session.add(order)
    in_memory_session.commit()

    query_payer_id = text(
        "SELECT payer_id "
        "FROM orders "
        "WHERE payer_name = :order_name"
    )
    result = in_memory_session.execute(query_payer_id, {'order_name': 'order1'}).fetchone()
    if result:
        payer_id = result[0]
        query_get_payer = text(
            "SELECT * "
            "FROM payers "
            "WHERE id = :payer_id"
        )
        allocated_payer = in_memory_session.execute(query_get_payer, {'payer_id': payer_id}).fetchone()

        assert allocated_payer.name == payer.name
    else:
        assert False, "No order found with the specified name"


