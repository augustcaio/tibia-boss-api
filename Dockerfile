FROM python:3.11-slim

# Evita .pyc e força stdout/stderr sem buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala certificados de sistema e curl para health checks
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia apenas o requirements para aproveitar cache
COPY requirements.txt .

# Instala dependências e garante certifi/uvicorn disponíveis
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir certifi uvicorn

# Copia o restante do código
COPY . .

# Cria usuário não-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Comando de execução explícito (porta configurável via PORT)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]


