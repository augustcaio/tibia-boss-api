<div align="center">
  <img src="docs/assets/tibia-logo.gif" alt="Tibia Logo" width="200"/>
  
  # Tibia Boss API
  
  API para scraping e disponibilização de dados de Bosses do Tibia Wiki.
</div>

## Sobre o Projeto

Esta API extrai dados de bosses do [TibiaWiki](https://tibia.fandom.com) e os disponibiliza através de endpoints REST estruturados.

## Stack Tecnológica

- **Python 3.10+** (Alinhado com OpenSSL para produção)
- **FastAPI** - Framework web assíncrono
- **MongoDB + Motor** - Banco de dados NoSQL com driver assíncrono
- **SlowAPI** - Rate Limiting para proteção de endpoints
- **Pydantic v2** - Validação de dados
- **httpx** - Cliente HTTP assíncrono
- **mwparserfromhell** - Parser de Wikitext

## Quick Start

### Pré-requisitos

- Python 3.10+
- Docker e Docker Compose

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
- **POST** `/api/v1/admin/sync` - Disparar sincronização manual (requer Token)

### Metadados de Resposta
As respostas paginadas incluem o campo `latest_update` (ISO 8601), indicando quando os dados foram sincronizados pela última vez com a TibiaWiki.

## Automação

O projeto possui um sistema de atualização automática:
- **Ciclo interno:** O scraper roda a cada 12 horas (10:00 e 22:00 UTC).
- **Resiliência:** Utiliza um sistema de *Distributed Lock* (Mongo Mutex) para garantir que apenas uma instância do scraper rode por vez, mesmo em ambientes escalados.
- **Modo Sleep:** Em ambientes como Render Free, recomenda-se configurar um gatilho externo (ex: cron-job.org) apontando para o endpoint `/admin/sync`.

## Auditoria e Integridade

Para garantir que a API está em sincronia com a TibiaWiki, utilize o script de auditoria:

```bash
python audit_bosses.py
```

O script compara a lista de artigos da categoria Bosses na Wiki com o banco de dados local e reporta discrepâncias.

- **Swagger UI:** `http://localhost:8000/docs`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

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

## Troubleshooting Production

### Diagnóstico de DNS/TLS com `debug_network.py`

Em ambiente de produção (ex.: Render), rode dentro do container:

```bash
python debug_network.py
```

O script vai:

- Resolver o host do MongoDB (a partir de `MONGODB_URL`/`MONGO_URL` ou `--host`)  
- Testar:
  - **DNS**: `socket.gethostbyname(host)`  
  - **TLS**: handshake com `ssl` usando `certifi.where()`  

Saída esperada:

- **DNS falhando** → mensagem do tipo `❌ DNS FALHOU` (problema de resolução / NXDOMAIN).  
- **TLS falhando** → `✅ DNS OK` mas `❌ TLS FALHOU` (problema de certificado / cadeia / SNI).  

### Connection String Legacy (`mongodb://` sem SRV)

Se o cluster estiver no MongoDB Atlas e houver problemas com `mongodb+srv://`, use a string **legacy**:

1. No Atlas, vá em **Connect → Drivers → Python 3.4+**.  
2. Copie a connection string no formato `mongodb://...` (sem `+srv`, com os hosts explícitos).  
3. Atualize a variável de ambiente no provider (ex.: Render):
   - `MONGO_URL` **ou** `MONGODB_URL` com a nova string `mongodb://...`.  

O código da aplicação já está preparado para:

- Usar TLS com `certifi` para URLs Atlas (`mongodb+srv://` ou contendo `mongodb.net`).  
- Não forçar TLS para Mongo local (ex.: `mongodb://mongo:27017/tibia_bosses`).  

### Modo Degradado e Respostas 503

Para evitar que a API caia quando o MongoDB estiver indisponível:

- No startup, se o banco não conectar, a API entra em **modo degradado** (soft startup):
  - A rota `/` continua respondendo **200**.  
  - Rotas que dependem de DB (ex.: `/api/v1/bosses`) retornam **503 Service Unavailable**.  
- A variável `ALLOW_START_WITHOUT_DB` controla se o processo pode subir mesmo sem banco:
  - Vaziu/`1`/`true` → sobe em modo degradado (recomendado para produção).  
  - Outro valor → falha duro no startup (útil para ambientes de debug).  

## Licença

MIT
