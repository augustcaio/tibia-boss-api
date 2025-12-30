<div align="center">
  <img src="docs/assets/tibia-logo.gif" alt="Tibia Logo" width="200"/>
  
  # Tibia Boss API
  
  API for scraping and serving Tibia Boss data from TibiaWiki.
</div>

## About the Project

This API scrapes boss data from [TibiaWiki](https://tibia.fandom.com) and provides it via structured REST endpoints. The system features automatic updates and fault resilience.

## Tech Stack

- **Python 3.10+** (FastAPI)
- **MongoDB + Motor** (Async NoSQL Database)
- **SlowAPI** (Rate Limiting)
- **Pydantic v2** (Data Validation)
- **httpx** (Async HTTP Client)

## Quick Start (Docker)

The easiest way to run the project is using Docker Compose.

```bash
# Clone the repository
git clone https://github.com/augustcaio/tibia-boss-api
cd tibia-boss-api

# Start the application and database
docker compose up -d

# The API will be available at:
# http://localhost:8000
```

> **Note:** If you prefer running manually with Poetry, ensure MongoDB is running and environment variables are configured.

## API Routes

Interactive documentation available at: `http://localhost:8000/docs`

- **GET** `/` - API Status
- **GET** `/api/v1/bosses` - List all bosses (paginated)
- **GET** `/api/v1/bosses/search?name=...` - Search boss by name
- **GET** `/api/v1/bosses/{slug}` - Specific boss details

## License

MIT
