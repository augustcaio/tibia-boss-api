# 🏃 Sprint 2: Assets Visuais e Persistência

**Objetivo:** Evoluir o pipeline para resolver URLs reais de imagens (GIFs/PNGs) e persistir os dados no MongoDB de forma idempotente e segura.

---

## 🎫 Task 2.1: Image Resolver Service (Batch Strategy)

| Campo          | Valor                          |
| -------------- | ------------------------------ |
| **Prioridade** | 🔴 Alta (Performance Critical) |
| **Estimativa** | 5 Story Points                 |
| **Status**     | ✅ Concluída                   |

### Descrição

Implementar um serviço para converter nomes de arquivos (ex: `File:Morgaroth.gif`) em URLs públicas finais (`https://.../Morgaroth.gif`).

**Crucial:** Proibido fazer 1 request por imagem. Devemos usar a estratégia de Batch Request.

### Detalhes Técnicos

- [x] **API Action:** `action=query&titles=File:A.gif|File:B.gif...&prop=imageinfo&iiprop=url`
- [x] **Chunking:** Agrupar nomes de imagens em lotes de 50
- [x] **Segurança (Input do Tech Lead):** O Client HTTP deve enviar esses títulos via **POST (body)** e não GET, para evitar erro de URI Too Long se os nomes dos arquivos forem gigantes
- [x] **Fallback:** Se a API retornar erro ou 404 para uma imagem, atribuir uma URL de placeholder (`static/placeholder_boss.png`) no objeto, para não quebrar o front no futuro

### Definition of Done (DoD)

- [x] Método `resolve_images(list_of_filenames)` implementado usando `asyncio`
- [x] Teste unitário simulando input de 55 imagens (garantindo que ele faz 2 requests: um lote de 50 e um de 5)
- [x] Tratamento de erro: O sistema não crasha se uma imagem específica falhar

---

## 🎫 Task 2.2: Repositório MongoDB & Schema Design

| Campo          | Valor          |
| -------------- | -------------- |
| **Prioridade** | 🔴 Alta        |
| **Estimativa** | 3 Story Points |
| **Status**     | ✅ Concluída   |

### Descrição

Criar a camada de persistência (`app/db/repository.py`) e garantir a integridade do banco.

### Detalhes Técnicos

- [x] **Driver:** `motor` (Async)
- [x] **Schema:** Atualizar o Model Pydantic para incluir o campo `visuals` (com `gif_url` e `filename`)

#### Inicialização (Startup Event)

- [x] Ao iniciar a aplicação, verificar e criar os índices automaticamente
- [x] **Obrigatório:** `await db.bosses.create_index("slug", unique=True)`. Isso é nossa trava de segurança contra duplicidade

#### Método Upsert

- [x] Usar `find_one_and_update` com `upsert=True`
- [x] Chave de busca: `slug` (versão "slugificada" do nome, ex: "Morgaroth" -> "morgaroth")
- [x] Operador `$set` para atualizar os campos

### Definition of Done (DoD)

- [x] Ao subir a app, o índice aparece no MongoDB (verificar via Compass)
- [x] Teste de integração: Inserir o mesmo boss 2 vezes. O resultado deve ser 1 documento no banco (atualizado), e não 2 documentos ou erro de duplicidade

---

## 🎫 Task 2.3: Pipeline Integration (The "Gluer")

| Campo          | Valor          |
| -------------- | -------------- |
| **Prioridade** | 🟡 Média       |
| **Estimativa** | 5 Story Points |
| **Status**     | ✅ Concluída   |

### Descrição

Conectar as pontas. Atualizar o script "Runner" da Sprint 1 para incluir o passo de resolução de imagens e salvamento.

### Detalhes Técnicos

#### Novo Fluxo Lógico

1. Scraper busca lista de Bosses
2. Parser extrai dados + nome do arquivo de imagem (ex: `Morgaroth.gif`)
3. Acumular Bosses em memória até atingir o tamanho do lote (50)
4. Chamar `ImageResolver` para esse lote
5. Enriquecer os objetos Boss com as URLs retornadas
6. Chamar `Repository.upsert_batch` (ou loop de upserts assíncronos) para salvar

- [x] **Performance:** Manter o controle de concorrência (Semaphore). Não tentar processar 1000 bosses de uma vez na memória RAM; processar em chunks para manter a pegada de memória baixa

### Definition of Done (DoD)

- [x] Script roda completo
- [x] Banco populado com Bosses contendo Stats (Sprint 1) + URLs de Imagens (Sprint 2)

---

## 🎫 Task 2.4: Sistema de Logs "Dead Letter" (Error Handling)

| Campo          | Valor          |
| -------------- | -------------- |
| **Prioridade** | 🟡 Média       |
| **Estimativa** | 3 Story Points |
| **Status**     | ✅ Concluída   |

### Descrição

Melhorar a observabilidade. Quando um Parser falhar (porque o Wiki mudou o template) ou uma Imagem não for encontrada, precisamos saber exatamente o porquê sem parar o processo.

### Detalhes Técnicos

- [x] Criar um logger estruturado (pode ser arquivo JSON `logs/parsing_errors.jsonl`)

#### Requisito do Tech Lead

O log **DEVE** conter:

- [x] `timestamp`
- [x] `boss_name`
- [x] `error_message` (Traceback resumido)
- [x] `raw_data_snippet`: Os primeiros 500 caracteres do wikitext que causou o erro. Isso é vital para debugarmos depois

### Definition of Done (DoD)

- [x] Provocar um erro proposital no parser e verificar se o arquivo de log foi gerado com o snippet do wikitext

---

## 🤝 Fluxo de Trabalho (Git)

| Branch      | Descrição                                                          |
| ----------- | ------------------------------------------------------------------ |
| `main`      | Código de produção (estável)                                       |
| `develop`   | Integração das features                                            |
| `feature/*` | Ex: `feature/task-2.1-image-resolver` (criada a partir da develop) |

---

## 📊 Resumo da Sprint

| Task      | Título                 | Story Points | Prioridade | Status       |
| --------- | ---------------------- | ------------ | ---------- | ------------ |
| 2.1       | Image Resolver Service | 5 SP         | 🔴 Alta    | ✅ Concluída |
| 2.2       | Repositório MongoDB    | 3 SP         | 🔴 Alta    | ✅ Concluída |
| 2.3       | Pipeline Integration   | 5 SP         | 🟡 Média   | ✅ Concluída |
| 2.4       | Sistema de Logs        | 3 SP         | 🟡 Média   | ✅ Concluída |
| **Total** |                        | **16 SP**    |            |              |

---

## 📝 Notas e Decisões

### 📋 Checklist do Tech Lead (Code Review)

Time, quando abrirem o PR, vou olhar especificamente para:

- [ ] **Chunks:** Vocês estão respeitando o limite da API do Wiki?
- [ ] **POST vs GET:** Estão enviando a lista de imagens via Body para não estourar a URL?
- [ ] **Indexes:** O código de inicialização do banco está robusto?
- [ ] **Async/Await:** Estão usando `await gather()` corretamente ou estão fazendo `await` dentro de um loop `for` (serializando o que deveria ser paralelo)?

---

## 🔗 Links Úteis

- **TibiaWiki API:** `https://tibia.fandom.com/api.php`
- **Image Info API:** `action=query&titles=File:Example.gif&prop=imageinfo&iiprop=url`
- **MongoDB Motor Docs:** `https://motor.readthedocs.io/`

---

## 📝 Notas e Decisões

### ✅ Task 2.1 Concluída (Image Resolver Service)

- Classe `ImageResolverService` criada em `app/services/image_resolver.py`
- Método `resolve_images()` implementado com processamento assíncrono
- Chunking automático em lotes de 50 imagens
- Requisições POST com parâmetros no body (evita URI Too Long)
- Fallback para placeholder em caso de erro/404
- Tratamento robusto de erros (não crasha o sistema)
- 10 testes unitários criados cobrindo todos os casos:
  - Resolução de lote único
  - Resolução de múltiplos lotes (55 imagens = 2 requests)
  - Imagens não encontradas (placeholder)
  - Erros HTTP (não crasha)
  - Exceções gerais (não crasha)
  - Duplicatas removidas
  - Verificação de uso de POST
- Teste real validado com imagem do TibiaWiki

## 🎯 Sprint 2 Concluída! 🎉

Todas as tasks da Sprint 2 foram finalizadas com sucesso!

---

## 📝 Notas e Decisões

### ✅ Task 2.2 Concluída (Repositório MongoDB & Schema Design)

- Modelo `BossModel` atualizado com:
  - Campo `slug` (opcional, gerado automaticamente se não fornecido)
  - Campo `visuals` (BossVisuals com `gif_url` e `filename`)
  - Método `get_slug()` para gerar slug automaticamente a partir do nome
- Módulo `app/db/connection.py` criado:
  - Função `init_database()` para inicializar conexão MongoDB
  - Função `_create_indexes()` que cria índices automaticamente:
    - `slug` (unique=True) - trava de segurança contra duplicidade
    - `name` - para buscas rápidas
  - Função `close_database()` para fechar conexão
- Módulo `app/db/repository.py` criado:
  - Classe `BossRepository` com métodos:
    - `upsert()` - insere ou atualiza boss usando slug como chave
    - `upsert_batch()` - processa múltiplos bosses em lote
    - `find_by_slug()` - busca por slug
    - `find_by_name()` - busca por nome
    - `count()` - retorna total de bosses
- Módulo `app/main.py` criado:
  - FastAPI app com lifespan para inicializar MongoDB na startup
  - Endpoint `/health` para verificar status da conexão
- Módulo `app/core/config.py` criado:
  - Settings usando Pydantic Settings para configuração
- 8 testes de integração criados em `tests/test_repository.py`:
  - Teste de criação de boss
  - Teste de idempotência (inserir 2 vezes = 1 documento)
  - Teste de batch upsert
  - Teste de busca por slug e nome
  - Teste de geração de slug
  - Teste de slug com caracteres especiais
  - Teste de criação de índices
- Script de teste manual criado em `scripts/test_repository.py`
- Todos os testes passando ✅

### ✅ Task 2.3 Concluída (Pipeline Integration - The "Gluer")

- Parser atualizado (`app/services/wikitext_parser.py`):
  - Extração do campo `image` do template Infobox
  - Normalização de nomes de arquivos para formato `File:Name.ext`
  - Criação automática de `BossVisuals` com `filename` quando imagem encontrada
  - Método `_normalize_image_filename()` para padronizar formatos
- Pipeline integrado (`app/main_scraper.py`):
  - Integração completa: TibiaWikiClient → WikitextParser → ImageResolverService → BossRepository
  - Processamento em lotes de 50 bosses para otimizar memória
  - Função `process_batch_with_images()` para resolver URLs em lote
  - Função `process_and_save_batch()` para processar e salvar lotes
  - Controle de concorrência mantido com `Semaphore(10)`
  - Salvamento no MongoDB ao invés de JSON
  - Logging detalhado de progresso por lote
- Fluxo completo implementado:
  1. Scraper busca lista de bosses
  2. Parser extrai dados + filename de imagem
  3. Acumula bosses em memória até lote de 50
  4. Resolve URLs de imagens em lote (batch)
  5. Enriquece bosses com URLs resolvidas
  6. Salva no MongoDB usando `upsert_batch`
- Todos os testes do parser passando (17 testes) ✅
- Teste manual validado: extração de imagem funcionando corretamente

### ✅ Task 2.4 Concluída (Sistema de Logs "Dead Letter" - Error Handling)

- Módulo `app/utils/dead_letter_logger.py` criado:
  - Classe `DeadLetterLogger` para logging estruturado
  - Formato JSONL (JSON Lines) para fácil processamento
  - Criação automática do diretório `logs/` se não existir
  - Método `log_parsing_error()` para erros de parsing
  - Método `log_image_error()` para erros de resolução de imagem
  - Truncamento automático de snippets para 500 caracteres
  - Extração de traceback resumido (últimas 3 linhas)
  - Métodos auxiliares: `get_log_count()`, `clear_logs()`
- Integração no `app/main_scraper.py`:
  - Captura de erros de parsing com `ParserError`
  - Captura de exceções gerais durante processamento
  - Logging automático com snippet do wikitext que causou o erro
  - Processo não é interrompido por erros (apenas logados)
- Campos obrigatórios implementados:
  - `timestamp`: ISO 8601 com timezone UTC
  - `boss_name`: Nome do boss que causou o erro
  - `error_message`: Traceback resumido (últimas 3 linhas)
  - `raw_data_snippet`: Primeiros 500 caracteres do wikitext
- 9 testes unitários criados em `tests/test_dead_letter_logger.py`:
  - Teste de criação de arquivo de log
  - Teste de campos obrigatórios
  - Teste de truncamento de snippets longos
  - Teste de múltiplas entradas
  - Teste com raw_data vazio
  - Teste de erro de imagem
  - Teste de contagem de logs
  - Teste de limpeza de logs
  - Teste com wikitext real (erro proposital)
- Script de teste manual criado em `scripts/test_dead_letter_logger.py`
- Teste DoD validado: erro proposital gerou arquivo de log com snippet do wikitext ✅
- Todos os testes passando (9 testes) ✅
- Warnings de depreciação corrigidos (datetime.utcnow() → datetime.now(UTC))
