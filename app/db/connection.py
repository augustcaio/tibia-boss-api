"""Conexão MongoDB usando Motor (async driver)."""

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Variável global para armazenar a conexão
_database: Optional[AsyncIOMotorDatabase] = None
_client: Optional[AsyncIOMotorClient] = None


def get_database() -> AsyncIOMotorDatabase:
    """
    Retorna a instância do banco de dados.

    Raises:
        RuntimeError: Se o banco não foi inicializado

    Returns:
        Instância do AsyncIOMotorDatabase
    """
    if _database is None:
        raise RuntimeError("Database não foi inicializado. Chame init_database() primeiro.")
    return _database


async def init_database(
    mongodb_url: str = "mongodb://localhost:27017",
    database_name: str = "tibia_bosses",
) -> AsyncIOMotorDatabase:
    """
    Inicializa a conexão com o MongoDB e cria os índices.

    Args:
        mongodb_url: URL de conexão do MongoDB (padrão: mongodb://localhost:27017)
        database_name: Nome do banco de dados (padrão: tibia_bosses)

    Returns:
        Instância do AsyncIOMotorDatabase
    """
    global _database, _client

    if _database is not None:
        logger.warning("Database já foi inicializado. Retornando instância existente.")
        return _database

    try:
        # Cria o cliente MongoDB
        _client = AsyncIOMotorClient(mongodb_url)
        _database = _client[database_name]

        # Testa a conexão
        await _client.admin.command("ping")
        logger.info(f"Conectado ao MongoDB: {database_name}")

        # Cria os índices
        await _create_indexes(_database)

        return _database

    except Exception as e:
        logger.error(f"Erro ao conectar ao MongoDB: {e}")
        raise


async def _create_indexes(db: AsyncIOMotorDatabase):
    """
    Cria os índices necessários no banco de dados.

    Args:
        db: Instância do banco de dados
    """
    try:
        # Índice único no campo slug (trava de segurança contra duplicidade)
        await db.bosses.create_index("slug", unique=True)
        logger.info("Índice 'slug' criado com sucesso (unique=True)")

        # Índice no campo name para buscas rápidas
        await db.bosses.create_index("name")
        logger.info("Índice 'name' criado com sucesso")

    except Exception as e:
        logger.error(f"Erro ao criar índices: {e}")
        raise


async def close_database():
    """Fecha a conexão com o MongoDB."""
    global _database, _client

    if _client:
        _client.close()
        _client = None
        _database = None
        logger.info("Conexão com MongoDB fechada")

