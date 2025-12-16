"""Rotas relacionadas a Bosses."""

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.db.repository import BossRepository
from app.schemas.boss import BossShortSchema
from app.schemas.response import PaginatedResponse

router = APIRouter(
    prefix="/bosses",
    tags=["bosses"],
)


@router.get(
    "",
    response_model=PaginatedResponse[BossShortSchema],
    summary="Listar bosses com paginação",
    description="Retorna uma lista paginada de bosses. Use os parâmetros `page` e `limit` para controlar a paginação.",
)
async def list_bosses(
    page: int = Query(default=1, ge=1, description="Número da página (começa em 1)"),
    limit: int = Query(default=20, ge=1, le=100, description="Número de itens por página (máximo 100)"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Lista bosses com paginação.

    Args:
        page: Número da página (padrão: 1)
        limit: Número de itens por página (padrão: 20, máximo: 100)
        db: Instância do banco de dados (injetada via Dependency Injection)

    Returns:
        Resposta paginada com lista de bosses e metadados
    """
    repository = BossRepository(db)

    # Calcula skip baseado na página
    skip = (page - 1) * limit

    # Busca bosses e total
    bosses = await repository.list_bosses(skip=skip, limit=limit)
    total = await repository.count()

    # Calcula número de páginas
    pages = (total + limit - 1) // limit if total > 0 else 0

    # Converte BossModel para BossShortSchema
    items = [
        BossShortSchema(
            name=boss.name,
            slug=boss.slug or boss.get_slug(),
            visuals=boss.visuals,
            hp=boss.hp,
        )
        for boss in bosses
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=len(items),
        pages=pages,
    )

