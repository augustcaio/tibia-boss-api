"""Configuração de rate limiting usando slowapi."""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

__all__ = [
    "Limiter",
    "SlowAPIMiddleware",
    "RateLimitExceeded",
    "_rate_limit_exceeded_handler",
    "limiter",
]


