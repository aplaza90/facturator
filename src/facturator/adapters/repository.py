from abc import ABC, abstractmethod
from facturator.domain import model
from facturator.adapters.repository_entity_implementation import EntityImplementation


class AbstractRepository(ABC):
    entity_implementation: EntityImplementation

    @abstractmethod
    def add(self, entity):
        raise NotImplementedError

    @abstractmethod
    def get(self, prop: str):
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, id: str):
        raise NotImplementedError
    
    @abstractmethod
    def delete_by_id(self, id: str):
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session, entity_implementation: EntityImplementation):
        self.session = session
        self.entity_implementation = entity_implementation

    def add(self, entity):
        self.session.add(entity)

    def get(self, value):
        filter_by = {self.entity_implementation.get_filter_parameter(): value}
        return self.session.query(
            self.entity_implementation.get_entity_class()
        ).filter_by(**filter_by).one()

    def get_by_id(self, id: str):
        return self.session.query(
            self.entity_implementation.get_entity_class()
        ).get(id)

    def list_all(self):
        return self.session.query(
            self.entity_implementation.get_entity_class()
        ).all()

    def delete_by_id(self, id: str):
        entity_class = self.entity_implementation.get_entity_class()
        entity = self.session.query(entity_class).get(id)
        if entity:
            self.session.delete(entity)
        else:
            raise ValueError(f"Entity with id {id} does not exist")

