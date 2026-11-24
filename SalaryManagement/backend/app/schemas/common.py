"""Shared API response schemas."""

from typing import Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Standard response envelope for paginated endpoints."""

    items: list[DataT]
    total: int
    page: int
    page_size: int
