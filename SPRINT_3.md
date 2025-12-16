# 🚀 Sprint 3: API RESTful (Exposição de Dados)

**Objetivo:** Transformar os dados do MongoDB em uma API pública, documentada e performática usando FastAPI.

---

## 🎫 Task 3.1: API Skeleton & Injeção de Dependência

| Campo          | Valor             |
| -------------- | ----------------- |
| **Prioridade** | 🔴 Alta (Blocker) |
| **Estimativa** | 3 Story Points    |
| **Status**     | ✅ Concluída      |

### Descrição

Estruturar o servidor FastAPI para deixar de ser um script e virar uma aplicação web modular. Implementar o padrão de Injeção de Dependência para o banco de dados.

### Detalhes Técnicos

- [x] **Refatoração:** Mover a lógica de conexão do banco para `app/core/database.py`
- [x] **Dependency Injection:** Criar uma função `get_database()` que será usada com `Depends()` nas rotas. Isso é vital para podermos mockar o banco nos testes depois
- [x] **Rotas:** Criar arquivo `app/api/v1/routers/bosses.py` e usar `APIRouter`
- [x] **Main:** O `app/main.py` deve apenas instanciar o FastAPI, configurar CORS e incluir os routers

### Definition of Done (DoD)

- [x] Endpoint `GET /health` retorna `{"status": "ok", "db": "connected"}`
- [x] Swagger UI carrega em `http://localhost:8000/docs`
- [x] O código respeita a separação: Rotas chamam Controllers/Services, que chamam Repositories

### 📝 Nota de Implementação

**Implementação realizada:**

- Criado `app/core/database.py` com a lógica de conexão MongoDB e função `get_database()` para Dependency Injection
- Criada estrutura de rotas em `app/api/v1/routers/` com:
  - `bosses.py`: Router para endpoints de bosses (estrutura criada, endpoints serão adicionados nas próximas tasks)
  - `health.py`: Router para health check com endpoint `GET /api/v1/health`
- Atualizado `app/main.py` para:
  - Usar `app.core.database` em vez de `app.db.connection`
  - Configurar CORS middleware
  - Incluir routers com prefixo `/api/v1`
- Mantida compatibilidade: `app/db/connection.py` agora re-exporta de `app/core/database.py` para não quebrar scripts existentes
- Endpoint `/api/v1/health` implementado usando `Depends(get_database)` para Dependency Injection

---

## 🎫 Task 3.2: Endpoint de Listagem com Paginação (Cursor/Offset)

| Campo          | Valor          |
| -------------- | -------------- |
| **Prioridade** | 🔴 Alta        |
| **Estimativa** | 5 Story Points |
| **Status**     | ✅ Concluída   |

### Descrição

Criar `GET /api/v1/bosses`. Implementar paginação robusta para não sobrecarregar o cliente nem o servidor.

### Detalhes Técnicos

- [x] **Query Params:** Aceitar `page` (default 1) e `limit` (default 20, max 100)
- [x] **Repository:** Método `list_bosses(skip: int, limit: int)`
- [x] **Mongo Projection:** Crucial. Não retornar o campo `raw_wikitext` ou campos de metadados internos nessa lista. Retornar apenas: `name`, `slug`, `visuals`, `hp`
- [x] **Schema de Resposta:** Usar Pydantic Generics para padronizar a resposta (ver Nota Técnica abaixo)

### Definition of Done (DoD)

- [x] Request `GET /api/v1/bosses?limit=5` retorna exatamente 5 itens
- [x] Response body inclui metadados: `total`, `page`, `pages`, `size`
- [x] Teste de integração valida que o `skip` está funcionando (página 2 traz itens diferentes da página 1)

### 📝 Nota de Implementação

**Implementação realizada:**

- Criado `app/schemas/response.py` com `PaginatedResponse[T]` usando Pydantic Generics
- Criado `app/schemas/boss.py` com `BossShortSchema` para listagem (sem campos pesados)
- Adicionado método `list_bosses(skip, limit)` no `BossRepository` com projection MongoDB
- Implementado endpoint `GET /api/v1/bosses` com:
  - Query params: `page` (default 1, ge=1) e `limit` (default 20, ge=1, le=100)
  - Validação automática via FastAPI Query
  - Cálculo de `skip` baseado na página
  - Metadados de paginação: `total`, `page`, `size`, `pages`
- Criados testes em `tests/test_bosses_endpoint.py` cobrindo:
  - Paginação padrão
  - Limit customizado
  - Validação de skip (página 2 diferente de página 1)
  - Metadados corretos
  - Projection não retorna campos pesados
  - Validação de limites máximos

### 👨‍💻 Nota Técnica do Tech Lead

Time, para a paginação, não vamos repetir código. Usem Generics do Pydantic. Criem um arquivo `app/schemas/response.py`:

```python
from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
```

E na rota, usem assim:

```python
@router.get("/", response_model=PaginatedResponse[BossShortSchema])
async def list_bosses(...):
    # lógica...
```

Isso garante que o Swagger entenda a tipagem e o Frontend receba sempre o mesmo envelope de dados.

---

## 🎫 Task 3.3: Endpoint de Detalhes (Read by Slug)

| Campo          | Valor          |
| -------------- | -------------- |
| **Prioridade** | 🔴 Alta        |
| **Estimativa** | 3 Story Points |
| **Status**     | ✅ Concluída   |

### Descrição

Criar `GET /api/v1/bosses/{slug}` para exibir a ficha completa do Boss.

### Detalhes Técnicos

- [x] **Busca:** Usar o campo `slug` (indexado na Sprint 2) e não o `_id` do Mongo (URLs com ObjectId são feias e expõem implementação)
- [x] **Error Handling:** Se o retorno do banco for `None`, lançar `HTTPException(status_code=404, detail="Boss not found")`
- [x] **Model:** Retornar o modelo completo (`BossModel`), incluindo todos os campos

### Definition of Done (DoD)

- [x] Busca por `/api/v1/bosses/morgaroth` retorna status 200 e JSON completo
- [x] Busca por `/api/v1/bosses/batatinha-frita` retorna status 404 e JSON de erro padrão

### 📝 Nota de Implementação

**Implementação realizada seguindo padrão MCP:**

- Endpoint `GET /api/v1/bosses/{slug}` implementado
- Usa `slug` como path parameter
- Retorna `BossModel` completo com todos os campos
- Tratamento de erro 404 com `HTTPException`
- Documentação Swagger completa com `summary`, `description` e `responses`

---

## 🎫 Task 3.4: Motor de Busca Simples (Regex Search)

| Campo          | Valor          |
| -------------- | -------------- |
| **Prioridade** | 🟡 Média       |
| **Estimativa** | 5 Story Points |
| **Status**     | ✅ Concluída   |

### Descrição

Permitir que o usuário encontre bosses digitando partes do nome.

### Detalhes Técnicos

- [x] **Endpoint:** `GET /api/v1/bosses/search?q=ghaz`
- [x] **Query Mongo:** Usar filtro `$regex` no campo `name`
- [x] **Query:** `{"name": {"$regex": query_string, "$options": "i"}}` (Case insensitive)
- [x] **Sanitização:** Escapar caracteres especiais da string de busca para evitar ReDoS (Regular Expression Denial of Service) ou injeção de regex maliciosa. Usar `re.escape()`

### Definition of Done (DoD)

- [x] Busca por `"rat"` retorna bosses com "rat" no nome (case insensitive)
- [x] Busca vazia retorna erro 400 com mensagem apropriada

### 📝 Nota de Implementação

**Implementação realizada seguindo padrão MCP:**

- Endpoint `GET /api/v1/bosses/search` implementado
- Métodos `search_by_name()` e `count_by_search()` adicionados ao `BossRepository`
- Query sanitizada com `re.escape()` para evitar ReDoS
- Busca case insensitive usando `$options: "i"`
- Validação de query vazia retorna HTTP 400
- Retorna resposta paginada usando `PaginatedResponse[BossShortSchema]`
- Documentação Swagger completa

---

## 🎫 Task 3.5: Documentação OpenAPI (Swagger Polish)

| Campo          | Valor                        |
| -------------- | ---------------------------- |
| **Prioridade** | 🟢 Baixa (Qualidade de Vida) |
| **Estimativa** | 2 Story Points               |
| **Status**     | ✅ Concluída                 |

### Descrição

A documentação automática do FastAPI é ótima, mas precisa de refinamento manual para ser profissional.

### Detalhes Técnicos

- [x] **Metadata:** Adicionar `title`, `description`, `version` e `contact` no construtor do FastAPI
- [x] **Models:** Adicionar `ConfigDict(json_schema_extra=...)` nos Pydantic Models com exemplos reais de Bosses. Isso faz o Swagger mostrar um JSON preenchido e não "string"
- [x] **Response Codes:** Documentar explicitamente os erros (404, 422, 500) nos decorators das rotas:
  ```python
  @router.get(..., responses={404: {"description": "Not found"}})
  ```

### Definition of Done (DoD)

- [x] Acessar `/docs` e ver exemplos úteis (não string, 0) nos schemas de Request/Response
- [x] Todas as rotas possuem descrição (`summary`) clara

### 📝 Nota de Implementação

**Implementação realizada seguindo padrão MCP:**

- Metadata completa no FastAPI:
  - `title`: "Tibia Boss API"
  - `description`: Descrição detalhada com funcionalidades e fonte de dados
  - `version`: "0.1.0"
  - `contact`: Informações de contato do time
- Exemplos adicionados nos Pydantic Models:
  - `BossModel`: Exemplo completo com Morgaroth (hp, exp, walks_through, immunities, visuals)
  - `BossVisuals`: Exemplo com URL e filename
  - `BossShortSchema`: Já tinha exemplo, mantido
  - `PaginatedResponse`: Exemplo completo com estrutura paginada
- Códigos de resposta documentados em todas as rotas:
  - `GET /api/v1/bosses`: 200, 422, 500
  - `GET /api/v1/bosses/{slug}`: 200, 404, 422, 500
  - `GET /api/v1/bosses/search`: 200, 400, 422, 500
  - `GET /api/v1/health`: 200, 500
- Todas as rotas possuem `summary` e `description` claras

---

## 📝 Resumo do Sprint 3

**Status Geral:** ✅ Concluído

- **Total de Tarefas:** 5
- **Tarefas Concluídas:** 5
- **Tarefas Pendentes:** 0

### Progresso por Prioridade

- 🔴 **Alta:** 3 tarefas (✅ 3.1, ✅ 3.2, ✅ 3.3)
- 🟡 **Média:** 1 tarefa (✅ 3.4)
- 🟢 **Baixa:** 1 tarefa (✅ 3.5)

---

## 📋 Checklist do Tech Lead (Code Review)

Ao revisar o PR, verificar:

- [ ] **Dependency Injection:** As rotas estão usando `Depends(get_database)` corretamente?
- [ ] **Paginação:** O `PaginatedResponse` está sendo usado de forma consistente?
- [ ] **Projection:** A listagem não está retornando campos desnecessários (`raw_wikitext`)?
- [ ] **Sanitização:** A busca está escapando caracteres especiais com `re.escape()`?
- [ ] **Error Handling:** Todos os endpoints têm tratamento adequado de erros (404, 422, 500)?
- [ ] **Swagger:** A documentação está completa e com exemplos úteis?

---

## 🔗 Links Úteis

- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI APIRouter](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Pydantic Generics](https://docs.pydantic.dev/latest/concepts/models/#generic-models)
- [MongoDB Regex Query](https://www.mongodb.com/docs/manual/reference/operator/query/regex/)
- [FastAPI OpenAPI Customization](https://fastapi.tiangolo.com/advanced/openapi-customization/)

---

**Sprint 3 pronta para o Poker Planning! 🚀**
