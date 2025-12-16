

## Sobre o Projeto

Esta API extrai dados de bosses do [TibiaWiki](https://tibia.fandom.com) e os disponibiliza através de endpoints REST estruturados.

## Stack Tecnológica

- **Python 3.11+**
- **FastAPI** - Framework web assíncrono
- **MongoDB + Motor** - Banco de dados NoSQL com driver assíncrono
- **Pydantic v2** - Validação de dados
- **httpx** - Cliente HTTP assíncrono
- **mwparserfromhell** - Parser de Wikitext

## Quick Start

### Pré-requisitos

- Python 3.11+
- Docker e Docker Compose (ou Docker Compose V2)
- Poetry (opcional) ou pip

### Instalação

#### Opção 1: Usando Poetry (Recomendado)

```bash
# Clone o repositório
git clone <repo-url>
cd tibia-boss-api

# Instale as dependências
poetry install

# Suba o MongoDB
docker compose up -d

# Ative o ambiente virtual
poetry shell

# Execute a API
uvicorn app.main:app --reload
```

#### Opção 2: Usando pip

```bash
# Clone o repositório
git clone <repo-url>
cd tibia-boss-api

# Crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements-dev.txt

# Suba o MongoDB
docker compose up -d

# Execute a API
uvicorn app.main:app --reload
```

**Nota:** Use `docker compose` (sem hífen) para Docker Compose V2, ou `docker-compose` (com hífen) para versões antigas.

### Configuração de Pre-commit

```bash
# Instale os hooks
poetry run pre-commit install

# Rode manualmente (opcional)
poetry run pre-commit run --all-files
```

## Estrutura do Projeto

```
tibia-boss-api/
├── app/
│   ├── api/            # Endpoints API (v1)
│   │   └── v1/
│   │       └── routers/ # Rotas da API
│   ├── core/           # Configs, Environment vars, Database
│   ├── db/             # Conexão MongoDB (Motor) + Repository
│   ├── models/         # Pydantic Schemas + Mongo Models
│   ├── schemas/        # Schemas de resposta da API
│   ├── services/       # Lógica de Negócio (Scraper, Parser)
│   └── utils/          # Helpers
├── tests/              # Testes (pytest)
├── scripts/            # Scripts de teste e utilidades
├── logs/               # Logs de erro (Dead Letter)
├── docker-compose.yml  # MongoDB container
├── pyproject.toml      # Dependências (Poetry)
├── requirements.txt   # Dependências de produção (pip)
└── requirements-dev.txt # Dependências de desenvolvimento (pip)
```

## Rotas da API

A API está disponível em `http://localhost:8000` após iniciar o servidor.

### Endpoints Disponíveis

- **GET** `/` - Endpoint raiz
- **GET** `/api/v1/health` - Health check (API + DB)
- **GET** `/api/v1/bosses` - Listar bosses (paginação)
- **GET** `/api/v1/bosses/{slug}` - Detalhes de um boss
- **GET** `/api/v1/bosses/search` - Buscar bosses por nome

### Documentação Interativa

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

Para mais detalhes, consulte o arquivo [ROUTES.md](ROUTES.md).

## Testes

```bash
# Rodar todos os testes
poetry run pytest
# ou
pytest

# Com cobertura
poetry run pytest --cov=app
# ou
pytest --cov=app
```

## Dependências

O projeto pode ser instalado usando:

- **Poetry:** `poetry install` (recomendado)
- **pip:** `pip install -r requirements-dev.txt`

Arquivos disponíveis:

- `requirements.txt` - Dependências de produção
- `requirements-dev.txt` - Dependências de desenvolvimento (inclui produção)

## Executando o Projeto

```bash
# 1. Subir o MongoDB
docker compose up -d

# 2. Ativar ambiente virtual
source .venv/bin/activate  # ou poetry shell

# 3. Executar a API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Acessar documentação
# http://localhost:8000/docs
```

## Licença

MIT
