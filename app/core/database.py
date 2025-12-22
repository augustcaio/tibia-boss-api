"""Conexão MongoDB usando Motor (async driver) com Dependency Injection."""

import logging
from typing import Optional

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

    logger.info("🔌 Tentativa de conexão 'Insegura' (Bypass SSL)...")

    try:
        # ⚠️ MODO DE DIAGNÓSTICO:
        # Desativamos a verificação de certificados e hostnames para isolar
        # se o problema no Render é a cadeia de confiança ou o protocolo.
        client_options = {
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 30000,
            "socketTimeoutMS": 30000,
            "tls": True,
            "tlsAllowInvalidCertificates": True,
            "tlsAllowInvalidHostnames": True,
        }

        # Para Mongo local sem TLS (detectado por ausência de Atlas na URL)
        if "mongodb.net" not in mongodb_url and not mongodb_url.startswith("mongodb+srv://"):
            client_options["tls"] = False
            client_options.pop("tlsAllowInvalidCertificates")
            client_options.pop("tlsAllowInvalidHostnames")

        _client = AsyncIOMotorClient(mongodb_url, **client_options)
        _database = _client[database_name]

        # Testa a conexão
        await _client.admin.command("ping")
        logger.info(f"✅ Conectado ao MongoDB: {database_name} (SSL Bypass ativo)")

        # Cria os índices
        await _create_indexes(_database)

        return _database

    except Exception as e:
        logger.error(f"❌ Falha Total ao conectar ao MongoDB: {e}")
        # Mantemos o soft startup (não levantamos exceção aqui,
        # o lifespan em main.py já trata isso marcando db_connected=False)
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
