"""Database module for Tibia Boss API."""

from app.db.connection import get_database, init_database
from app.db.repository import BossRepository

__all__ = ["get_database", "init_database", "BossRepository"]

