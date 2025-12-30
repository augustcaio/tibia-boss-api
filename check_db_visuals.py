import os

from dotenv import load_dotenv
from pymongo import MongoClient

# Carrega variáveis de ambiente
load_dotenv()


def check_visuals():
    # Pega a URL do ambiente (mesma lógica do app/core/config.py)
    mongodb_url = (
        os.environ.get("MONGODB_URL")
        or os.environ.get("MONGO_URL")
        or "mongodb://127.0.0.1:27017"
    )
    database_name = "tibia_bosses"

    print(f"🔍 Conectando ao banco para verificação...")

    try:
        client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
        db = client[database_name]
        collection = db["bosses"]

        # Conta total de bosses
        total = collection.count_documents({})
        print(f"📊 Total de bosses no banco: {total}")

        # Busca 5 bosses aleatórios que tenham o campo visuals
        sample = collection.find({"visuals": {"$exists": True}}).limit(10)

        print("\n📝 Amostra de Bosses e seus Visuals:")
        print("-" * 60)
        found = False
        for boss in sample:
            found = True
            name = boss.get("name", "N/A")
            visuals = boss.get("visuals")
            print(f"Boss: {name}")
            print(f"Visuals: {visuals}")
            print("-" * 30)

        if not found:
            print("❌ Nenhum boss com o campo 'visuals' encontrado!")

        # Verifica se existem bosses com visuals null ou campos internos null
        null_visuals = collection.count_documents({"visuals": None})
        null_gif_url = collection.count_documents({"visuals.gif_url": None})
        placeholder_count = collection.count_documents(
            {"visuals.gif_url": {"$regex": "placeholder"}})

        print(f"\n📈 Estatísticas:")
        print(f"- Bosses com visuals nulo: {null_visuals}")
        print(f"- Bosses com gif_url nulo: {null_gif_url}")
        print(f"- Bosses usando placeholder: {placeholder_count}")

    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")


if __name__ == "__main__":
    check_visuals()
