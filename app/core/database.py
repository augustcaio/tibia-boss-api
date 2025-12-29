"""Conexão MongoDB usando Motor (async driver) com Dependency Injection."""

import logging
import os
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

    logger.info("🔌 Conectando ao MongoDB...")

    # Verifica se estamos em ambiente de teste (Github Actions / Local Tests)
    is_testing = os.getenv("TESTING") == "true"

    try:
        if is_testing:
            # Conexão Simples para Testes (Sem SSL, Sem Certifi)
            logger.info("🧪 Modo de Teste Detectado: Conectando sem SSL")
            client_options = {
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 30000,
                "socketTimeoutMS": 30000,
                "tls": False,
            }
            _client = AsyncIOMotorClient(mongodb_url, **client_options)
        else:
            # Conexão de Produção (Com SSL e Certifi)
            logger.info("🌐 Modo de Produção: Conectando com SSL (certifi)")
            client_options = {
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 30000,
                "socketTimeoutMS": 30000,
                "tls": True,
                "tlsCAFile": certifi.where(),
            }
            # Se for Mongo local (sem Atlas na URL), desativa TLS
            if "mongodb.net" not in mongodb_url and not mongodb_url.startswith("mongodb+srv://"):
                client_options["tls"] = False
                client_options.pop("tlsCAFile")

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
        if is_testing:
            # Em testes, queremos que falhe duro para identificar o erro
            raise e
        # Em prod, mantemos o soft startup (levantando exceção para o lifespan tratar)
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
