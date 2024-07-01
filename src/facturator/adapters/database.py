from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from facturator import config
from facturator.adapters import orm


def init_db():
    orm.start_mappers()
    engine = create_engine(config.get_postgres_uri())
    orm.metadata.create_all(engine)
    return sessionmaker(bind=engine)


get_session = init_db()
