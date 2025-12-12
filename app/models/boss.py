"""Modelo Pydantic para dados de Bosses do Tibia."""

import re
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class BossVisuals(BaseModel):
    """Modelo para dados visuais do boss."""

    gif_url: Optional[str] = None
    filename: Optional[str] = None


class BossModel(BaseModel):
    """Modelo para representar um Boss do Tibia."""

    name: str
    slug: Optional[str] = None
    hp: Optional[int] = None
    exp: Optional[int] = None
    walks_through: List[str] = []
    immunities: List[str] = []
    visuals: Optional[BossVisuals] = None

    @field_validator("hp", mode="before")
    @classmethod
    def sanitize_hp(cls, v):
        """
        Sanitiza o valor de HP.

        Exemplos:
            "50,000 (estimated)" → 50000
            "???" → None
            "Variable" → None
            "100000" → 100000
        """
        if v is None:
            return None

        if isinstance(v, int):
            return v

        if isinstance(v, str):
            # Remove espaços
            v = v.strip()

            # Casos especiais que devem retornar None
            if v.lower() in ("???", "variable", "unknown", "n/a", ""):
                return None

            # Remove parênteses e conteúdo dentro (ex: "(estimated)")
            v = re.sub(r"\([^)]*\)", "", v).strip()

            # Remove vírgulas e espaços
            v = v.replace(",", "").replace(" ", "")

            # Tenta extrair apenas números
            numbers = re.findall(r"\d+", v)
            if numbers:
                return int("".join(numbers))

        return None

    @field_validator("exp", mode="before")
    @classmethod
    def sanitize_exp(cls, v):
        """
        Sanitiza o valor de EXP.

        Mesma lógica do sanitize_hp.
        """
        return cls.sanitize_hp(v)

    @field_validator("walks_through", mode="before")
    @classmethod
    def sanitize_walks_through(cls, v):
        """
        Sanitiza a lista de walks_through.

        Exemplos:
            "Fire, Energy" → ["Fire", "Energy"]
            "Fire, Energy (partial)" → ["Fire", "Energy"]
            "None" → []
        """
        if v is None:
            return []

        if isinstance(v, list):
            return [item.strip() for item in v if item.strip()]

        if isinstance(v, str):
            v = v.strip()

            # Casos especiais
            if v.lower() in ("none", "n/a", "???", ""):
                return []

            # Remove parênteses e conteúdo dentro
            v = re.sub(r"\([^)]*\)", "", v).strip()

            # Divide por vírgula
            items = [item.strip() for item in v.split(",") if item.strip()]

            return items

        return []

    @field_validator("immunities", mode="before")
    @classmethod
    def sanitize_immunities(cls, v):
        """
        Sanitiza a lista de immunities.

        Mesma lógica do sanitize_walks_through.
        """
        return cls.sanitize_walks_through(v)

    def get_slug(self) -> str:
        """
        Retorna o slug do boss, gerando automaticamente se não fornecido.

        Returns:
            Slug do boss
        """
        if self.slug:
            return self.slug
        return self._generate_slug(self.name)

    @staticmethod
    def _generate_slug(name: str) -> str:
        """
        Gera um slug a partir do nome do boss.

        Args:
            name: Nome do boss

        Returns:
            Slug gerado (ex: "Morgaroth" -> "morgaroth")
        """
        # Remove caracteres especiais, converte para minúsculas
        slug = re.sub(r"[^\w\s-]", "", name.lower())
        # Remove espaços extras e substitui por hífens
        slug = re.sub(r"[-\s]+", "-", slug)
        # Remove hífens no início e fim
        slug = slug.strip("-")
        return slug

    model_config = ConfigDict(
        frozen=False,
        extra="ignore",  # Ignora campos extras do wiki
    )
