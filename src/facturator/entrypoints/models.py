from pydantic import BaseModel, ValidationError
from typing import Optional


class PostPayer(BaseModel):
    name: str
    nif: str
    address: str
    zip_code: str
    city: str
    province: str

class PatchPayer(BaseModel):
    name: Optional[str] = None
    nif: Optional[str] = None
    address: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None

class PostOrder(BaseModel):
    number: str
    payer_name: str
    date: str
    quantity: float

class PatchOrder(BaseModel):
    number: Optional[str] = None
    payer_name: Optional[str] = None
    date: Optional[str] = None
    quantity: Optional[float] = None
