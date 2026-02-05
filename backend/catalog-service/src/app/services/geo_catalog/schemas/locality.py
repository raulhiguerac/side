import uuid

from app.schemas.base import StrictBase

class LocalityListItem(StrictBase):
    id: uuid.UUID                                                                                          
    name: str                                                                                              
    admin_division_name: str