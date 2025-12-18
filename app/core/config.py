"""Configurações da aplicação usando Pydantic Settings."""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação."""

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "tibia_bosses"

    # Admin
    admin_secret: str = "changeme"

    # Segurança / Hosts confiáveis
    allowed_hosts: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()

