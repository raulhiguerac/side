import uuid

from sqlmodel import Session, func, select

from app.models.promotion import PromotedListing, active_promotion_clause
from app.services.admin.ports.promotion_repository import PromotionRepository


class SqlPromotionRepository(PromotionRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, *, promotion: PromotedListing) -> None:
        self.session.add(promotion)
        self.session.flush()

    def flush(self) -> None:
        self.session.flush()

    def get_active_by_property_id(self, *, property_id: uuid.UUID) -> PromotedListing | None:
        stmt = (
            select(PromotedListing)
            .where(PromotedListing.property_id == property_id)
            .where(active_promotion_clause())
        )
        return self.session.exec(stmt).first()

    def get_all(self, *, offset: int = 0, limit: int = 20) -> list[PromotedListing]:
        """Orden por prioridad y luego por vencimiento: es el orden en el que se
        revisan. El `id` desempata para que el offset no repita ni saltee filas
        entre páginas cuando dos promociones comparten prioridad y fecha."""
        stmt = (
            select(PromotedListing)
            .where(active_promotion_clause())
            .order_by(
                PromotedListing.priority.desc(),
                PromotedListing.ends_at.asc(),
                PromotedListing.id,
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(stmt).all())

    def count_all(self) -> int:
        stmt = (
            select(func.count())
            .select_from(PromotedListing)
            .where(active_promotion_clause())
        )
        return self.session.exec(stmt).one()

    def delete(self, *, promotion: PromotedListing) -> None:
        self.session.delete(promotion)
        self.session.flush()
