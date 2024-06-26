from dataclasses import dataclass
from werkzeug.datastructures import FileStorage


class Command:
    pass


@dataclass
class AddPayer(Command):
    id: str
    name: str
    nif: str
    address: str
    zip_code: str
    city: str
    province: str

@dataclass
class UpdatePayer(Command):
    id: str
    name: str = None
    nif: str = None
    address: str = None
    zip_code: str = None
    city: str = None
    province: str = None   

@dataclass
class DeletePayer(Command):
    id: str

@dataclass
class AddOrder(Command):
    id: str
    payer_name: str
    date: str
    quantity: float
    number: str = None

@dataclass
class UpdateOrder(Command):
    id: str
    payer_name: str = None
    date: str = None
    quantity: float = None
    number: str = None  

@dataclass
class DeleteOrder(Command):
    id: str

@dataclass
class UploadOrders(Command):
    file: FileStorage
    code_fixed_part: str
    code_starting_number: int

