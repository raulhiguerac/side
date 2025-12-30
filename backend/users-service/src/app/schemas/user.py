import uuid
from pydantic import BaseModel,EmailStr

class User(BaseModel):
    name: str
    last_name: str
    email: EmailStr

class UserGeneric(User):
    password: str
    phone: str | None = None

class UserOut(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    class Config:
        from_attributes = True