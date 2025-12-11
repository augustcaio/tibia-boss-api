# 🎮 Tibia Boss API

API para scraping e disponibilização de dados de Bosses do Tibia Wiki.

## 📋 Sobre o Projeto

Esta API extrai dados de bosses do [TibiaWiki](https://tibia.fandom.com) e os disponibiliza através de endpoints REST estruturados.

## 🛠️ Stack Tecnológica

- **Python 3.11+**
- **FastAPI** - Framework web assíncrono
- **MongoDB + Motor** - Banco de dados NoSQL com driver assíncrono
- **Pydantic v2** - Validação de dados
- **httpx** - Cliente HTTP assíncrono
- **mwparserfromhell** - Parser de Wikitext

## 🚀 Quick Start

### Pré-requisitos

- Python 3.11+
- Poetry
- Docker e Docker Compose

### Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd tibia-boss-api

# Instale as dependências
poetry install

# Suba o MongoDB
docker-compose up -d

# Ative o ambiente virtual
poetry shell

# Execute a API
uvicorn app.main:app --reload
```

### Configuração de Pre-commit

```bash
# Instale os hooks
poetry run pre-commit install

# Rode manualmente (opcional)
poetry run pre-commit run --all-files
```

## 📁 Estrutura do Projeto

```
tibia-boss-api/
├── app/
│   ├── core/           # Configs, Environment vars, Logging
│   ├── db/             # Conexão MongoDB (Motor)
│   ├── models/         # Pydantic Schemas + Mongo Models
│   ├── routers/        # Endpoints API (v1)
│   ├── services/       # Lógica de Negócio (Scraper, Parser)
│   └── utils/          # Helpers
├── tests/              # Testes (pytest)
├── docker-compose.yml  # MongoDB container
└── pyproject.toml      # Dependências (Poetry)
```

## 🧪 Testes

```bash
# Rodar todos os testes
poetry run pytest

# Com cobertura
poetry run pytest --cov=app
```

## 📜 Licença

MIT
