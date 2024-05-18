from abc import ABC, abstractmethod
from facturator.domain import model


class EntityImplementation(ABC):
    @abstractmethod
    def get_entity_class(self) -> type:
        pass

    @abstractmethod
    def get_filter_parameter(self) -> str:
        pass


class OrderImplementation(EntityImplementation):
    def get_entity_class(self) -> type:
        return model.InvoiceOrder

    def get_filter_parameter(self) -> str:
        return "payer_name"


class PayerImplementation(EntityImplementation):
    def get_entity_class(self) -> type:
        return model.Payer

    def get_filter_parameter(self) -> str:
        return "name"
