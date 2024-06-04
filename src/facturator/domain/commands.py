from dataclasses import dataclass
from datetime import datetime
from werkzeug.datastructures import FileStorage


class Command:
    pass


@dataclass
class AddPayer(Command):
    name: str
    nif: str
    address: str
    zip_code: str
    city: str
    province: str

@dataclass
class UpdatePayer(Command):
    id: int
    name: str = None
    nif: str = None
    address: str = None
    zip_code: str = None
    city: str = None
    province: str = None   

@dataclass
class DeletePayer(Command):
    id: int     

@dataclass
class AddOrder(Command):
    payer_name: str
    date: str
    quantity: float
    number: str = None

@dataclass
class UpdateOrder(Command):
    id: int
    payer_name: str = None
    date: str = None
    quantity: float = None
    number: str = None  

@dataclass
class DeleteOrder(Command):
    id: int

@dataclass
class UploadOrders(Command):
    file: FileStorage
    code_fixed_part: str
    code_starting_number: int

