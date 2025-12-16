"""Conexão MongoDB usando Motor (async driver).

Este módulo mantém compatibilidade com código existente.
A implementação real está em app.core.database.
"""

# Re-exporta funções de app.core.database para manter compatibilidade
from app.core.database import (
    close_database,
    get_database,
    init_database,
)

__all__ = ["get_database", "init_database", "close_database"]

