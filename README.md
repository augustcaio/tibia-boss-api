<div align="center">
  <img src="docs/assets/tibia-logo.gif" alt="Tibia Logo" width="200"/>
  
  # Tibia Boss API
  
  API para scraping e disponibilização de dados de Bosses do Tibia Wiki.
</div>

## Sobre o Projeto

Esta API extrai dados de bosses do [TibiaWiki](https://tibia.fandom.com) e os disponibiliza através de endpoints REST estruturados. O sistema conta com atualização automática e resiliência a falhas.

## Stack Tecnológica

- **Python 3.10+** (FastAPI)
- **MongoDB + Motor** (Banco de dados NoSQL assíncrono)
- **SlowAPI** (Rate Limiting)
- **Pydantic v2** (Validação de dados)
- **httpx** (Cliente HTTP assíncrono)

## Quick Start (Docker)

A maneira mais fácil de rodar o projeto é usando Docker Compose.

```bash
# Clone o repositório
git clone https://github.com/augustcaio/tibia-boss-api
cd tibia-boss-api

# Suba a aplicação e o banco de dados
docker compose up -d

# A API estará disponível em:
# http://localhost:8000
```

> **Nota:** Se preferir rodar manualmente com Poetry, certifique-se de ter o MongoDB rodando e as variáveis de ambiente configuradas.

## Rotas da API

Documentação interativa disponível em: `http://localhost:8000/docs`

- **GET** `/` - Status da API
- **GET** `/api/v1/bosses` - Listar todos os bosses (paginado)
- **GET** `/api/v1/bosses/search?name=...` - Buscar boss por nome
- **GET** `/api/v1/bosses/{slug}` - Detalhes específicos de um boss

## Licença

MIT
