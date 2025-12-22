"""Aplicação FastAPI principal."""

from contextlib import asynccontextmanager
import logging
import os

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
logger = logging.getLogger(__name__)
db_connected: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager para inicializar e fechar recursos.

    - Inicializa conexão MongoDB e cria índices
    - Configura o APScheduler com job semanal
    - Fecha conexão e desliga o scheduler ao encerrar
    """
    # Startup: Inicializa MongoDB e cria índices
    print("🔌 Conectando ao MongoDB...")
    allow_start_without_db = os.getenv("ALLOW_START_WITHOUT_DB", "").strip().lower() in (
        "",
        "1",
        "true",
        "yes",
        "on",
    )

    db_ready = False
    try:
        await init_database(
            mongodb_url=settings.mongodb_url,
            database_name=settings.database_name,
        )
        db_ready = True
        app.state.db_connected = True
        print("✅ MongoDB conectado com sucesso!")
    except Exception:
        # Modo degradado (Circuit Breaker / Soft Startup):
        # - Não derruba o processo caso o Mongo esteja indisponível.
        # - Marca o estado da aplicação como desconectado.
        # - Em produção, rotas que dependem de DB devolverão 503.
        logger.exception("Falha ao conectar ao MongoDB durante o startup.")
        app.state.db_connected = False
        if not allow_start_without_db:
            # Mantém opção de falhar duro via variável de ambiente,
            # mas por padrão a API sobe em modo degradado.
            raise
        print("⚠️ MongoDB indisponível. API iniciará em modo degradado (sem DB).")

    # Configura job semanal de sincronização (Mongo Mutex em run_scraper_job)
    if db_ready:
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
    if scheduler.running:
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
    # Permite qualquer host para não bloquear health checks internos (ex.: Render).
    # Em produção, ajuste para a lista específica de domínios confiáveis.
    allowed_hosts=["*"],
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


@app.head("/")
async def root_head():
    """HEAD para health checks que não precisam de corpo."""
    return None
