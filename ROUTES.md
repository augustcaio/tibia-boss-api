# 🛣️ Rotas da API - Tibia Boss API

## 📍 Endpoints Disponíveis

### 🌐 Endpoint Raiz

- **GET** `/`
  - **Descrição:** Endpoint raiz da API
  - **Resposta:** `{"message": "Tibia Boss API", "version": "0.1.0"}`

---

### 🏥 Health Check

- **GET** `/api/v1/health`
  - **Descrição:** Verifica se a API e o banco de dados estão funcionando corretamente
  - **Resposta de Sucesso (200):**
    ```json
    {
      "status": "ok",
      "db": "connected"
    }
    ```
  - **Resposta de Erro (500):**
    ```json
    {
      "status": "ok",
      "db": "disconnected",
      "error": "mensagem de erro"
    }
    ```

---

### 👹 Bosses

#### 1. Listar Bosses (Paginação)

- **GET** `/api/v1/bosses`
  - **Descrição:** Retorna uma lista paginada de bosses
  - **Query Parameters:**
    - `page` (int, default: 1, min: 1) - Número da página
    - `limit` (int, default: 20, min: 1, max: 100) - Número de itens por página
  - **Exemplo:** `GET /api/v1/bosses?page=1&limit=20`
  - **Resposta (200):**
    ```json
    {
      "items": [
        {
          "name": "Morgaroth",
          "slug": "morgaroth",
          "hp": 100000,
          "visuals": {
            "gif_url": "https://tibia.fandom.com/images/Morgaroth.gif",
            "filename": "Morgaroth.gif"
          }
        }
      ],
      "total": 500,
      "page": 1,
      "size": 20,
      "pages": 25
    }
    ```
  - **Códigos de Resposta:**
    - `200` - Lista retornada com sucesso
    - `422` - Parâmetros de validação inválidos
    - `500` - Erro interno do servidor

#### 2. Obter Detalhes de um Boss

- **GET** `/api/v1/bosses/{slug}`
  - **Descrição:** Retorna os detalhes completos de um boss pelo slug
  - **Path Parameters:**
    - `slug` (string) - Slug do boss (ex: "morgaroth")
  - **Exemplo:** `GET /api/v1/bosses/morgaroth`
  - **Resposta (200):**
    ```json
    {
      "name": "Morgaroth",
      "slug": "morgaroth",
      "hp": 100000,
      "exp": 50000,
      "walks_through": ["Fire", "Energy"],
      "immunities": ["Physical", "Ice"],
      "visuals": {
        "gif_url": "https://tibia.fandom.com/images/Morgaroth.gif",
        "filename": "Morgaroth.gif"
      }
    }
    ```
  - **Códigos de Resposta:**
    - `200` - Boss encontrado e retornado com sucesso
    - `404` - Boss não encontrado
    - `422` - Parâmetros de validação inválidos
    - `500` - Erro interno do servidor

#### 3. Buscar Bosses por Nome

- **GET** `/api/v1/bosses/search`
  - **Descrição:** Busca bosses por nome usando regex case insensitive
  - **Query Parameters:**
    - `q` (string, required, min_length: 1) - Termo de busca
    - `page` (int, default: 1, min: 1) - Número da página
    - `limit` (int, default: 20, min: 1, max: 100) - Número de itens por página
  - **Exemplo:** `GET /api/v1/bosses/search?q=rat&page=1&limit=10`
  - **Resposta (200):**
    ```json
    {
      "items": [
        {
          "name": "Cave Rat",
          "slug": "cave-rat",
          "hp": 20,
          "visuals": {
            "gif_url": "https://tibia.fandom.com/images/Cave_Rat.gif",
            "filename": "Cave_Rat.gif"
          }
        }
      ],
      "total": 5,
      "page": 1,
      "size": 10,
      "pages": 1
    }
    ```
  - **Códigos de Resposta:**
    - `200` - Busca realizada com sucesso
    - `400` - Parâmetro de query inválido ou vazio
    - `422` - Parâmetros de validação inválidos
    - `500` - Erro interno do servidor

---

## 📚 Documentação Interativa

A documentação completa da API está disponível em:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

---

## 🚀 Como Executar

```bash
# Subir o MongoDB (se ainda não estiver rodando)
docker-compose up -d

# Executar a API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em: `http://localhost:8000`

---

## 📝 Notas

- Todas as rotas usam **Dependency Injection** para acesso ao banco de dados
- A busca por nome usa **sanitização** com `re.escape()` para evitar ReDoS
- A listagem usa **projection MongoDB** para otimizar performance (não retorna `raw_wikitext`)
- Todas as respostas paginadas seguem o padrão `PaginatedResponse[T]`
