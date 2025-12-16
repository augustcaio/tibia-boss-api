"""Schemas genéricos para respostas da API."""

from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Resposta paginada genérica."""

    items: List[T]
    total: int
    page: int
    size: int
    pages: int

