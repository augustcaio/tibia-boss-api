"""Aplicação FastAPI principal."""

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.routers import admin, bosses, health
from app.core.config import settings
from app.core.database import close_database, init_database
from app.core.rate_limit import (
    RateLimitExceeded,
    SlowAPIMiddleware,
    _rate_limit_exceeded_handler,
    limiter,
)
from app.services.scraper_job import run_scraper_job

# Scheduler global para o processo FastAPI
scheduler = AsyncIOScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager para inicializar e fechar recursos.

    - Inicializa conexão MongoDB e cria índices
    - Configura o APScheduler com job semanal
    - Fecha conexão e desliga o scheduler ao encerrar
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Debug: mostra qual URL está sendo usada
    logger.info(f"🔍 Tentando conectar ao MongoDB: {settings.mongodb_url}")
    
    # Startup: Inicializa MongoDB e cria índices
    await init_database(
        mongodb_url=settings.mongodb_url,
        database_name=settings.database_name,
    )

    # Configura job semanal de sincronização (Mongo Mutex em run_scraper_job)
    scheduler.add_job(
        run_scraper_job,
        trigger="cron",
        day_of_week="tue",
        hour=10,
        timezone="UTC",
        id="weekly_scraper_sync",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()

    yield

    # Shutdown: encerra scheduler e fecha conexão MongoDB
    scheduler.shutdown(wait=False)
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

# Configurações de rate limiting (slowapi)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Middleware de hosts confiáveis
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts,
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sobrescreve a função openapi para usar versão 3.0.3
app.openapi = custom_openapi

# Inclui os routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(bosses.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Endpoint raiz."""
    return {"message": "Tibia Boss API", "version": "0.1.0"}

