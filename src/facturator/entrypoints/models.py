from pydantic import BaseModel, ValidationError, ConfigDict, UUID4
from typing import Optional, List


class SignUp(BaseModel):
    username: str
    nif: str
    address: str
    zip_code: str
    city: str
    province: str
    email: str
    password: str


class LogIn(BaseModel):
    username: str
    password: str


class PostPayer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    nif: str
    address: str
    zip_code: str
    city: str
    province: str


class PayerItemResponse(PostPayer):
    id: UUID4


class PayerListResponse(BaseModel):
    payers: List[PayerItemResponse] = []    


class PatchPayer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Optional[str] = None
    nif: Optional[str] = None
    address: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None


class PostOrder(BaseModel):
    model_config = ConfigDict(extra='forbid')
    number: str
    payer_name: str
    date: str
    quantity: float


class PatchOrder(BaseModel):
    model_config = ConfigDict(extra='forbid')
    number: Optional[str] = None
    payer_name: Optional[str] = None
    date: Optional[str] = None
    quantity: Optional[float] = None

