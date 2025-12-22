"""Script de teste manual para o repositório MongoDB."""

import asyncio

from app.db.connection import close_database, init_database
from app.db.repository import BossRepository
from app.models.boss import BossModel, BossVisuals


async def main():
    """Testa o repositório manualmente."""
    print("🔌 Conectando ao MongoDB...")
    db = await init_database(
        mongodb_url="mongodb://localhost:27017",
        database_name="tibia_bosses",
    )

    print("✅ Conectado!\n")

    # Verifica índices
    print("📊 Verificando índices...")
    indexes = await db.bosses.list_indexes().to_list(length=10)
    print(f"Índices encontrados: {len(indexes)}")
    for idx in indexes:
        key = idx.get("key", {})
        unique = idx.get("unique", False)
        print(f"  - {idx['name']}: {key} (unique: {unique})")
    print()

    # Cria repositório
    repository = BossRepository(db)

    # Teste 1: Criar boss
    print("🧪 Teste 1: Criar boss...")
    boss1 = BossModel(
        name="Morgaroth",
        hp=77000,
        exp=50000,
        visuals=BossVisuals(gif_url="https://example.com/morgaroth.gif", filename="morgaroth.gif"),
    )
    result = await repository.upsert(boss1)
    print(f"  Resultado: {'✅ Sucesso' if result else '❌ Falhou'}")
    print(f"  Slug gerado: {boss1.get_slug()}\n")

    # Teste 2: Buscar por slug
    print("🧪 Teste 2: Buscar por slug...")
    found = await repository.find_by_slug("morgaroth")
    if found:
        print(f"  ✅ Boss encontrado: {found.name} (HP: {found.hp})")
        if found.visuals:
            print(f"  GIF URL: {found.visuals.gif_url}")
    else:
        print("  ❌ Boss não encontrado")
    print()

    # Teste 3: Idempotência (inserir 2 vezes)
    print("🧪 Teste 3: Testar idempotência (inserir 2 vezes)...")
    boss2 = BossModel(name="Test Boss", hp=10000)
    await repository.upsert(boss2)
    count1 = await repository.count()
    print(f"  Após primeira inserção: {count1} bosses")

    boss2.hp = 15000  # Altera HP
    await repository.upsert(boss2)
    count2 = await repository.count()
    print(f"  Após segunda inserção: {count2} bosses")
    print(f"  {'✅ Idempotência OK' if count1 == count2 == 1 else '❌ Falhou'}\n")

    # Teste 4: Batch upsert
    print("🧪 Teste 4: Batch upsert...")
    bosses = [BossModel(name=f"Boss {i}", hp=10000 + i * 1000) for i in range(5)]
    success = await repository.upsert_batch(bosses)
    total = await repository.count()
    print(f"  Processados: {success}/{len(bosses)}")
    print(f"  Total no banco: {total}\n")

    print("✅ Todos os testes concluídos!")

    # Fecha conexão
    await close_database()


if __name__ == "__main__":
    asyncio.run(main())
