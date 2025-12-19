# Guia de Deploy no Render

Este guia explica como fazer o deploy da Tibia Boss API no Render.

## Pré-requisitos

1. **Conta no MongoDB Atlas** (gratuita)
   - Criar cluster gratuito em [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
   - Configurar Network Access para permitir conexões de qualquer IP (`0.0.0.0/0`)
   - Criar um usuário de banco de dados com senha
   - Obter a string de conexão (Connection String)

2. **Conta no Render** (gratuita)
   - Criar conta em [render.com](https://render.com)

## Passo a Passo

### 1. MongoDB Atlas - Obter String de Conexão

1. Acesse o MongoDB Atlas
2. Vá em **Database** > **Connect** > **Connect your application**
3. Copie a string de conexão. Ela será similar a:
   ```
   mongodb+srv://usuario:<password>@cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
4. **IMPORTANTE:** Substitua `<password>` pela senha real do seu usuário
5. **OPCIONAL:** Adicione o nome do banco ao final da URL:
   ```
   mongodb+srv://usuario:senha@cluster.xxxxx.mongodb.net/tibia_bosses?retryWrites=true&w=majority
   ```

### 2. Render - Criar Web Service

1. No painel do Render, clique em **New +** > **Web Service**
2. Conecte seu repositório do GitHub
3. Configure o serviço:
   - **Name:** `tibia-boss-api` (ou o nome que preferir)
   - **Region:** Escolha a região mais próxima
   - **Branch:** `main` ou `develop`
   - **Runtime:** `Docker`
   - **Instance Type:** `Free`

### 3. Render - Configurar Variáveis de Ambiente

**PASSO CRÍTICO:** Na aba **Environment**, adicione as seguintes variáveis:

| Key | Value | Observação |
|-----|-------|------------|
| `MONGODB_URL` | `mongodb+srv://usuario:senha@cluster.xxxxx.mongodb.net/tibia_bosses` | Sua URL do MongoDB Atlas (COM A SENHA REAL) |
| `DATABASE_NAME` | `tibia_bosses` | Nome do banco (opcional, já tem default) |
| `ADMIN_SECRET` | `sua_chave_secreta_forte` | Token para o endpoint `/api/v1/admin/sync` |

**⚠️ ATENÇÃO:**
- A variável DEVE se chamar **exatamente** `MONGODB_URL` (tudo em maiúsculo)
- Substitua `<password>` ou `<db_password>` pela senha real
- Use uma senha forte para `ADMIN_SECRET`

### 4. Deploy

1. Clique em **Create Web Service**
2. O Render começará o build automático
3. Acompanhe os logs:
   - Procure pela mensagem: `✅ Variável MONGODB_URL encontrada no ambiente`
   - Procure pela mensagem: `🔍 Tentando conectar ao MongoDB: mongodb+srv://...`
   - Se aparecer `⚠️ Variável MONGODB_URL NÃO encontrada`, volte ao passo 3

### 5. Verificação

Após o deploy bem-sucedido, acesse:

- **Health Check:** `https://seu-app.onrender.com/api/v1/health`
- **Documentação:** `https://seu-app.onrender.com/docs`
- **API Root:** `https://seu-app.onrender.com/`

## Troubleshooting

### Erro: Connection refused 127.0.0.1:27017

**Causa:** A variável `MONGODB_URL` não está sendo lida.

**Solução:**
1. Verifique se a variável está configurada EXATAMENTE como `MONGODB_URL` (maiúsculas)
2. Nos logs do deploy, procure pela mensagem de debug para confirmar
3. Re-deploy manualmente: **Manual Deploy** > **Deploy latest commit**

### Erro: Authentication failed

**Causa:** Senha incorreta na string de conexão.

**Solução:**
1. Verifique se você substituiu `<password>` pela senha real
2. Gere uma nova senha no MongoDB Atlas se necessário
3. Atualize a variável `MONGODB_URL` no Render

### Erro: Network Access

**Causa:** MongoDB Atlas bloqueando conexões do IP do Render.

**Solução:**
1. No MongoDB Atlas, vá em **Network Access**
2. Clique em **Add IP Address**
3. Selecione **Allow Access from Anywhere** (`0.0.0.0/0`)
4. Salve e aguarde alguns minutos

## Monitoramento

O Render oferece logs em tempo real. Para acessar:
1. Acesse seu serviço no painel do Render
2. Clique na aba **Logs**
3. Procure por mensagens de erro ou sucesso na conexão com MongoDB

## Rate Limiting

A API possui rate limiting configurado:
- **Listagem de bosses:** 60 requisições/minuto
- **Busca e detalhes:** 20 requisições/minuto
- **Admin sync:** 5 requisições/hora

Em produção, o Render automaticamente detecta o IP real do cliente através de proxy headers.

## Scheduler (Scraper Automático)

O scraper roda automaticamente toda **terça-feira às 10:00 UTC**. Para forçar uma sincronização manual:

```bash
curl -X POST https://seu-app.onrender.com/api/v1/admin/sync \
  -H "X-Admin-Token: sua_chave_secreta_forte"
```

## Links Úteis

- [Documentação do Render](https://render.com/docs)
- [Documentação do MongoDB Atlas](https://docs.atlas.mongodb.com/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)

