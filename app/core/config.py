"""Configurações da aplicação usando Pydantic Settings."""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação."""

    # MongoDB
    mongodb_url: str = "mongodb://127.0.0.1:27017"
    database_name: str = "tibia_bosses"

    # Admin
    admin_secret: str = "changeme"

    # Segurança / Hosts confiáveis
    allowed_hosts: List[str] = ["localhost", "127.0.0.1", ".onrender.com"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignora variáveis extras do ambiente
    )


# Debug: Mostra as variáveis de ambiente disponíveis no startup
import os
import logging
logger = logging.getLogger(__name__)

# Verifica se MONGODB_URL está no ambiente
mongodb_url_env = os.environ.get("MONGODB_URL") or os.environ.get("mongodb_url")
if mongodb_url_env:
    logger.info("✅ Variável MONGODB_URL encontrada no ambiente")
else:
    logger.warning("⚠️ Variável MONGODB_URL NÃO encontrada - usando default")

settings = Settings()
