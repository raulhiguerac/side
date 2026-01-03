import uuid
from pydantic import BaseModel,EmailStr

from app.models.user import AccountType

class User(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    account_type: AccountType.person

class UserGeneric(User):
    password: str
    phone: str | None = None

class Company(BaseModel):
    display_name: str
    email: EmailStr
    account_type: AccountType.organization

class CompanyGeneric(Company):
    password: str
    phone: str | None = None

class UserOut(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    class Config:
        from_attributes = True