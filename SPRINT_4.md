## 🚀 Sprint 4: Hardening & Deployment (Produção)

**Origem:** Tech Lead  
**Objetivo:** Entregar uma aplicação containerizada, segura e com automação resiliente a concorrência.

---

## 🎫 Task 4.1: Dockerização "Production Grade"

| Campo          | Valor             |
| -------------- | ----------------- |
| **Prioridade** | 🔴 Alta (Blocker) |
| **Estimativa** | 5 Story Points    |
| **Status**     | ⏳ Planejada      |

### Descrição

Criar a infraestrutura de container final. O Dockerfile deve ser otimizado para segurança e tamanho.

### Detalhes Técnicos

- [ ] **Multi-Stage Build**
  - [ ] `builder`: Instalar `poetry`, `gcc`, `libssl-dev`. Exportar `requirements.txt`.
  - [ ] `final`: Usar base `python:3.11-slim`. Instalar dependências via `pip` (sem Poetry) para economizar espaço.
- [ ] **Security**
  - [ ] Criar usuário `appuser` (UID 1000). O container não pode rodar como root.
  - [ ] `CMD`: Usar `sh -c` para garantir que variáveis de ambiente sejam expandidas.
- [ ] **Docker Compose**
  - [ ] Serviço `api`: Depende de `mongo`. Variáveis carregadas de `.env`.
  - [ ] Serviço `mongo`: Volume persistente em `./data/db`.
- [ ] **Ignore**
  - [ ] Configurar `.dockerignore` (ignorar `.git`, `__pycache__`, `venv`, `tests`).

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
| **Status**     | ⏳ Planejada                 |

### Descrição

Implementar a atualização automática semanal e o trigger manual. Crucial: Implementar um mecanismo de trava (Lock) no banco para impedir que múltiplos workers rodem o scraper simultaneamente.

### Detalhes Técnicos

- [ ] **Lock System**

  - [ ] Criar collection `system_jobs`.
  - [ ] Documento de controle base:

    ```json
    {
      "_id": "scraper_lock",
      "status": "idle",
      "last_run": "...",
      "locked_at": null
    }
    ```

  - [ ] Antes de rodar, o código deve tentar fazer um `find_one_and_update`:
    - **Query:** `{ "_id": "scraper_lock", "status": "idle" }`
    - **Update:** `{ "$set": { "status": "running", "locked_at": now } }`
  - [ ] Se o update falhar (retornar `null`/`None`), significa que já tem alguém rodando → abortar silenciosamente.
  - [ ] No `finally` (sucesso ou erro), dar release:
    - **Update:** `{ "$set": { "status": "idle" } }`.

- [ ] **APScheduler**
  - [ ] Configurar `AsyncIOScheduler` no lifespan do FastAPI.
  - [ ] Cron: `day_of_week='tue'`, `hour=10`, `timezone='UTC'`.
- [ ] **Endpoint Admin**
  - [ ] `POST /api/v1/admin/sync`.
  - [ ] Header: `X-Admin-Token` (comparar com `settings.ADMIN_SECRET`).
  - [ ] Chamar a mesma função do Scheduler (que respeita o Lock).
  - [ ] Usar `BackgroundTasks` para não travar o request.

### Definition of Done (DoD)

- [ ] Se o endpoint `/api/v1/admin/sync` for disparado 5 vezes seguidas rapidamente, o scraper roda apenas 1 vez (logs confirmam `"Lock acquired"` vs `"Job already running"`).
- [ ] Trigger agendado via APScheduler funcionando.

---

## 🎫 Task 4.3: Segurança e Rate Limiting

| Campo          | Valor          |
| -------------- | -------------- |
| **Prioridade** | 🟡 Média       |
| **Estimativa** | 3 Story Points |
| **Status**     | ⏳ Planejada   |

### Descrição

Proteger a API contra abusos e configurar headers de proxy corretamente.

### Detalhes Técnicos

- [ ] **Lib:** `slowapi`.
- [ ] **Configuração base:**
  - [ ] `limiter = Limiter(key_func=get_remote_address)`.
  - [ ] `app.state.limiter = limiter`.
  - [ ] Adicionar `CheckHostMiddleware` ou `TrustedHostMiddleware` se formos expor diretamente.
- [ ] **Regras de Rate Limiting:**
  - [ ] `@limiter.limit("60/minute")` nos endpoints `GET /bosses`.
  - [ ] `@limiter.limit("20/minute")` na busca `GET /search`.
  - [ ] `@limiter.limit("5/hour")` no `POST /admin/sync`.
- [ ] **Proxy Fix:**
  - [ ] Configurar `uvicorn` com `--proxy-headers` e `--forwarded-allow-ips='*'` no comando do Docker, senão o `get_remote_address` vai pegar sempre o IP do Docker (`172.x.x.x`) e bloquear todo mundo junto.

### Definition of Done (DoD)

- [ ] Teste de carga local bloqueia após o limite (HTTP 429).
- [ ] Headers `X-RateLimit-*` presentes na resposta.

---

## 🎫 Task 4.4: Pipeline de CI (GitHub Actions)

| Campo          | Valor          |
| -------------- | -------------- |
| **Prioridade** | 🟡 Média       |
| **Estimativa** | 3 Story Points |
| **Status**     | ⏳ Planejada   |

### Descrição

Garantir a integridade do código antes do merge.

### Detalhes Técnicos

- [ ] **Arquivo:** `.github/workflows/ci.yml`.
- [ ] **Jobs:**
  - [ ] **Build & Lint:**
    - [ ] Rodar com Python 3.11.
    - [ ] Cache de Poetry.
    - [ ] Rodar `ruff` (mais rápido que `black`/`isort`) ou `black --check`.
  - [ ] **Test:**
    - [ ] Service: `mongo:6.0`.
    - [ ] Env: `MONGO_URL=mongodb://localhost:27017`.
    - [ ] Comando: `pytest -v`.
- [ ] **Trigger:**
  - [ ] Push na `main` e em PRs.

### Definition of Done (DoD)

- [ ] O check verde aparece no GitHub ao abrir um PR.
- [ ] O pipeline falha se houver erro de sintaxe ou teste quebrado.

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
