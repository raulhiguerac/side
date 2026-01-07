import uuid 
from typing import Annotated, Union, Literal, Optional 
from pydantic import EmailStr, Field 
from app.schemas.base import StrictBase 
    
class CurrentUserPerson(StrictBase): 
    first_name: str 
    last_name: str 
    phone: Optional[str] 
    photo_url: Optional[str] 
    description: Optional[str]
    account_type: Literal['person']
    
class CurrentUserOrganization(StrictBase):
    display_name: str 
    phone: Optional[str] 
    photo_url: Optional[str] 
    description: Optional[str] 
    account_type: Literal["organization"]

class CurrentUserProfileOut(StrictBase): 
    account_id: uuid.UUID 
    email: EmailStr 
    account_type: Literal["person", "organization"]
    onboarding_step: int 
    profile: Annotated[
        Union[CurrentUserPerson,CurrentUserOrganization],
        Field(discriminator="account_type")
    ]

class CurrentUserOut(StrictBase):
    account_id: uuid.UUID
    email: EmailStr
    account_type: Literal["person", "organization"]
    onboarding_step: int