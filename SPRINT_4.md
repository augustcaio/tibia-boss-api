## 🚀 Sprint 4: Hardening & Deployment (Produção)

**Origem:** Tech Lead  
**Objetivo:** Entregar uma aplicação containerizada, segura e com automação resiliente a concorrência.

---

## 🎫 Task 4.1: Dockerização "Production Grade"

| Campo          | Valor             |
| -------------- | ----------------- |
| **Prioridade** | 🔴 Alta (Blocker) |
| **Estimativa** | 5 Story Points    |
| **Status**     | 🚧 Em andamento   |

### Descrição

Criar a infraestrutura de container final. O Dockerfile deve ser otimizado para segurança e tamanho.

### Detalhes Técnicos

- [x] **Multi-Stage Build**
  - [x] `builder`: Instalar `poetry`, `gcc`, `libssl-dev`. Exportar `requirements.txt`.
  - [x] `final`: Usar base `python:3.11-slim`. Instalar dependências via `pip` (sem Poetry) para economizar espaço.
- [x] **Security**
  - [x] Criar usuário `appuser` (UID 1000). O container não pode rodar como root.
  - [x] `CMD`: Usar `sh -c` para garantir que variáveis de ambiente sejam expandidas.
- [x] **Docker Compose**
  - [x] Serviço `api`: Depende de `mongo`. Variáveis carregadas de `.env` (via variáveis de ambiente do Docker Compose).
  - [x] Serviço `mongo`: Volume persistente em `./data/db`.
- [x] **Ignore**
  - [x] Configurar `.dockerignore` (ignorar `.git`, `__pycache__`, `venv`, `tests`).

### Definition of Done (DoD)

- [ ] Imagem final < 500MB.
- [ ] `docker exec -it <container> whoami` retorna `appuser`.
- [ ] Aplicação conecta no Mongo via rede interna do Docker (`mongo:27017`).

---

## 🎫 Task 4.2: Scheduler com "Distributed Lock" (Mongo Mutex)

| Campo          | Valor                        |
| -------------- | ---------------------------- |
| **Prioridade** | 🔴 Alta (Risco Arquitetural) |
| **Estimativa** | 8 Story Points               |
| **Status**     | ✅ Concluída                 |

### Descrição

Implementar a atualização automática semanal e o trigger manual. Crucial: Implementar um mecanismo de trava (Lock) no banco para impedir que múltiplos workers rodem o scraper simultaneamente.

### Detalhes Técnicos

- [x] **Lock System**

  - [x] Criar collection `system_jobs`.
  - [x] Documento de controle base:

    ```json
    {
      "_id": "scraper_lock",
      "status": "idle",
      "last_run": "...",
      "locked_at": null
    }
    ```

  - [x] Antes de rodar, o código deve tentar fazer um `find_one_and_update`:
    - **Query:** `{ "_id": "scraper_lock", "status": "idle" }`
    - **Update:** `{ "$set": { "status": "running", "locked_at": now } }`
  - [x] Se o update falhar (retornar `null`/`None`), significa que já tem alguém rodando → abortar silenciosamente.
  - [x] No `finally` (sucesso ou erro), dar release:
    - **Update:** `{ "$set": { "status": "idle" } }`.

- [x] **APScheduler**
  - [x] Configurar `AsyncIOScheduler` no lifespan do FastAPI.
  - [x] Cron: `day_of_week='tue'`, `hour=10`, `timezone='UTC'`.
- [x] **Endpoint Admin**
  - [x] `POST /api/v1/admin/sync`.
  - [x] Header: `X-Admin-Token` (comparar com `settings.ADMIN_SECRET`).
  - [x] Chamar a mesma função do Scheduler (que respeita o Lock).
  - [x] Usar `BackgroundTasks` para não travar o request.

### Definition of Done (DoD)

- [x] Se o endpoint `/api/v1/admin/sync` for disparado 5 vezes seguidas rapidamente, o scraper roda apenas 1 vez (logs confirmam `"Lock acquired"` vs `"Job already running"`).
- [x] Trigger agendado via APScheduler funcionando.

---

## 🎫 Task 4.3: Segurança e Rate Limiting

| Campo          | Valor          |
| -------------- | -------------- |
| **Prioridade** | 🟡 Média       |
| **Estimativa** | 3 Story Points |
| **Status**     | ✅ Concluída   |

### Descrição

Proteger a API contra abusos e configurar headers de proxy corretamente.

### Detalhes Técnicos

- [x] **Lib:** `slowapi`.
- [x] **Configuração base:**
  - [x] `limiter = Limiter(key_func=get_remote_address)`.
  - [x] `app.state.limiter = limiter`.
  - [x] Adicionar `CheckHostMiddleware` ou `TrustedHostMiddleware` se formos expor diretamente.
- [x] **Regras de Rate Limiting:**
  - [x] `@limiter.limit("60/minute")` nos endpoints `GET /bosses`.
  - [x] `@limiter.limit("20/minute")` na busca `GET /search`.
  - [x] `@limiter.limit("5/hour")` no `POST /admin/sync`.
- [x] **Proxy Fix:**
  - [x] Configurar `uvicorn` com `--proxy-headers` e `--forwarded-allow-ips='*'` no comando do Docker, senão o `get_remote_address` vai pegar sempre o IP do Docker (`172.x.x.x`) e bloquear todo mundo junto.

### Definition of Done (DoD)

- [x] Teste de carga local bloqueia após o limite (HTTP 429).
- [x] Headers `X-RateLimit-*` presentes na resposta.

---

## 🎫 Task 4.4: Pipeline de CI (GitHub Actions)

| Campo          | Valor          |
| -------------- | -------------- |
| **Prioridade** | 🟡 Média       |
| **Estimativa** | 3 Story Points |
| **Status**     | ✅ Concluída   |

### Descrição

Garantir a integridade do código antes do merge.

### Detalhes Técnicos

- [x] **Arquivo:** `.github/workflows/ci.yml`.
- [x] **Jobs:**
  - [x] **Build & Lint:**
    - [x] Rodar com Python 3.11.
    - [x] Cache de Poetry.
    - [x] Rodar `black --check`.
  - [x] **Test:**
    - [x] Service: `mongo:6.0`.
    - [x] Env: `MONGO_URL=mongodb://localhost:27017`.
    - [x] Comando: `pytest -v`.
- [x] **Trigger:**
  - [x] Push na `main` e em PRs.

### Definition of Done (DoD)

- [x] O check verde aparece no GitHub ao abrir um PR (simulado localmente via configuração do workflow).
- [x] O pipeline falha se houver erro de sintaxe ou teste quebrado (garantido por black --check e pytest -v).

---

## 👨‍💻 Comentário do Tech Lead

"Time, aprovei o plano. A adição do Mongo Mutex na Task 4.2 é a diferença entre um projeto de estudante e um projeto de engenharia. Isso evita que, se escalarmos a API no futuro, tenhamos problemas de dados duplicados ou banimento do Wiki.

Sobre a Task 4.1: Lembrem-se de não commitar o arquivo `.env`. Usem um `.env.example` no repositório.

Podem iniciar a última Sprint! Quero ver esse deploy na sexta-feira. 🚀"

---

## 📝 Resumo da Sprint 4 (Planejamento)

- **Total de Tarefas:** 4
- **Story Points Totais:** 19 (5 + 8 + 3 + 3)
- **Status Geral:** 🔄 Em planejamento / execução.
