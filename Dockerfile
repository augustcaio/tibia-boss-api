# Base Python 3.10 no Debian Bullseye (A que funcionou para o Banco)
FROM python:3.10-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Copia requirements e instala
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir certifi uvicorn

# Copia o código fonte
COPY . .

# 👇 A CORREÇÃO MÁGICA 👇
# Cria um arquivo .env vazio para satisfazer a biblioteca slowapi/starlette
RUN touch .env
# 👆 FIM DA CORREÇÃO 👆

# Configura usuário não-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:10000/', timeout=2)" || exit 1

# Start
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
