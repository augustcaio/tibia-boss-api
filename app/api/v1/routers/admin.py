"""Rotas administrativas para sincronização manual do scraper."""

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, status

from app.core.config import settings
from app.core.rate_limit import limiter
from app.services.scraper_job import run_scraper_job

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@limiter.limit("5/hour")
@router.post(
    "/sync",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Disparar sincronização manual de bosses",
    description=(
        "Dispara manualmente o job de sincronização de bosses, reutilizando o mesmo "
        "pipeline do scheduler e respeitando o lock distribuído em MongoDB."
    ),
    responses={
        202: {"description": "Job de sincronização agendado com sucesso."},
        401: {"description": "Token de administrador inválido."},
    },
)
async def trigger_sync(
    background_tasks: BackgroundTasks,
    x_admin_token: str = Header(..., alias="X-Admin-Token"),
):
    """
    Endpoint administrativo para disparar sincronização manual.

    Regras:
    - Requer header `X-Admin-Token` igual a `settings.ADMIN_SECRET`
    - Usa BackgroundTasks para não travar o request HTTP
    - Reutiliza o mesmo job do APScheduler (run_scraper_job), que respeita o lock
    """
    if x_admin_token != settings.admin_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )

    background_tasks.add_task(run_scraper_job)
    return {"detail": "Sync job scheduled"}


