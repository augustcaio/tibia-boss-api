"""Configurações da aplicação usando Pydantic Settings."""

import os
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


# ===== DEBUG CRÍTICO: FORCE PRINT =====
# Força impressão direta no stdout (não usa logger que pode ser filtrado)
print("=" * 80)
print("🔍 DEBUG: Verificando variáveis de ambiente")
print("=" * 80)

# Tenta todas as variações possíveis
mongodb_url_variants = [
    "MONGODB_URL",
    "mongodb_url", 
    "MONGO_URL",
    "MONGODB_URI",
    "DATABASE_URL",
]

for variant in mongodb_url_variants:
    value = os.environ.get(variant)
    if value:
        # Mascara a senha para não expor nos logs
        masked = value
        if "@" in value and "://" in value:
            protocol = value.split("://")[0]
            rest = value.split("://")[1]
            if "@" in rest:
                creds = rest.split("@")[0]
                host_part = rest.split("@")[1]
                masked = f"{protocol}://*****:*****@{host_part}"
        print(f"✅ {variant} = {masked}")
    else:
        print(f"❌ {variant} = (não definida)")

print("=" * 80)

# Cria instância das configurações
settings = Settings()

# Mostra o que foi carregado
print(f"📌 Settings carregados:")
print(f"   mongodb_url: {settings.mongodb_url[:50]}...")
print(f"   database_name: {settings.database_name}")
print("=" * 80)
