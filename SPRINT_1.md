# 🏃 Sprint 1: Engenharia de Extração (Core Scraper)

**Objetivo:** Estabelecer a arquitetura do projeto e garantir que conseguimos extrair, limpar e estruturar os dados textuais dos Bosses via API do MediaWiki.

---

## 🎫 Task 1.1: Setup do Projeto e Ambiente de Desenvolvimento

| Campo | Valor |
|-------|-------|
| **Prioridade** | 🔴 Alta (Blocker) |
| **Estimativa** | 2 Story Points |
| **Status** | ⬜ Pendente |

### Descrição
Inicializar o repositório seguindo a Arquitetura em Camadas definida. Configurar gerenciamento de dependências e container do banco de dados.

### Detalhes Técnicos
- [ ] Inicializar Poetry (`pyproject.toml`) com Python 3.11+
- [ ] Dependências iniciais: `fastapi`, `uvicorn`, `motor`, `odmantic` (ou Pydantic v2 direto), `httpx`, `mwparserfromhell`
- [ ] Dev dependencies: `pytest`, `black`, `isort`, `pre-commit`
- [ ] Criar estrutura de pastas: `app/core`, `app/services`, `app/models`, `app/utils`
- [ ] Criar `docker-compose.yml` apenas com o serviço do MongoDB (imagem `mongo:latest`) expondo a porta 27017

### Definition of Done (DoD)
- [ ] `poetry install` roda sem erros
- [ ] `docker-compose up -d` sobe o MongoDB e é possível conectar via Compass/Robo3T
- [ ] Pre-commit hook configurado (formatação automática)
- [ ] Estrutura de pastas commitada no Git

---

## 🎫 Task 1.2: TibiaWiki Client Wrapper (Async)

| Campo | Valor |
|-------|-------|
| **Prioridade** | 🔴 Alta |
| **Estimativa** | 5 Story Points |
| **Status** | ⬜ Pendente |

### Descrição
Criar uma classe cliente responsável por toda comunicação HTTP com a API do TibiaWiki (`tibia.fandom.com/api.php`). Deve ser totalmente assíncrona.

### Detalhes Técnicos
- [ ] Lib: `httpx.AsyncClient`
- [ ] **Requisito 1 (Discovery):** Método `get_all_bosses()` que consome `action=query&list=categorymembers&cmtitle=Category:Bosses`. Deve lidar com paginação (`cmcontinue`) automaticamente para puxar todos os 500+ bosses.
- [ ] **Requisito 2 (Extraction):** Método `get_boss_wikitext(pageid/title)` que consome `action=query&prop=revisions&rvprop=content` para pegar o texto bruto.
- [ ] Configurar User-Agent no header: `TibiaBossApiBot/0.1 (contato@seuexemplo.com)`
- [ ] Implementar Exponential Backoff simples para erros 429 (Too Many Requests)

### Definition of Done (DoD)
- [ ] Teste unitário (mockando httpx) para listagem e obtenção de conteúdo
- [ ] Script de teste manual imprime no console uma lista de nomes de Bosses reais

---

## 🎫 Task 1.3: Parser de Wikitext e Sanitização (Pydantic)

| Campo | Valor |
|-------|-------|
| **Prioridade** | 🔴 Alta (Complexidade Lógica) |
| **Estimativa** | 8 Story Points |
| **Status** | ⬜ Pendente |

### Descrição
Transformar o "caos" do Wikitext em objetos Python estruturados e tipados. **Essa é a inteligência central da Sprint.**

### Detalhes Técnicos
- [ ] Lib: `mwparserfromhell`
- [ ] Criar modelos Pydantic (`app/models/boss.py`) para validação
- [ ] **Campos:** `name`, `hp` (int), `exp` (int), `walks_through` (list[str]), `immunities` (list[str])

#### Lógica de Parsing
- [ ] Extrair template `{{Infobox Boss}}`
- [ ] Mapear campos do wiki (`hp`, `exp`) para o modelo

#### Sanitização
Criar validadores (`@field_validator`) para limpar sujeira:
- [ ] Ex: `"50,000 (estimated)"` → `50000`
- [ ] Ex: `"Fire, Energy (partial)"` → `["Fire", "Energy"]`
- [ ] Ex: `"???"` ou `"Variable"` → `None`

### Definition of Done (DoD)
- [ ] O Parser aceita uma string wikitext e retorna uma instância `BossModel`
- [ ] 100% de cobertura de testes com edge cases (Boss sem HP, Boss com formatação quebrada, Bosses novos vs antigos)
- [ ] Tratamento de erro: Se não achar o template `Infobox Boss`, deve lançar `ParserError`

---

## 🎫 Task 1.4: Orchestrator Script (Runner)

| Campo | Valor |
|-------|-------|
| **Prioridade** | 🟡 Média |
| **Estimativa** | 3 Story Points |
| **Status** | ⬜ Pendente |

### Descrição
Integrar o Client (Task 1.2) e o Parser (Task 1.3) em um script executável para validar o fluxo completo.

### Detalhes Técnicos
- [ ] Arquivo: `app/main_scraper.py` (temporário, depois vira um Job)
- [ ] Usar `asyncio.gather` para concorrência
- [ ] **Obrigatório:** Implementar `asyncio.Semaphore(10)` para limitar a 10 requests simultâneos e evitar bloqueio de IP

#### Fluxo
1. Busca lista de todos os bosses
2. Para cada boss → Busca Wikitext → Faz Parse → Adiciona em lista em memória
3. Salva resultado final em `data/bosses_dump.json` (apenas para verificação nesta sprint)

### Definition of Done (DoD)
- [ ] O script roda do início ao fim sem "crashar" em menos de 2 minutos
- [ ] Gera um JSON local contendo dados estruturados de pelo menos 90% dos bosses listados
- [ ] Logs informativos (`INFO: Processed Ghazbaran`, `ERROR: Failed parsing Rat`)

---

## 🤝 Fluxo de Trabalho (Git)

| Branch | Descrição |
|--------|-----------|
| `main` | Código de produção (estável) |
| `develop` | Integração das features |
| `feature/*` | Ex: `feature/task-1.3-parser-logic` (criada a partir da develop) |

---

## 📊 Resumo da Sprint

| Task | Título | Story Points | Prioridade | Status |
|------|--------|--------------|------------|--------|
| 1.1 | Setup do Projeto | 2 SP | 🔴 Alta | ⬜ |
| 1.2 | TibiaWiki Client | 5 SP | 🔴 Alta | ⬜ |
| 1.3 | Parser + Sanitização | 8 SP | 🔴 Alta | ⬜ |
| 1.4 | Orchestrator Script | 3 SP | 🟡 Média | ⬜ |
| **Total** | | **18 SP** | | |

---

## 📝 Notas e Decisões

> _Espaço reservado para anotações durante a execução da Sprint_

---

## 🔗 Links Úteis

- **TibiaWiki API:** `https://tibia.fandom.com/api.php`
- **Category Bosses:** `https://tibia.fandom.com/api.php?action=query&list=categorymembers&cmtitle=Category:Bosses&cmlimit=500&format=json`

