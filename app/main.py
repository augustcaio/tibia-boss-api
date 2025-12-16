"""Aplicação FastAPI principal."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers import bosses, health
from app.core.config import settings
from app.core.database import close_database, init_database


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


def custom_openapi():
    """Gera schema OpenAPI 3.0.3 com servidor padrão."""
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Força versão OpenAPI 3.0.3
    openapi_schema["openapi"] = "3.0.3"
    # Adiciona servidor padrão se não existir
    if "servers" not in openapi_schema or not openapi_schema.get("servers"):
        openapi_schema["servers"] = [
            {"url": "http://localhost:8000", "description": "Servidor local de desenvolvimento"}
        ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI(
    title="Tibia Boss API",
    description="""
    API RESTful para scraping e disponibilização de dados de Bosses do Tibia Wiki.
    
    ## Funcionalidades
    
    * **Listagem paginada** de bosses
    * **Busca por nome** usando regex case insensitive
    * **Detalhes completos** de cada boss pelo slug
    * **Health check** para monitoramento
    
    ## Fonte de Dados
    
    Os dados são extraídos do [TibiaWiki](https://tibia.fandom.com) e atualizados periodicamente.
    """,
    version="0.1.0",
    contact={
        "name": "Tibia Boss API Team",
        "url": "https://github.com/tibia-boss-api",
    },
    lifespan=lifespan,
    redoc_url=None,  # ReDoc desabilitado
)

# Sobrescreve a função openapi para usar versão 3.0.3
app.openapi = custom_openapi

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui os routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(bosses.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Endpoint raiz."""
    return {"message": "Tibia Boss API", "version": "0.1.0"}

