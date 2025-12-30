# Changelog

## [1.0.0] - 2025-12-30

### 🎉 initial Release

A primeira versão estável da Tibia Boss API está no ar! Esta release traz uma solução robusta para rastreamento e consulta de bosses do Tibia.

### ✨ Funcionalidades

- **Scraping Automático Resiliente**:
    - Sistema de atualização a cada 12 horas.
    - Mecanismo de *Distributed Lock* com MongoDB para garantir unicidade da execução.
- **API RESTful Completa**:
    - `GET /bosses`: Listagem paginada.
    - `GET /bosses/{slug}`: Detalhes ricos de bosses.
    - `GET /bosses/search`: Busca por nome parcial.
- **Gestão Inteligente de Imagens**:
    - Resolução automática de GIFs do TibiaWiki via API de Mídia.
    - Fallback para placeholder em caso de falhas.
- **Performance e Segurança**:
    - Rate Limiting configurado.
    - Validação estrita de dados com Pydantic v2.
    - Modo degradado (API funciona parcialmente mesmo sem DB).
- **Tooling Developer-Friendly**:
    - Pipeline de CI robusto separado em Quality e Tests.
    - Scripts de audit (`audit_bosses.py`) e debug (`debug_network.py`).
