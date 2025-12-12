"""Aplicação FastAPI principal."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db.connection import close_database, init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager para inicializar e fechar recursos.

    - Inicializa conexão MongoDB e cria índices
    - Fecha conexão ao encerrar
    """
    # Startup: Inicializa MongoDB e cria índices
    await init_database(
        mongodb_url=settings.mongodb_url,
        database_name=settings.database_name,
    )
    yield
    # Shutdown: Fecha conexão MongoDB
    await close_database()


app = FastAPI(
    title="Tibia Boss API",
    description="API para scraping e disponibilização de dados de Bosses do Tibia Wiki",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Endpoint raiz."""
    return {"message": "Tibia Boss API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Endpoint de health check."""
    from app.db.connection import get_database

    try:
        db = get_database()
        # Testa conexão
        await db.client.admin.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

