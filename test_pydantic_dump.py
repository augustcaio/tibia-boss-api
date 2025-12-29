from typing import List, Optional
from pydantic import BaseModel, ConfigDict
import json

class BossVisuals(BaseModel):
    gif_url: Optional[str] = None
    filename: Optional[str] = None

class BossModel(BaseModel):
    name: str
    slug: Optional[str] = None
    hp: Optional[int] = None
    visuals: Optional[BossVisuals] = None
    model_config = ConfigDict(frozen=False, extra="ignore")

# Test model_dump
boss = BossModel(name="Morgaroth", hp=100000)
boss.visuals = BossVisuals(filename="Morgaroth.gif", gif_url="https://example.com/morgaroth.gif")

print("Boss dict:")
print(json.dumps(boss.model_dump(), indent=2))

boss_no_visuals = BossModel(name="Test Boss", hp=50)
print("\nBoss no visuals dict:")
print(json.dumps(boss_no_visuals.model_dump(), indent=2))

