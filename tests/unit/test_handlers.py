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
    
    def get_by_id(self, element_id):
        try:
            return next(entity for entity in self._entities if getattr(entity, 'id') == element_id)
        except StopIteration:
            return None

    def list_all(self):
        return list(self._entities)
    
    def delete_by_id(self, id: str):
        entity = self.get_by_id(id)
        if entity:
            self._entities.remove(entity)
        else:
            raise ValueError(f"Entity with id {id} does not exist")


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
        id=str(uuid.uuid4()),
        payer_name="Luis Sarmiento",
        date="2024-04-30",
        quantity=150,
        number="A123"
    )
    handlers.add_order(cmd, uow)
    assert uow.orders.get("A123") is not None
    assert uow.committed


def test_add_then_update_order():
    uow = FakeUnitOfWork()
    order_id = str(uuid.uuid4())
    cmd = commands.AddOrder(
        id=order_id,
        payer_name="original_name",
        date="2024-04-30",
        quantity=150,
        number="TEST_NUMBER"
    )
    handlers.add_order(cmd, uow)
    
    original_order = uow.orders.get("TEST_NUMBER")
    assert original_order.payer_name == "original_name".upper()
    assert uow.committed
    
    update_cmd = commands.UpdateOrder(
        id=order_id,
        payer_name="modified_name",
        date="2024-04-30",
        quantity=150,
        number="TEST_NUMBER"
    )
    handlers.update_order(cmd=update_cmd, uow=uow)
    order = uow.orders.get("TEST_NUMBER")
    assert order.payer_name == "modified_name".upper()


def test_add_the_get_order():
    uow = FakeUnitOfWork()
    order_id = str(uuid.uuid4())
    cmd = commands.AddOrder(
        id=order_id,
        payer_name="payer_name",
        date="2024-04-30",
        quantity=150,
        number="TEST_GET_BY_ID"
    )
    handlers.add_order(cmd, uow)

    retrieved_order = handlers.get_order(uow=uow, id = order_id)
    assert retrieved_order.get('number') == "TEST_GET_BY_ID"


def test_add_order_and_then_delete_it():
    uow = FakeUnitOfWork()
    order_id = str(uuid.uuid4())
    cmd = commands.AddOrder(
        id=order_id,
        payer_name="original_name",
        date="2024-04-30",
        quantity=150,
        number="TEST_DELETE"
    )
    handlers.add_order(cmd, uow)
    
    original_order = uow.orders.get("TEST_DELETE")
    assert original_order.payer_name == "original_name".upper()
    assert uow.committed
    
    delete_cmd = commands.DeleteOrder(id=order_id)

    handlers.delete_order(cmd=delete_cmd, uow=uow)
    assert not uow.orders.get_by_id(order_id)
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

