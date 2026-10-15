import math
from typing import Any, Generic, TypeVar

from pydantic import Field
from typing_extensions import Self

from app.schemas.base import StrictBase

T = TypeVar("T")


class PageRequest(StrictBase):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Page(StrictBase, Generic[T]):
    items: list[T]
    total_items: int
    total_pages: int
    current_page: int
    items_per_page: int

    @classmethod
    def build(cls, *, items: list[T], total_items: int, req: PageRequest, **extra: Any) -> Self:
        return cls(
            items=items,
            total_items=total_items,
            total_pages=math.ceil(total_items / req.page_size),
            current_page=req.page,
            items_per_page=req.page_size,
            **extra,
        )
