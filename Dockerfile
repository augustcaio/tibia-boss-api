# ⚠️ VERSÃO CRÍTICA: Usamos 3.10-slim-bullseye (OpenSSL 1.1.1)
# Isso resolve o erro TLSV1_ALERT_INTERNAL_ERROR nativamente.
FROM python:3.10-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala certificados de sistema essenciais
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Instala dependências
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir certifi uvicorn

COPY . .

# Cria usuário não-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Comando de start
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
