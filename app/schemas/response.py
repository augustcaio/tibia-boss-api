"""Schemas genéricos para respostas da API."""

from typing import Generic, List, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Resposta paginada genérica."""

    items: List[T]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "name": "Morgaroth",
                        "slug": "morgaroth",
                        "hp": 100000,
                        "visuals": {
                            "gif_url": "https://tibia.fandom.com/images/Morgaroth.gif",
                            "filename": "Morgaroth.gif",
                        },
                    }
                ],
                "total": 500,
                "page": 1,
                "size": 20,
                "pages": 25,
            }
        }
    )

