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
class AddOrder(Command):
    payer_name: str
    date: datetime.date
    quantity: float
    number: str


@dataclass
class UploadOrders(Command):
    file: FileStorage
    code_fixed_part: str
    code_starting_number: int

