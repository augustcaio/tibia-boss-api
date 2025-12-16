"""Rotas relacionadas a Bosses."""

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.db.repository import BossRepository
from app.models.boss import BossModel
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


@router.get(
    "/{slug}",
    response_model=BossModel,
    summary="Obter detalhes de um boss",
    description="Retorna os detalhes completos de um boss pelo slug.",
    responses={404: {"description": "Boss not found"}},
)
async def get_boss_by_slug(
    slug: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Retorna os detalhes completos de um boss pelo slug.

    Args:
        slug: Slug do boss (ex: "morgaroth")
        db: Instância do banco de dados (injetada via Dependency Injection)

    Returns:
        Detalhes completos do boss

    Raises:
        HTTPException: 404 se o boss não for encontrado
    """
    repository = BossRepository(db)
    boss = await repository.find_by_slug(slug)

    if boss is None:
        raise HTTPException(status_code=404, detail="Boss not found")

    return boss


@router.get(
    "/search",
    response_model=PaginatedResponse[BossShortSchema],
    summary="Buscar bosses por nome",
    description="Busca bosses por nome usando regex case insensitive. A query é sanitizada para evitar ReDoS.",
    responses={400: {"description": "Invalid query parameter"}},
)
async def search_bosses(
    q: str = Query(..., min_length=1, description="Termo de busca"),
    page: int = Query(default=1, ge=1, description="Número da página (começa em 1)"),
    limit: int = Query(
        default=20, ge=1, le=100, description="Número de itens por página (máximo 100)"
    ),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Busca bosses por nome usando regex.

    Args:
        q: Termo de busca (mínimo 1 caractere)
        page: Número da página (padrão: 1)
        limit: Número de itens por página (padrão: 20, máximo: 100)
        db: Instância do banco de dados (injetada via Dependency Injection)

    Returns:
        Resposta paginada com lista de bosses que correspondem à busca

    Raises:
        HTTPException: 400 se a query estiver vazia
    """
    # Valida query vazia
    if not q or not q.strip():
        raise HTTPException(
            status_code=400, detail="Query parameter 'q' cannot be empty"
        )

    # Sanitiza a query para evitar ReDoS (Regular Expression Denial of Service)
    sanitized_query = re.escape(q.strip())

    repository = BossRepository(db)

    # Calcula skip baseado na página
    skip = (page - 1) * limit

    # Busca bosses e total
    bosses = await repository.search_by_name(query=sanitized_query, skip=skip, limit=limit)
    total = await repository.count_by_search(query=sanitized_query)

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

