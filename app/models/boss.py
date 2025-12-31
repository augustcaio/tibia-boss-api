"""Modelo Pydantic para dados de Bosses do Tibia."""

import re
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class BossVisuals(BaseModel):
    """Modelo para dados visuais do boss."""

    gif_url: Optional[str] = None
    filename: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "gif_url": "https://tibia.fandom.com/images/Morgaroth.gif",
                "filename": "Morgaroth.gif",
            }
        }
    )


class BosstiaryStats(BaseModel):
    """Modelo para estatísticas do Bosstiary."""

    class_name: Optional[str] = None  # Bane, Archfoe, Nemesis
    kills_required: Optional[int] = None  # 2500, 60, 5


class BossModel(BaseModel):
    """Modelo para representar um Boss do Tibia."""

    name: str
    slug: Optional[str] = None
    hp: Optional[int] = None
    exp: Optional[int] = None
    speed: Optional[int] = None
    version: Optional[str] = None
    location: Optional[str] = None
    abilities: List[str] = []
    sounds: List[str] = []
    loot: List[str] = []
    walks_through: List[str] = []
    elemental_weaknesses: List[str] = []  # Legado (texto)
    elemental_resistances: List[str] = [] # Legado (texto)
    immunities: List[str] = []
    # Novas resistências percentuais
    resistances: dict[str, int] = {} # Ex: {"physical": 100, "earth": 0, "fire": 85}
    bosstiary: Optional[BosstiaryStats] = None
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

    @field_validator("speed", mode="before")
    @classmethod
    def sanitize_speed(cls, v):
        """Sanitiza o valor de Speed."""
        return cls.sanitize_hp(v)

    @field_validator("abilities", "sounds", "loot", mode="before")
    @classmethod
    def sanitize_list_fields(cls, v):
        """Sanitiza listas de habilidades, sons e loot."""
        return cls.sanitize_walks_through(v)

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

    @field_validator("elemental_weaknesses", mode="before")
    @classmethod
    def sanitize_weaknesses(cls, v):
        """Sanitiza fraquezas elementais."""
        return cls.sanitize_walks_through(v)

    @field_validator("elemental_resistances", mode="before")
    @classmethod
    def sanitize_resistances(cls, v):
        """Sanitiza resistências elementais."""
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
        json_schema_extra={
            "example": {
                "name": "Morgaroth",
                "slug": "morgaroth",
                "hp": 100000,
                "exp": 50000,
                "speed": 160,
                "version": "8.0",
                "location": "Vampire Hell, Feyrist",
                "abilities": ["Melee", "Fireball"],
                "sounds": ["I WILL DEVOUR YOUR SOUL!"],
                "loot": ["Golden Armor", "Great Fireball Rune"],
                "walks_through": ["Fire", "Energy"],
                "elemental_weaknesses": ["Holy", "Ice"],
                "elemental_resistances": ["Fire"],
                "immunities": ["Physical", "Earth"],
                "resistances": {
                    "physical": 100,
                    "earth": 0,
                    "fire": 85,
                    "ice": 100,
                    "energy": 100,
                    "death": 100,
                    "holy": 120
                },
                "bosstiary": {
                    "class_name": "Nemesis",
                    "kills_required": 5,
                },
                "visuals": {
                    "gif_url": "https://tibia.fandom.com/images/Morgaroth.gif",
                    "filename": "Morgaroth.gif",
                },
            }
        },
    )
