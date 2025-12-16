"""Rotas relacionadas a Bosses."""

from fastapi import APIRouter

router = APIRouter(
    prefix="/bosses",
    tags=["bosses"],
)

# Rotas serão adicionadas nas próximas tasks
# Por enquanto, apenas a estrutura do router

