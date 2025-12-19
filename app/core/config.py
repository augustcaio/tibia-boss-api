"""Configurações da aplicação usando Pydantic Settings."""

import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação."""

    # MongoDB - aceita MONGODB_URL ou MONGO_URL
    mongodb_url: str = os.environ.get("MONGODB_URL") or os.environ.get(
        "MONGO_URL") or "mongodb://127.0.0.1:27017"
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


# Cria instância das configurações
settings = Settings()

# Debug: mostra o que foi carregado
print("=" * 80)
print("🚀 Tibia Boss API - Inicializando")
print("=" * 80)
print(f"✅ MongoDB URL: {settings.mongodb_url[:60]}...")
print(f"✅ Database: {settings.database_name}")
print("=" * 80)
