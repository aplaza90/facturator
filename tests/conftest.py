import time
from pathlib import Path

import pytest
import requests
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, clear_mappers

from facturator.adapters.orm import metadata, start_mappers
from facturator import config


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def session_factory(in_memory_db):
    start_mappers()
    yield sessionmaker(bind=in_memory_db)
    clear_mappers()


@pytest.fixture
def in_memory_session(session_factory):
    return session_factory()


def wait_for_postgres_to_come_up(engine):
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            return engine.connect()
        except OperationalError:
            time.sleep(0.5)
    pytest.fail("Postgres never came up")


def wait_for_webapp_to_come_up():
    deadline = time.time() + 10
    url = config.get_api_url()
    while time.time() < deadline:
        try:
            return requests.get(url)
        except ConnectionError:
            time.sleep(0.5)
    pytest.fail("API never came up")


@pytest.fixture(scope="session")
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    metadata.create_all(engine)
    return engine


@pytest.fixture
def postgres_session(postgres_db):
    start_mappers()
    yield sessionmaker(bind=postgres_db)()
    clear_mappers()


@pytest.fixture
def restart_api():
    (Path(__file__).parent / "flask_app.py").touch()
    time.sleep(0.5)
    wait_for_webapp_to_come_up()


def restart_table_in_db(engine, session, table_name, param=""):
    session.execute(text("DROP TABLE {} {}".format(table_name, param)))
    session.commit()
    metadata.create_all(engine)
    session.close()


@pytest.fixture
def setup_orders_postgres(postgres_db):
    session = sessionmaker(postgres_db)()
    restart_table_in_db(engine=postgres_db, session=session, table_name='orders')
    yield
    restart_table_in_db(engine=postgres_db, session=session, table_name='orders')


@pytest.fixture
def setup_payers_postgres(postgres_db):
    session = sessionmaker(bind=postgres_db)()
    restart_table_in_db(engine=postgres_db, session=session, table_name='payers', param="CASCADE")
    yield
    restart_table_in_db(engine=postgres_db, session=session, table_name='payers', param="CASCADE")


@pytest.fixture
def setup_users_postgres(postgres_db):
    session = sessionmaker(bind=postgres_db)()
    session.execute(text("DELETE FROM users"))
    session.commit()
    yield
    session.execute(text("DELETE FROM users"))    
    session.commit()
