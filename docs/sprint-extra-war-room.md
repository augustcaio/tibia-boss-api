# Sprint Extra — War Room & Estabilização

**Status:** Crítico (deploy bloqueado)  
**Objetivo:** Resolver conexão TLS/DNS com MongoDB Atlas e aumentar a resiliência da API.

## Visão Geral

- Foco total em estabilidade, sem novas features.
- Alvo principal: eliminar falhas de handshake/DNS e impedir que a API caia se o banco estiver indisponível.

## Backlog do Sprint

| ID        | Título                             | Pontos | Foco            | DoD resumido                                                                                                                    |
| --------- | ---------------------------------- | ------ | --------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| 5.1       | Connection String Legacy (sem SRV) | 3      | Infra           | API conecta sem ServerSelectionTimeoutError usando string `mongodb://` (não `+srv`) copiada do Atlas/Drivers Python 3.4+.       |
| 5.2       | Circuit Breaker (Soft Startup)     | 5      | Resiliência     | API sobe mesmo sem DB; rota `/` responde 200; rotas que dependem de DB retornam 503 ou reconectam lazy sem derrubar o processo. |
| 5.3       | Script de Diagnóstico de Rede      | 2      | Observabilidade | Script `debug_network.py` mostra DNS e handshake TLS (OK/Falhou) dentro do container.                                           |
| 5.4       | Documentação de Disaster Recovery  | 1      | Docs            | README tem seção de troubleshooting e procedimentos (debug, troca de string, modo degradado).                                   |
| **Total** |                                    | **11** |                 |                                                                                                                                 |

## Detalhamento das Tasks

### 5.1 Connection String Legacy (sem SRV)

- Motivo: DNS SRV pode falhar no ambiente Render.
- Ação: No Atlas, em Connect → Drivers → Python 3.4+, copiar a string `mongodb://...` (sem `+srv`, com hosts listados) e colocar em `MONGO_URL` no Render.
- Código: manter `tlsCAFile=certifi.where()`; não usar parâmetros exóticos.
- DoD: conexão sem `ServerSelectionTimeoutError`.

### 5.2 Circuit Breaker (Soft Startup)

- Motivo: hoje a API cai se o DB não sobe.
- Ação: no `lifespan`, capturar erro de conexão, logar e **não** dar `raise`; setar flag `app.state.db_connected=False`.
- Em `get_database`/handlers: se desconectado, tentar reconectar ou retornar 503 ("reconectando").
- DoD: `/` responde 200 mesmo sem DB; `/bosses` retorna 503 em vez de matar o processo.

### 5.3 Script de Diagnóstico de Rede

- Arquivo `debug_network.py` (executado no container) testando:
  - DNS: `socket.gethostbyname(host)`
  - TLS: `ssl.create_default_context(cafile=certifi.where())` + handshake
- DoD: Log indica se a falha é DNS (NXDOMAIN) ou TLS (Handshake).

### 5.4 Documentação de Disaster Recovery

- Seção no README: Troubleshooting Production
  - Como rodar `debug_network.py`
  - Como rotacionar string de conexão para `mongodb://` (sem SRV)
  - Descrição do modo degradado (503) e como reverter.

## Notas do Tech Lead

- Priorizar 5.1 + 5.2 para desbloquear o deploy.
- Após estabilizar, podemos voltar a restringir `allowed_hosts` e, se desejado, otimizar a imagem (ex.: python:3.11-slim) somente se não quebrar TLS/DNS.
