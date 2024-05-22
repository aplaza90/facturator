from facturator.domain import model
from sqlalchemy import text
from datetime import date


def test_retrieve_payer(in_memory_session):
    query_payers = text(
        "INSERT INTO payers (name) VALUES "
        '("payer1"),'
        '("payer2"),'
        '("payer3")'
    )
    in_memory_session.execute(query_payers)

    expected_payers = [
        model.Payer("payer1"),
        model.Payer("payer2"),
        model.Payer("payer3"),
    ]

    assert in_memory_session.query(model.Payer).all() == expected_payers


def test_retrieve_payer_address(in_memory_session):
    query_address = text(
        "INSERT INTO addresses (address, zip_code, city, province) VALUES "
        '("address 1", "28280", "pueblo", "Madrid")'
    )
    in_memory_session.execute(query_address)
    query_payers = text(
        "INSERT INTO payers (name, address_id) VALUES "
        '("payer3", "1")'
    )
    in_memory_session.execute(query_payers)

    expected_address = model.CompleteAddress(
        address="address 1",
        zip_code="28280",
        city="pueblo",
        province="Madrid"
    )
    assert in_memory_session.query(model.Payer).first().address == expected_address


def test_saving_payers(in_memory_session):
    new_payer = model.Payer("payer1")
    in_memory_session.add(new_payer)
    in_memory_session.commit()

    query = text('SELECT name FROM "payers"')
    rows = list(in_memory_session.execute(query))
    assert rows == [("payer1",)]


def test_saving_address_allocations(in_memory_session):
    address = model.CompleteAddress(
        address="address 1",
        zip_code="28280",
        city="pueblo",
        province="Madrid"
    )
    payer = model.Payer(
        name='payer1',
        address=address
    )
    in_memory_session.add(payer)
    in_memory_session.commit()

    query_address_id = text(
        "SELECT address_id "
        "FROM payers "
        "WHERE name = 'payer1'"
    )
    result = in_memory_session.execute(query_address_id).fetchone()
    if result:
        address_id = result[0]
        query_get_payer = text(
            "SELECT * "
            "FROM addresses "
            "WHERE id = :address_id"
        )
        allocated_address = in_memory_session.execute(query_get_payer, {'address_id': address_id}).fetchone()

        assert allocated_address.city == address.city
    else:
        assert False, "No order found with the specified name"


def test_retrieving_orders(in_memory_session):
    query = text(
        "INSERT INTO orders (payer_name, date, quantity, number) VALUES "
        '("order1", "2024-04-30", 150, "A123"),'
        '("order2", "2024-05-01", 200, "B456")'
    )

    in_memory_session.execute(query)
    expected = [
        model.InvoiceOrder(
            "order1",
            date=date(2024, 4, 30),
            quantity=150,
            number="A123"
        ),
        model.InvoiceOrder(
            "order2",
            date=date(2024, 5, 1),
            quantity=200,
            number="B456"
        )
    ]
    assert in_memory_session.query(model.InvoiceOrder).all() == expected


def test_saving_orders(in_memory_session):
    new_order = model.InvoiceOrder(
        "order1",
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
        date=date(2024, 5, 1),
        quantity=200,
        number="B456"
    )
    payer = model.Payer("payer1")
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


