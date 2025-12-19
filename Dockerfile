FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências de sistema necessárias para compilar pacotes Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libssl-dev curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Instala Poetry para exportar requirements a partir do pyproject
RUN curl -sSL https://install.python-poetry.org | python - --version 1.8.3
ENV POETRY_HOME="/root/.local"
ENV PATH="$POETRY_HOME/bin:$PATH"

COPY pyproject.toml .

# Exporta requirements.txt a partir do pyproject (sem extras/dev)
RUN poetry export -f requirements.txt --without-hashes -o /tmp/requirements.txt


FROM python:3.11-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Criar usuário não-root (UID 1000)
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 appuser

# Instala apenas dependências de runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends libssl-dev ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /tmp/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copia o código da aplicação
COPY . /app

# Ajusta permissões para o usuário de aplicação
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Usar sh -c para permitir expansão de variáveis de ambiente (ex: PORT)
# Inclui --proxy-headers e --forwarded-allow-ips='*' para que o slowapi
# consiga obter o IP real do cliente atrás de proxies / Docker.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]


