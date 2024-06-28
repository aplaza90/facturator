from abc import ABC, abstractmethod
from facturator.adapters.repository_entity_implementation import EntityImplementation


class AbstractRepository(ABC):
    entity_implementation: EntityImplementation

    @abstractmethod
    def add(self, element: object):
        raise NotImplementedError

    @abstractmethod
    def get(self, value: str):
        raise NotImplementedError
    
    @abstractmethod
    def list_all(self):
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, element_id: str):
        raise NotImplementedError
    
    @abstractmethod
    def delete_by_id(self, element_id: str):
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session, entity_implementation: EntityImplementation):
        self.session = session
        self.entity_implementation = entity_implementation

    def add(self, element):
        self.session.add(element)

    def get(self, value):
        filter_by = {self.entity_implementation.get_filter_parameter(): value}
        return self.session.query(
            self.entity_implementation.get_entity_class()
        ).filter_by(**filter_by).one()

    def get_by_id(self, element_id: str):
        return self.session.get(
            self.entity_implementation.get_entity_class(), element_id
        )

    def list_all(self):
        return self.session.query(
            self.entity_implementation.get_entity_class()
        ).all()

    def delete_by_id(self, element_id: str):
        entity_class = self.entity_implementation.get_entity_class()
        entity = self.session.query(entity_class).get(element_id)
        if entity:
            self.session.delete(entity)
        else:
            raise ValueError(f"Entity with id {element_id} does not exist")

