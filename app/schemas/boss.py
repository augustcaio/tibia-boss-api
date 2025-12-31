"""Schemas específicos para Bosses."""

from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.boss import BosstiaryStats, BossVisuals


class BossShortSchema(BaseModel):
    """Schema reduzido para listagem de bosses (sem campos pesados)."""

    name: str
    slug: Optional[str] = None
    visuals: Optional[BossVisuals] = None
    hp: Optional[int] = None
    speed: Optional[int] = None
    location: Optional[str] = None
    bosstiary: Optional[BosstiaryStats] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Morgaroth",
                "slug": "morgaroth",
                "hp": 100000,
                "speed": 160,
                "location": "Vampire Hell",
                "bosstiary": {"class_name": "Nemesis", "kills_required": 5},
                "visuals": {
                    "gif_url": "https://tibia.fandom.com/images/Morgaroth.gif",
                    "filename": "Morgaroth.gif",
                },
            }
        }
    )
