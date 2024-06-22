from sqlalchemy import Table, MetaData, Column, Integer, String, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship, registry
import uuid

from facturator.domain import model

metadata = MetaData()

users = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('public_id', String(128)),
    Column('username', String(255)),
    Column('nif', String(20)),
    Column('address', String(255)),
    Column('zip_code', String(100)),
    Column('city', String(100)),
    Column('province', String(100)),
    Column('email', String(255)),
    Column('password', String(255))
)

orders = Table(
    'orders',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('payer_name', String(255)),
    Column('payer_id', String(255), ForeignKey('payers.id')),
    Column('date', Date),
    Column('quantity', Numeric(10, 2)),
    Column('number', String(50))
)

payers = Table(
    'payers',
    metadata,
    Column('id', String(255), primary_key=True),
    Column('name', String(255)),
    Column('nif', String(20)),
    Column('address', String(255)),
    Column('zip_code', String(10)),
    Column('city', String(100)),
    Column('province', String(100)),
)


def start_mappers():
    mapper_registry = registry()

    mapper_registry.map_imperatively(model.User, users)

    mapper_registry.map_imperatively(model.Payer, payers)

    mapper_registry.map_imperatively(
        model.InvoiceOrder, orders, properties={
            '_payer': relationship(model.Payer)
        }
    )
