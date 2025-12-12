"""Testes de integração para BossRepository."""

import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.connection import close_database, init_database
from app.db.repository import BossRepository
from app.models.boss import BossModel, BossVisuals


@pytest.fixture
async def test_database():
    """Fixture para criar um banco de dados de teste."""
    # Usa um banco de teste diferente
    db = await init_database(
        mongodb_url="mongodb://localhost:27017",
        database_name="tibia_bosses_test",
    )
    yield db
    # Limpa após os testes
    await db.client.drop_database("tibia_bosses_test")
    await close_database()


@pytest.fixture
async def repository(test_database: AsyncIOMotorDatabase):
    """Fixture para criar uma instância do repositório."""
    return BossRepository(test_database)


@pytest.mark.asyncio
async def test_upsert_creates_boss(repository: BossRepository):
    """Testa que upsert cria um novo boss."""
    boss = BossModel(
        name="Test Boss",
        hp=50000,
        exp=10000,
        visuals=BossVisuals(gif_url="https://example.com/test.gif", filename="test.gif"),
    )

    result = await repository.upsert(boss)

    assert result is True

    # Verifica que foi salvo
    saved_boss = await repository.find_by_slug(boss.get_slug())
    assert saved_boss is not None
    assert saved_boss.name == "Test Boss"
    assert saved_boss.hp == 50000
    assert saved_boss.visuals is not None
    assert saved_boss.visuals.gif_url == "https://example.com/test.gif"


@pytest.mark.asyncio
async def test_upsert_idempotent(repository: BossRepository):
    """Testa que inserir o mesmo boss 2 vezes resulta em 1 documento (atualizado)."""
    boss = BossModel(
        name="Idempotent Boss",
        hp=30000,
        exp=5000,
    )

    # Primeira inserção
    result1 = await repository.upsert(boss)
    assert result1 is True

    # Segunda inserção (deve atualizar, não criar duplicata)
    boss.hp = 35000  # Altera o HP
    result2 = await repository.upsert(boss)
    assert result2 is True

    # Verifica que há apenas 1 documento
    count = await repository.count()
    assert count == 1

    # Verifica que o documento foi atualizado
    saved_boss = await repository.find_by_slug(boss.get_slug())
    assert saved_boss is not None
    assert saved_boss.hp == 35000  # HP atualizado
    assert saved_boss.name == "Idempotent Boss"


@pytest.mark.asyncio
async def test_upsert_batch(repository: BossRepository):
    """Testa upsert em lote."""
    bosses = [
        BossModel(name=f"Boss {i}", hp=10000 + i, exp=5000 + i)
        for i in range(5)
    ]

    success_count = await repository.upsert_batch(bosses)

    assert success_count == 5

    # Verifica que todos foram salvos
    count = await repository.count()
    assert count == 5


@pytest.mark.asyncio
async def test_find_by_slug(repository: BossRepository):
    """Testa busca por slug."""
    boss = BossModel(
        name="Slug Test Boss",
        hp=40000,
        visuals=BossVisuals(gif_url="https://example.com/slug.gif"),
    )

    await repository.upsert(boss)

    # Busca pelo slug
    found = await repository.find_by_slug(boss.get_slug())
    assert found is not None
    assert found.name == "Slug Test Boss"
    assert found.visuals.gif_url == "https://example.com/slug.gif"


@pytest.mark.asyncio
async def test_find_by_name(repository: BossRepository):
    """Testa busca por nome."""
    boss = BossModel(name="Name Test Boss", hp=25000)

    await repository.upsert(boss)

    # Busca pelo nome
    found = await repository.find_by_name("Name Test Boss")
    assert found is not None
    assert found.name == "Name Test Boss"
    assert found.hp == 25000


@pytest.mark.asyncio
async def test_slug_generation(repository: BossRepository):
    """Testa que o slug é gerado automaticamente."""
    boss = BossModel(name="Morgaroth", hp=77000)

    # Não fornece slug explicitamente
    assert boss.slug is None

    # Upsert deve gerar o slug automaticamente
    await repository.upsert(boss)

    # Verifica que o slug foi gerado e salvo
    saved_boss = await repository.find_by_slug("morgaroth")
    assert saved_boss is not None
    assert saved_boss.name == "Morgaroth"


@pytest.mark.asyncio
async def test_slug_with_special_characters(repository: BossRepository):
    """Testa geração de slug com caracteres especiais."""
    boss = BossModel(name="The Lord of the Lice", hp=50000)

    await repository.upsert(boss)

    # Verifica que o slug foi gerado corretamente
    slug = boss.get_slug()
    assert "the-lord-of-the-lice" in slug.lower()

    saved_boss = await repository.find_by_slug(slug)
    assert saved_boss is not None


@pytest.mark.asyncio
async def test_index_created(test_database: AsyncIOMotorDatabase):
    """Testa que o índice único em slug foi criado."""
    # Lista os índices da coleção
    indexes = await test_database.bosses.list_indexes().to_list(length=10)

    index_names = [idx["name"] for idx in indexes]

    # Verifica que o índice slug existe e é único
    slug_index = next((idx for idx in indexes if idx.get("key", {}).get("slug")), None)
    assert slug_index is not None
    assert slug_index.get("unique") is True

