# 🛠️ Guia de Implementação do MCP

Este guia documenta como usar o MCP nas próximas tasks do projeto.

---

## 📋 Status Atual

✅ **Formatação:** Arquivos Python já estão sendo formatados via pre-commit hooks (black/isort)  
✅ **Estrutura:** Projeto FastAPI bem estruturado  
⚠️ **MCP:** Não está sendo usado atualmente, mas será aplicado nas próximas tasks

---

## 🎯 Próximas Ações com MCP

### 1. Task 3.3: Endpoint de Detalhes (GET /bosses/{slug})

**Como usar o MCP:**

```python
# Chamar o MCP para gerar a rota base
mcp_python-backend-expert_generate_fastapi_route(
    resource_name="Boss",
    http_method="GET"
)
```

**Nota:** O MCP gerará um template básico. Será necessário:
- Adaptar para usar `slug` como parâmetro de path
- Adicionar `HTTPException` para 404
- Integrar com `BossRepository.find_by_slug()`
- Usar schema completo (`BossModel` ou `BossFullSchema`)

### 2. Task 3.4: Motor de Busca (GET /bosses/search)

**Como usar o MCP:**

```python
# Chamar o MCP para gerar a rota base
mcp_python-backend-expert_generate_fastapi_route(
    resource_name="Boss",
    http_method="GET"
)
```

**Nota:** O MCP gerará um template básico. Será necessário:
- Adaptar para usar query parameter `q`
- Implementar busca com `$regex` no MongoDB
- Adicionar sanitização com `re.escape()`
- Retornar lista paginada

### 3. Commits Futuros

**Sempre usar:**

1. **Construir mensagem de commit:**
```python
mcp_git-conventional-expert_construct_commit(
    type="feat",
    scope="api",
    description="implementar Task 3.3 - Endpoint de Detalhes",
    body="Detalhes da implementação...",
    is_breaking=False
)
```

2. **Validar antes de commitar:**
```python
mcp_git-conventional-expert_validate_commit(
    message="feat(api): implementar Task 3.3 - Endpoint de Detalhes"
)
```

---

## 📝 Template de Uso para Task 3.3

### Passo 1: Gerar rota base com MCP
```python
# Usar MCP para gerar estrutura inicial
mcp_python-backend-expert_generate_fastapi_route(
    resource_name="Boss",
    http_method="GET"
)
```

### Passo 2: Adaptar o código gerado
```python
@router.get(
    "/{slug}",
    response_model=BossModel,  # ou BossFullSchema
    summary="Obter detalhes de um boss",
    responses={404: {"description": "Boss not found"}},
)
async def get_boss_by_slug(
    slug: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Retorna os detalhes completos de um boss pelo slug."""
    repository = BossRepository(db)
    boss = await repository.find_by_slug(slug)
    
    if boss is None:
        raise HTTPException(status_code=404, detail="Boss not found")
    
    return boss
```

### Passo 3: Commit usando MCP
```python
# Construir commit
commit_msg = mcp_git-conventional-expert_construct_commit(...)

# Validar
mcp_git-conventional-expert_validate_commit(message=commit_msg)

# Fazer commit
git commit -m "$commit_msg"
```

---

## 📝 Template de Uso para Task 3.4

### Passo 1: Gerar rota base com MCP
```python
# Usar MCP para gerar estrutura inicial
mcp_python-backend-expert_generate_fastapi_route(
    resource_name="Boss",
    http_method="GET"
)
```

### Passo 2: Adaptar o código gerado
```python
@router.get(
    "/search",
    response_model=PaginatedResponse[BossShortSchema],
    summary="Buscar bosses por nome",
)
async def search_bosses(
    q: str = Query(..., min_length=1, description="Termo de busca"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Busca bosses por nome usando regex."""
    import re
    
    # Sanitiza a query para evitar ReDoS
    sanitized_query = re.escape(q)
    
    repository = BossRepository(db)
    # Implementar busca com regex...
```

---

## ✅ Checklist de Implementação

### Para Task 3.3:
- [ ] Usar `generate_fastapi_route` para gerar estrutura base
- [ ] Adaptar para usar `slug` como path parameter
- [ ] Implementar tratamento de erro 404
- [ ] Usar `construct_commit` e `validate_commit` para o commit

### Para Task 3.4:
- [ ] Usar `generate_fastapi_route` para gerar estrutura base
- [ ] Implementar busca com regex sanitizada
- [ ] Adicionar validação de query vazia
- [ ] Usar `construct_commit` e `validate_commit` para o commit

### Para Todos os Commits:
- [ ] Sempre usar `construct_commit` para construir mensagem
- [ ] Sempre usar `validate_commit` antes de commitar
- [ ] Manter padrão Conventional Commits

---

## 🔍 Observações Importantes

1. **MCP gera templates:** O MCP gera código base, mas sempre será necessário adaptar para as necessidades específicas do projeto.

2. **Pre-commit hooks:** Os hooks de formatação (black/isort) já estão configurados e funcionando, então não é necessário usar `format_python_code` manualmente.

3. **Commits:** O padrão Conventional Commits já está sendo seguido, mas agora será validado via MCP para garantir conformidade.

4. **Estrutura:** A estrutura do projeto já está bem definida, então o MCP será usado principalmente para gerar endpoints e validar commits.

---

**Última atualização:** Sprint 3 - Task 3.2 concluída

