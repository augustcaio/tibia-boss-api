# Changelog

## [1.0.0] - 2025-12-30

### 🚀 Release 1.0.0: Initial Production Release

We are proud to announce the first stable release of **Tibia Boss API**, a specialized high-performance RESTful service for tracking and querying Tibia boss data.

This major release marks the transition from development to a production-ready state, delivering a robust architecture built for resilience, scalability, and ease of integration.

### ✨ Key Features

- **Robust Distributed Scraping**:
    - Automated synchronization engine running on a 12-hour cycle updates data from TibiaWiki.
    - Implements **MongoDB Distributed Locks** to ensure consistency and prevent race conditions in horizontal scaling scenarios.

- **High-Performance REST API**:
    - **`GET /v1/bosses`**: Paginated, filterable list of all bosses.
    - **`GET /v1/bosses/{slug}`**: rich detailed view including hitpoints, loot statistics, and spawn mechanics.
    - **`GET /v1/bosses/search`**: Optimized fuzzy search for quick lookups.

- **Enterprise-Grade Reliability**:
    - **Resilient Image Resolution**: Dynamic resolving of TibiaWiki assets with intelligent fallback handling.
    - **Graceful Degradation**: Architecture designed to maintain read-availability even during partial database outages.
    - **Security & Stability**: Integrated **SlowAPI** for rate limiting and **Pydantic v2** for strict data validation.

- **Developer Experience**:
    - Comprehensive **Swagger/OpenAPI** documentation.
    - Fully containerized with **Docker** for effortless deployment.
    - Production-ready CI pipeline for quality assurance.
