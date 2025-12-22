"""Script de diagnóstico de rede para MongoDB (DNS e TLS).

Uso típico (dentro do container):

    python debug_network.py --host cluster0.abc123.mongodb.net --port 27017

Ou deixando que o script extraia host/porta da variável de ambiente
MONGODB_URL/MONGO_URL (connection string do Atlas ou local).
"""

from __future__ import annotations

import argparse
import socket
import ssl
import sys
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import certifi
from app.core.config import settings


@dataclass
class DnsResult:
    ok: bool
    host: str
    ip: Optional[str]
    error: Optional[str] = None


@dataclass
class TlsResult:
    ok: bool
    host: str
    port: int
    error: Optional[str] = None


def parse_mongo_url(url: str) -> tuple[str, int]:
    """Extrai host e porta de uma connection string MongoDB.

    Suporta URLs do tipo:
    - mongodb://host:port/db
    - mongodb+srv://host/db  (porta padrão 27017)
    """
    # motor/pymongo aceitam múltiplos hosts separados por vírgula;
    # aqui pegamos apenas o primeiro para diagnóstico.
    if "," in url:
        url = url.split(",", 1)[0]

    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 27017
    return host, port


def diagnose_dns(host: str) -> DnsResult:
    """Testa resolução DNS usando socket.gethostbyname."""
    try:
        ip = socket.gethostbyname(host)
        return DnsResult(ok=True, host=host, ip=ip)
    except socket.gaierror as exc:
        return DnsResult(ok=False, host=host, ip=None, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return DnsResult(ok=False, host=host, ip=None, error=str(exc))


def diagnose_tls(host: str, port: int) -> TlsResult:
    """Testa handshake TLS usando ssl + certifi."""
    context = ssl.create_default_context(cafile=certifi.where())

    try:
        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host):
                # Se chegar aqui, handshake TLS foi bem-sucedido
                return TlsResult(ok=True, host=host, port=port)
    except Exception as exc:  # noqa: BLE001
        return TlsResult(ok=False, host=host, port=port, error=str(exc))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnóstico de DNS e TLS para o host do MongoDB "
            "(útil em ambientes como Render/containers)."
        )
    )
    parser.add_argument(
        "--host",
        help=(
            "Host a ser testado. Se omitido, será extraído de MONGODB_URL/MONGO_URL "
            f"(atual: {settings.mongodb_url})"
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Porta a ser testada (padrão: 27017, ou a porta da URL do MongoDB).",
    )

    args = parser.parse_args(argv)

    # Resolve host/porta a partir dos argumentos ou da URL de configuração
    if args.host:
        host = args.host
        port = args.port or 27017
    else:
        host, default_port = parse_mongo_url(settings.mongodb_url)
        port = args.port or default_port

    print("=" * 80)
    print("🔍 Debug de Rede para MongoDB")
    print("=" * 80)
    print(f"Host alvo : {host}")
    print(f"Porta     : {port}")
    print(f"Mongo URL : {settings.mongodb_url}")
    print("-" * 80)

    # Teste de DNS
    dns_result = diagnose_dns(host)
    if dns_result.ok:
        print("✅ DNS OK")
        print(f"   {host} -> {dns_result.ip}")
    else:
        print("❌ DNS FALHOU")
        print(f"   Host: {dns_result.host}")
        print(f"   Erro: {dns_result.error}")
        print()
        print("Conclusão: problema de DNS (ex.: NXDOMAIN ou falha de resolução).")
        return 1

    print("-" * 80)

    # Teste de TLS
    tls_result = diagnose_tls(host, port)
    if tls_result.ok:
        print("✅ TLS OK")
        print(f"   Handshake TLS bem-sucedido com {host}:{port}")
        print()
        print("Conclusão: DNS e TLS OK; se ainda houver erro na aplicação,")
        print("verifique string de conexão, credenciais ou firewall/regras de rede.")
        return 0

    print("❌ TLS FALHOU")
    print(f"   Host: {tls_result.host}")
    print(f"   Porta: {tls_result.port}")
    print(f"   Erro: {tls_result.error}")
    print()
    print("Conclusão: DNS OK, porém handshake TLS falhou (problema de certificado,")
    print("cadeia de confiança, SNI ou política de rede).")
    return 2


if __name__ == "__main__":  # pragma: no cover - script utilitário
    sys.exit(main())
