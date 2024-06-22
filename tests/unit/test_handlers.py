import datetime
import uuid

import pytest

from facturator.adapters import repository
from facturator.adapters.repository_entity_implementation import OrderImplementation, PayerImplementation
from facturator.service_layer import handlers, unit_of_work
from facturator.domain.model import Payer, InvoiceOrder
from facturator.domain import commands


class FakeRepository(repository.AbstractRepository):
    def __init__(self, entity_implementation, entities):
        self.entity_implementation = entity_implementation
        self._entities = set(entities)

    def add(self, entity):
        self._entities.add(entity)

    def get(self, value):
        param = self.entity_implementation.get_filter_parameter()
        return next(b for b in self._entities if getattr(b, param) == value)
    
    def get_by_id(self, id):
        pass

    def list_all(self):
        return list(self._entities)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.payers = FakeRepository(PayerImplementation(), [])
        self.orders = FakeRepository(OrderImplementation(), [])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


sample_payers = [
    Payer(
        name="Luis Sarmiento",
        nif="123456789A",
        address="123 Main St", 
        zip_code="12345",
        city="Anytown",
        province="CA"
    ),
    Payer(
        name="Luis Serrano",
        nif="123456789A",
        address="123 Main St", 
        zip_code="12345",
        city="Anytown",
        province="CA"
    ),
    Payer(
        name="Luis Moreno",
        nif="123456789A",
        address="123 Main St", 
        zip_code="12345",
        city="Anytown",
        province="CA"
    ),
    Payer(
        name="Luis Moron",
        nif="123456789A",
        address="123 Main St", 
        zip_code="12345",
        city="Anytown",
        province="CA"
    )
]

def test_add_order():
    uow = FakeUnitOfWork()
    cmd = commands.AddOrder(
        payer_name="Luis Sarmiento",
        date="2024-04-30",
        quantity=150,
        number="A123"
    )
    handlers.add_order(cmd, uow)
    assert uow.orders.get("A123") is not None
    assert uow.committed


def test_add_payer():
    uow = FakeUnitOfWork()
    cmd = commands.AddPayer(
        id=str(uuid.uuid4()),
        name='payer1',
        nif='1111',
        address='test_addr',
        zip_code='test_zip',
        city='test_zip',
        province='test_prov'
    )

    handlers.add_payer(
        cmd=cmd,
        uow=uow,
    )
    assert uow.payers.get('payer1'.upper()) is not None
    assert uow.committed


@pytest.mark.parametrize("name, expected_payer", [
    ("Luis Sarmiento", sample_payers[0]),
    ("Luis More", sample_payers[2]),
    ("Not a name", None)
])
def test_get_payer_from_name(name, expected_payer):
    result = handlers.get_payer_from_name(name, sample_payers)
    assert result == expected_payer


def test_associate_payer():
    orders = [
        InvoiceOrder(
            "Luis Moro",
            date=datetime.date(2024, 4, 30),
            quantity=120,
        ),
        InvoiceOrder(
            "Luis Sarmiento",
            date=datetime.date(2024, 4, 30),
            quantity=240,
        )
    ]
    for order in orders:
        handlers.associate_payer_to_order(order, sample_payers)
    assert orders[0]._payer == sample_payers[3]
    assert orders[1]._payer == sample_payers[0]

