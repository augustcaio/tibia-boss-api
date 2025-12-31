"""Rotas relacionadas a Bosses."""

import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.rate_limit import limiter
from app.db.repository import BossRepository
from app.db.system_jobs import SystemJobsRepository
from app.models.boss import BossModel
from app.schemas.boss import BossShortSchema
from app.schemas.response import PaginatedResponse

router = APIRouter(
    prefix="/bosses",
    tags=["bosses"],
)


@limiter.limit("60/minute")
@router.get(
    "",
    response_model=PaginatedResponse[BossShortSchema],
    summary="Listar bosses com paginação",
    description="Retorna uma lista paginada de bosses. Use os parâmetros `page` e `limit` para controlar a paginação.",
    responses={
        200: {"description": "Lista de bosses retornada com sucesso"},
        422: {"description": "Parâmetros de validação inválidos"},
        500: {"description": "Erro interno do servidor"},
    },
)
async def list_bosses(
    request: Request,  # noqa: ARG001 - usado pelo slowapi para extrair o IP
    page: int = Query(default=1, ge=1, description="Número da página (começa em 1)"),
    limit: int = Query(
        default=20, ge=1, le=100, description="Número de itens por página (máximo 100)"
    ),
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

    # Busca última atualização
    jobs_repo = SystemJobsRepository(db)
    status = await jobs_repo.get_scraper_status()
    latest_update = status.last_run.isoformat() if status and status.last_run else None

    # Calcula número de páginas
    pages = (total + limit - 1) // limit if total > 0 else 0

    # Converte BossModel para BossShortSchema
    items = [
        BossShortSchema(
            name=boss.name,
            slug=boss.slug or boss.get_slug(),
            visuals=boss.visuals,
            hp=boss.hp,
            speed=boss.speed,
            location=boss.location,
            bosstiary=boss.bosstiary,
        )
        for boss in bosses
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=len(items),
        pages=pages,
        latest_update=latest_update,
    )


@limiter.limit("20/minute")
@router.get(
    "/search",
    response_model=PaginatedResponse[BossShortSchema],
    summary="Buscar bosses por nome",
    description="Busca bosses por nome usando regex case insensitive. A query é sanitizada para evitar ReDoS.",
    responses={
        200: {"description": "Busca realizada com sucesso"},
        400: {"description": "Parâmetro de query inválido ou vazio"},
        422: {"description": "Parâmetros de validação inválidos"},
        500: {"description": "Erro interno do servidor"},
    },
)
async def search_bosses(
    request: Request,  # noqa: ARG001 - usado pelo slowapi para extrair o IP
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
        raise HTTPException(status_code=400, detail="Query parameter 'q' cannot be empty")

    # Sanitiza a query para evitar ReDoS (Regular Expression Denial of Service)
    sanitized_query = re.escape(q.strip())

    repository = BossRepository(db)

    # Calcula skip baseado na página
    skip = (page - 1) * limit

    # Busca bosses e total
    bosses = await repository.search_by_name(query=sanitized_query, skip=skip, limit=limit)
    total = await repository.count_by_search(query=sanitized_query)

    # Busca última atualização
    jobs_repo = SystemJobsRepository(db)
    status = await jobs_repo.get_scraper_status()
    latest_update = status.last_run.isoformat() if status and status.last_run else None

    # Calcula número de páginas
    pages = (total + limit - 1) // limit if total > 0 else 0

    # Converte BossModel para BossShortSchema
    items = [
        BossShortSchema(
            name=boss.name,
            slug=boss.slug or boss.get_slug(),
            visuals=boss.visuals,
            hp=boss.hp,
            speed=boss.speed,
            location=boss.location,
            bosstiary=boss.bosstiary,
        )
        for boss in bosses
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=len(items),
        pages=pages,
        latest_update=latest_update,
    )


@router.get(
    "/{slug}",
    response_model=BossModel,
    summary="Obter detalhes de um boss",
    description="Retorna os detalhes completos de um boss pelo slug.",
    responses={
        200: {"description": "Boss encontrado e retornado com sucesso"},
        404: {"description": "Boss não encontrado"},
        422: {"description": "Parâmetros de validação inválidos"},
        500: {"description": "Erro interno do servidor"},
    },
)
async def get_boss_by_slug(
    request: Request,  # noqa: ARG001 - usado pelo slowapi para extrair o IP
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
