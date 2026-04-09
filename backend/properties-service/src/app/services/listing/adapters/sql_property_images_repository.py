import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models.property import BatchStatus, ImageStatus, PropertyImage, PropertyImageUploadBatch
from app.services.listing.ports.property_images_repository import PropertyImageRepository


class SqlPropertyImageRepository(PropertyImageRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, *, image: PropertyImage) -> None:
        self.session.add(image)

    def add_batch(self, *, batch: PropertyImageUploadBatch) -> None:
        self.session.add(batch)

    def get_active_ids(self, *, property_id: uuid.UUID) -> list[uuid.UUID]:
        stmt = (
            select(PropertyImage.id)
            .where(PropertyImage.property_id == property_id)
            .where(PropertyImage.status == ImageStatus.active)
        )
        return list(self.session.exec(stmt).all())

    def get_images(
        self,
        *,
        property_id: uuid.UUID,
        image_ids: list[uuid.UUID] | None = None,
    ) -> list[PropertyImage]:
        stmt = (
            select(PropertyImage)
            .where(PropertyImage.property_id == property_id)
            .where(PropertyImage.status == ImageStatus.active)
        )
        if image_ids is not None:
            stmt = stmt.where(PropertyImage.id.in_(image_ids))
        return list(self.session.exec(stmt).all())

    def get_batch(self, *, batch_id: uuid.UUID) -> Optional[PropertyImageUploadBatch]:
        return self.session.get(PropertyImageUploadBatch, batch_id)

    def get_open_batches(
        self,
        *,
        property_id: uuid.UUID,
        now: datetime,
        exclude_ids: list[uuid.UUID] | None = None,
    ) -> list[PropertyImageUploadBatch]:
        stmt = (
            select(PropertyImageUploadBatch)
            .where(PropertyImageUploadBatch.property_id == property_id)
            .where(PropertyImageUploadBatch.expires_at > now)
            .where(PropertyImageUploadBatch.status.in_([BatchStatus.pending, BatchStatus.ready]))
        )
        if exclude_ids:
            stmt = stmt.where(PropertyImageUploadBatch.id.notin_(exclude_ids))
        return list(self.session.exec(stmt).all())
