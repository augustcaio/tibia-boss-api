# 🏃 Sprint 1: Engenharia de Extração (Core Scraper)

**Objetivo:** Estabelecer a arquitetura do projeto e garantir que conseguimos extrair, limpar e estruturar os dados textuais dos Bosses via API do MediaWiki.

---

## 🎫 Task 1.1: Setup do Projeto e Ambiente de Desenvolvimento

| Campo          | Valor             |
| -------------- | ----------------- |
| **Prioridade** | 🔴 Alta (Blocker) |
| **Estimativa** | 2 Story Points    |
| **Status**     | ✅ Concluída      |

### Descrição

Inicializar o repositório seguindo a Arquitetura em Camadas definida. Configurar gerenciamento de dependências e container do banco de dados.

### Detalhes Técnicos

- [x] Inicializar Poetry (`pyproject.toml`) com Python 3.11+
- [x] Dependências iniciais: `fastapi`, `uvicorn`, `motor`, `odmantic` (ou Pydantic v2 direto), `httpx`, `mwparserfromhell`
- [x] Dev dependencies: `pytest`, `black`, `isort`, `pre-commit`
- [x] Criar estrutura de pastas: `app/core`, `app/services`, `app/models`, `app/utils`
- [x] Criar `docker-compose.yml` apenas com o serviço do MongoDB (imagem `mongo:latest`) expondo a porta 27017

### Definition of Done (DoD)

- [x] `poetry install` roda sem erros
- [x] `docker-compose up -d` sobe o MongoDB e é possível conectar via Compass/Robo3T
- [x] Pre-commit hook configurado (formatação automática)
- [x] Estrutura de pastas commitada no Git

---

## 🎫 Task 1.2: TibiaWiki Client Wrapper (Async)

| Campo          | Valor          |
| -------------- | -------------- |
| **Prioridade** | 🔴 Alta        |
| **Estimativa** | 5 Story Points |
| **Status**     | ✅ Concluída   |

### Descrição

Criar uma classe cliente responsável por toda comunicação HTTP com a API do TibiaWiki (`tibia.fandom.com/api.php`). Deve ser totalmente assíncrona.

### Detalhes Técnicos

- [x] Lib: `httpx.AsyncClient`
- [x] **Requisito 1 (Discovery):** Método `get_all_bosses()` que consome `action=query&list=categorymembers&cmtitle=Category:Bosses`. Deve lidar com paginação (`cmcontinue`) automaticamente para puxar todos os 500+ bosses.
- [x] **Requisito 2 (Extraction):** Método `get_boss_wikitext(pageid/title)` que consome `action=query&prop=revisions&rvprop=content` para pegar o texto bruto.
- [x] Configurar User-Agent no header: `TibiaBossApiBot/0.1 (contato@seuexemplo.com)`
- [x] Implementar Exponential Backoff simples para erros 429 (Too Many Requests)

### Definition of Done (DoD)

- [x] Teste unitário (mockando httpx) para listagem e obtenção de conteúdo
- [x] Script de teste manual imprime no console uma lista de nomes de Bosses reais

---

## 🎫 Task 1.3: Parser de Wikitext e Sanitização (Pydantic)

| Campo          | Valor                         |
| -------------- | ----------------------------- |
| **Prioridade** | 🔴 Alta (Complexidade Lógica) |
| **Estimativa** | 8 Story Points                |
| **Status**     | ✅ Concluída                  |

### Descrição

Transformar o "caos" do Wikitext em objetos Python estruturados e tipados. **Essa é a inteligência central da Sprint.**

### Detalhes Técnicos

- [x] Lib: `mwparserfromhell`
- [x] Criar modelos Pydantic (`app/models/boss.py`) para validação
- [x] **Campos:** `name`, `hp` (int), `exp` (int), `walks_through` (list[str]), `immunities` (list[str])

#### Lógica de Parsing

- [x] Extrair template `{{Infobox Boss}}`
- [x] Mapear campos do wiki (`hp`, `exp`) para o modelo

#### Sanitização

Criar validadores (`@field_validator`) para limpar sujeira:

- [x] Ex: `"50,000 (estimated)"` → `50000`
- [x] Ex: `"Fire, Energy (partial)"` → `["Fire", "Energy"]`
- [x] Ex: `"???"` ou `"Variable"` → `None`

### Definition of Done (DoD)

- [x] O Parser aceita uma string wikitext e retorna uma instância `BossModel`
- [x] 100% de cobertura de testes com edge cases (Boss sem HP, Boss com formatação quebrada, Bosses novos vs antigos)
- [x] Tratamento de erro: Se não achar o template `Infobox Boss`, deve lançar `ParserError`

---

## 🎫 Task 1.4: Orchestrator Script (Runner)

| Campo          | Valor          |
| -------------- | -------------- |
| **Prioridade** | 🟡 Média       |
| **Estimativa** | 3 Story Points |
| **Status**     | ✅ Concluída   |

### Descrição

Integrar o Client (Task 1.2) e o Parser (Task 1.3) em um script executável para validar o fluxo completo.

### Detalhes Técnicos

- [x] Arquivo: `app/main_scraper.py` (temporário, depois vira um Job)
- [x] Usar `asyncio.gather` para concorrência
- [x] **Obrigatório:** Implementar `asyncio.Semaphore(10)` para limitar a 10 requests simultâneos e evitar bloqueio de IP

#### Fluxo

1. Busca lista de todos os bosses
2. Para cada boss → Busca Wikitext → Faz Parse → Adiciona em lista em memória
3. Salva resultado final em `data/bosses_dump.json` (apenas para verificação nesta sprint)

### Definition of Done (DoD)

- [x] O script roda do início ao fim sem "crashar" em menos de 2 minutos
- [x] Gera um JSON local contendo dados estruturados de pelo menos 90% dos bosses listados
- [x] Logs informativos (`INFO: Processed Ghazbaran`, `ERROR: Failed parsing Rat`)

---

## 🤝 Fluxo de Trabalho (Git)

| Branch      | Descrição                                                        |
| ----------- | ---------------------------------------------------------------- |
| `main`      | Código de produção (estável)                                     |
| `develop`   | Integração das features                                          |
| `feature/*` | Ex: `feature/task-1.3-parser-logic` (criada a partir da develop) |

---

## 📊 Resumo da Sprint

| Task      | Título               | Story Points | Prioridade | Status       |
| --------- | -------------------- | ------------ | ---------- | ------------ |
| 1.1       | Setup do Projeto     | 2 SP         | 🔴 Alta    | ✅ Concluída |
| 1.2       | TibiaWiki Client     | 5 SP         | 🔴 Alta    | ✅ Concluída |
| 1.3       | Parser + Sanitização | 8 SP         | 🔴 Alta    | ✅ Concluída |
| 1.4       | Orchestrator Script  | 3 SP         | 🟡 Média   | ✅ Concluída |
| **Total** |                      | **18 SP**    |            |              |

---

## 📝 Notas e Decisões

### ✅ Configuração Git (Concluído)

- Repositório inicializado
- Branch `main` criada (código de produção)
- Branch `develop` criada (integração de features)
- Commit inicial: `c172cbb` - estrutura de pastas + .gitignore
- `.gitignore` configurado para Python/Poetry/MongoDB

### ✅ Task 1.1 Concluída (Setup do Projeto)

- `pyproject.toml` criado com Poetry (Python >=3.11)
- Dependências instaladas: fastapi, uvicorn, motor, pydantic, httpx, mwparserfromhell
- Dev dependencies: pytest, black, isort, pre-commit
- `docker-compose.yml` com MongoDB funcionando na porta 27017
- Pre-commit hooks configurados e funcionando (black, isort)
- Feature branch: `feature/task-1.1-setup` → merged em `develop`
- Commit: `6c2d626`

### ✅ Task 1.2 Concluída (TibiaWiki Client Wrapper)

- Classe `TibiaWikiClient` criada em `app/services/tibiawiki_client.py`
- Implementado `get_all_bosses()` com paginação automática via `cmcontinue`
- Implementado `get_boss_wikitext()` para extrair conteúdo por `pageid` ou `title`
- User-Agent configurado: `TibiaBossApiBot/0.1 (contato@seuexemplo.com)`
- Exponential Backoff implementado para erros 429 (Too Many Requests)
- Suporte a context manager (`async with`) para gerenciamento de recursos
- Testes unitários completos em `tests/test_tibiawiki_client.py` (mockando httpx)
- Script de teste manual criado em `scripts/test_tibiawiki_client.py`

### ✅ Task 1.3 Concluída (Parser de Wikitext e Sanitização)

- Modelo `BossModel` criado em `app/models/boss.py` com Pydantic v2 (ConfigDict)
- Campos implementados: `name`, `hp`, `exp`, `walks_through`, `immunities`
- Validadores de sanitização implementados para todos os campos:
  - HP/EXP: remove vírgulas, parênteses, trata valores desconhecidos
  - Lists: separa por vírgula, remove parênteses, trata valores vazios
- Parser `WikitextParser` criado em `app/services/wikitext_parser.py`
- Extração do template `Infobox Boss` com suporte case-insensitive
- Mapeamento de campos do wiki para o modelo (suporta nomes alternativos)
- Exceção `ParserError` implementada para tratamento de erros
- 27 testes unitários criados cobrindo todos os edge cases:
  - Boss sem HP/EXP
  - Formatação quebrada
  - Formatos antigos vs novos
  - Valores desconhecidos (???, Variable)
  - Listas com parênteses parciais
  - Template não encontrado
- Todos os testes passando (27/27)

### ✅ Task 1.4 Concluída (Orchestrator Script)

- Script `main_scraper.py` criado em `app/main_scraper.py`
- Integração completa entre `TibiaWikiClient` e `WikitextParser`
- Processamento assíncrono com `asyncio.gather` para concorrência
- `asyncio.Semaphore(10)` implementado para limitar requisições simultâneas
- Parser ajustado para aceitar templates `Infobox Boss` e `Infobox Creature`
- Salvamento automático em `data/bosses_dump.json`
- Logs informativos implementados (INFO/ERROR)
- Resultados de validação:
  - ✅ Processou 541 de 546 bosses (99.1% de sucesso)
  - ✅ Superou o requisito de 90% do DoD
  - ✅ Execução completa em menos de 2 minutos
  - ✅ JSON gerado com sucesso

### 🎉 Sprint 1 Completa!

Todas as tasks da Sprint 1 foram concluídas com sucesso:

- ✅ Task 1.1: Setup do Projeto
- ✅ Task 1.2: TibiaWiki Client Wrapper
- ✅ Task 1.3: Parser de Wikitext e Sanitização
- ✅ Task 1.4: Orchestrator Script

**Total:** 18 Story Points concluídos

---

## 🔗 Links Úteis

- **TibiaWiki API:** `https://tibia.fandom.com/api.php`
- **Category Bosses:** `https://tibia.fandom.com/api.php?action=query&list=categorymembers&cmtitle=Category:Bosses&cmlimit=500&format=json`
