"""Conexão MongoDB usando Motor (async driver) com Dependency Injection."""

import logging
from typing import Optional

import certifi
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Variável global para armazenar a conexão
_database: Optional[AsyncIOMotorDatabase] = None
_client: Optional[AsyncIOMotorClient] = None


def get_database() -> AsyncIOMotorDatabase:
    """
    Retorna a instância do banco de dados.

    Raises:
        HTTPException: 503 se o banco não foi inicializado ou está indisponível
    """
    if _database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable. Please try again later.",
        )
    return _database


async def init_database(
    mongodb_url: str = "mongodb://localhost:27017",
    database_name: str = "tibia_bosses",
) -> AsyncIOMotorDatabase:
    """
    Inicializa a conexão com o MongoDB e cria os índices.
    """
    global _database, _client

    if _database is not None:
        logger.warning("Database já foi inicializado. Retornando instância existente.")
        return _database

    logger.info("🔌 Conectando ao MongoDB (Standard Mode)...")

    try:
        # Configuração limpa e correta para Cluster Atlas ou Local
        client_options = {
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 30000,
            "socketTimeoutMS": 30000,
        }

        # Se for Atlas (detectado pela URL), habilitamos TLS com certifi
        if "mongodb.net" in mongodb_url or mongodb_url.startswith("mongodb+srv://"):
            client_options.update(
                {
                    "tls": True,
                    "tlsCAFile": certifi.where(),
                }
            )
        else:
            # Mongo local sem TLS
            client_options["tls"] = False

        _client = AsyncIOMotorClient(mongodb_url, **client_options)
        _database = _client[database_name]

        # Testa a conexão
        await _client.admin.command("ping")
        logger.info(f"✅ Conectado ao MongoDB: {database_name} com sucesso!")

        # Cria os índices
        await _create_indexes(_database)

        return _database

    except Exception as e:
        logger.error(f"❌ Erro Crítico Mongo: {e}")
        # Mantemos o soft startup através do raise (o lifespan em main.py trata isso)
        raise


async def _create_indexes(db: AsyncIOMotorDatabase):
    """Cria os índices necessários no banco de dados."""
    try:
        await db.bosses.create_index("slug", unique=True)
        await db.bosses.create_index("name")
        logger.info("Índices criados com sucesso")
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
