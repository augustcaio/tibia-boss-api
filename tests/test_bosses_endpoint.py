"""Testes para o endpoint de listagem de bosses."""

import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.connection import close_database, init_database
from app.db.repository import BossRepository
from app.main import app
from app.models.boss import BossModel, BossVisuals


@pytest.fixture
async def test_database():
    """Fixture para criar um banco de dados de teste."""
    db = await init_database(
        mongodb_url="mongodb://localhost:27017",
        database_name="tibia_bosses_test",
    )
    yield db
    # Limpa após os testes
    await db.client.drop_database("tibia_bosses_test")
    await close_database()


@pytest.fixture
async def populated_repository(test_database: AsyncIOMotorDatabase):
    """Fixture que popula o banco com dados de teste."""
    repository = BossRepository(test_database)

    # Cria 15 bosses de teste
    bosses = []
    for i in range(1, 16):
        boss = BossModel(
            name=f"Test Boss {i}",
            hp=10000 * i,
            exp=5000 * i,
            visuals=BossVisuals(
                gif_url=f"https://example.com/boss{i}.gif",
                filename=f"boss{i}.gif",
            ),
        )
        bosses.append(boss)

    await repository.upsert_batch(bosses)
    return repository


@pytest.fixture
def client(test_database, populated_repository):
    """Fixture para criar um cliente de teste."""
    # Monkey patch: substitui get_database para retornar o banco de teste
    from app.core import database

    original_get_database = database.get_database
    database.get_database = lambda: test_database

    with TestClient(app) as test_client:
        yield test_client

    # Restaura a função original
    database.get_database = original_get_database


def test_list_bosses_default_pagination(client):
    """Testa listagem com paginação padrão."""
    response = client.get("/api/v1/bosses")

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data

    assert data["page"] == 1
    assert data["size"] <= 20  # Default limit
    assert data["total"] == 15  # Total de bosses criados


def test_list_bosses_custom_limit(client):
    """Testa listagem com limit customizado."""
    response = client.get("/api/v1/bosses?limit=5")

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 5
    assert data["size"] == 5
    assert data["page"] == 1


def test_list_bosses_pagination_page_2(client):
    """Testa que página 2 traz itens diferentes da página 1."""
    # Página 1
    response_page1 = client.get("/api/v1/bosses?page=1&limit=5")
    assert response_page1.status_code == 200
    data_page1 = response_page1.json()
    items_page1 = [item["name"] for item in data_page1["items"]]

    # Página 2
    response_page2 = client.get("/api/v1/bosses?page=2&limit=5")
    assert response_page2.status_code == 200
    data_page2 = response_page2.json()
    items_page2 = [item["name"] for item in data_page2["items"]]

    # Verifica que são diferentes
    assert items_page1 != items_page2
    assert len(set(items_page1) & set(items_page2)) == 0  # Nenhum item em comum


def test_list_bosses_metadata(client):
    """Testa que os metadados de paginação estão corretos."""
    response = client.get("/api/v1/bosses?page=2&limit=5")

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 15
    assert data["page"] == 2
    assert data["size"] == 5
    assert data["pages"] == 3  # 15 itens / 5 por página = 3 páginas


def test_list_bosses_projection_excludes_raw_wikitext(client):
    """Testa que a projection não retorna campos pesados como raw_wikitext."""
    response = client.get("/api/v1/bosses?limit=1")

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) > 0
    item = data["items"][0]

    # Verifica campos presentes
    assert "name" in item
    assert "slug" in item

    # Verifica que campos pesados não estão presentes
    assert "raw_wikitext" not in item
    assert "walks_through" not in item
    assert "immunities" not in item


def test_list_bosses_max_limit(client):
    """Testa que o limite máximo de 100 é respeitado."""
    response = client.get("/api/v1/bosses?limit=150")  # Tenta exceder o máximo

    # FastAPI deve validar e retornar erro 422
    assert response.status_code == 422


def test_list_bosses_invalid_page(client):
    """Testa validação de página inválida."""
    response = client.get("/api/v1/bosses?page=0")  # Página deve ser >= 1

    assert response.status_code == 422


def test_search_bosses_rate_limit_headers_and_blocking(client):
    """Testa que o rate limiting aplica headers e bloqueia após o limite."""
    # Primeira requisição deve passar e conter headers de rate limit
    response = client.get("/api/v1/bosses/search?q=Test")
    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers

    # Limite configurado para 20/minute → a 21ª deve retornar 429
    last_status = None
    for _ in range(21):
        resp = client.get("/api/v1/bosses/search?q=Test")
        last_status = resp.status_code

    assert last_status == 429

