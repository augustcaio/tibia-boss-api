"""Testes para o endpoint de listagem de bosses."""

import pytest
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.database import get_database
from app.db.repository import BossRepository
from app.main import app
from app.models.boss import BossModel, BossVisuals


@pytest.fixture
async def test_database() -> AsyncIOMotorDatabase:
    """Fixture para criar um banco de dados de teste isolado."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["tibia_bosses_test"]
    await client.drop_database("tibia_bosses_test")
    yield db
    await client.drop_database("tibia_bosses_test")
    client.close()


@pytest.fixture
async def populated_repository(test_database: AsyncIOMotorDatabase):
    """Fixture que popula o banco com dados de teste."""
    repository = BossRepository(test_database)
    await repository.collection.delete_many({})

    bosses = []
    for i in range(1, 16):
        boss = BossModel(
            name=f"Test Boss {i:02d}",
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
async def client(test_database, populated_repository):
    """Fixture para criar um cliente HTTP assíncrono para os testes."""
    # Usa dependency_overrides do FastAPI para injetar o banco de teste
    app.dependency_overrides[get_database] = lambda: test_database

    # Usa AsyncClient com ASGITransport para evitar problemas de thread/loop
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_list_bosses_default_pagination(client):
    """Testa listagem com paginação padrão."""
    response = await client.get("/api/v1/bosses")

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert data["total"] == 15
    assert data["page"] == 1
    assert data["size"] <= 20


@pytest.mark.asyncio
async def test_list_bosses_custom_limit(client):
    """Testa listagem com limit customizado."""
    response = await client.get("/api/v1/bosses?limit=5")

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 5
    assert data["size"] == 5
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_bosses_pagination_page_2(client):
    """Testa que página 2 traz itens diferentes da página 1."""
    # Página 1
    response_page1 = await client.get("/api/v1/bosses?page=1&limit=5")
    assert response_page1.status_code == 200
    data_page1 = response_page1.json()
    items_page1 = [item["name"] for item in data_page1["items"]]

    # Página 2
    response_page2 = await client.get("/api/v1/bosses?page=2&limit=5")
    assert response_page2.status_code == 200
    data_page2 = response_page2.json()
    items_page2 = [item["name"] for item in data_page2["items"]]

    # Verifica que são diferentes
    assert items_page1 != items_page2
    assert len(set(items_page1) & set(items_page2)) == 0


@pytest.mark.asyncio
async def test_list_bosses_metadata(client):
    """Testa que os metadados de paginação estão corretos."""
    # Popula o banco via fixture populated_repository
    response = await client.get("/api/v1/bosses?page=2&limit=5")

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 15
    assert data["page"] == 2
    assert data["size"] == 5
    assert data["pages"] == 3


@pytest.mark.asyncio
async def test_list_bosses_projection_excludes_raw_wikitext(client):
    """Testa que a projection não retorna campos pesados."""
    response = await client.get("/api/v1/bosses?limit=1")

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) > 0
    item = data["items"][0]

    assert "name" in item
    assert "slug" in item
    assert "raw_wikitext" not in item
    assert "walks_through" not in item
    assert "immunities" not in item


@pytest.mark.asyncio
async def test_list_bosses_max_limit(client):
    """Testa que o limite máximo de 100 é respeitado."""
    response = await client.get("/api/v1/bosses?limit=150")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_bosses_invalid_page(client):
    """Testa validação de página inválida."""
    response = await client.get("/api/v1/bosses?page=0")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_and_get_slug_routing(client):
    """Testa que as rotas /search e /{slug} funcionam corretamente sem conflito."""
    # 1. Testa busca
    search_resp = await client.get("/api/v1/bosses/search?q=Test")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total"] > 0
    
    # 2. Testa slug (pega o primeiro boss da listagem)
    list_resp = await client.get("/api/v1/bosses?limit=1")
    assert list_resp.status_code == 200
    boss_info = list_resp.json()["items"][0]
    slug = boss_info["slug"]
    
    get_resp = await client.get(f"/api/v1/bosses/{slug}")
    assert get_resp.status_code == 200
    assert get_resp.json()["slug"] == slug
    assert get_resp.json()["name"] == boss_info["name"]
