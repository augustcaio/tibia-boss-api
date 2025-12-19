"""Rotas de health check."""

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core import database as dbmod
from app.core.database import get_database

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get(
    "",
    summary="Health check",
    description="Verifica se a API e o banco de dados estão funcionando corretamente.",
    responses={
        200: {"description": "Status da API e conexão com banco de dados"},
        500: {"description": "Erro ao verificar saúde do sistema"},
    },
)
async def health_check(db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Endpoint de health check.
    
    Verifica se a API e o banco de dados estão funcionando corretamente.
    
    Returns:
        Dict com status da API e conexão com o banco
    """
    client = getattr(dbmod, "_client", None)
    if client is None:
        return {"status": "ok", "db": "disconnected", "error": "db_not_initialized"}

    try:
        await client.admin.command("ping")
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "ok", "db": "disconnected", "error": str(e)}

