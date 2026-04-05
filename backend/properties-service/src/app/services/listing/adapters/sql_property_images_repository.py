from sqlmodel import Session

from app.models.property import PropertyImage
from app.services.listing.ports.property_images_repository import PropertyImageRepository


class SqlPropertyImageRepository(PropertyImageRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, *, image: PropertyImage) -> None:
        self.session.add(image)
