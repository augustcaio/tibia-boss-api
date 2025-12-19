FROM python:3.11

# Evita .pyc e força stdout/stderr sem buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copia apenas o requirements para aproveitar cache
COPY requirements.txt .

# Instala dependências e garante certifi/uvicorn/requests disponíveis
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir certifi uvicorn requests

# Força o uso do bundle de certificados do certifi em todo o runtime
ENV SSL_CERT_FILE=/usr/local/lib/python3.11/site-packages/certifi/cacert.pem

# Copia o restante do código
COPY . .

# Cria usuário não-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Healthcheck via requests (HEAD/GET na raiz)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:10000/', timeout=2)" || exit 1

# Comando de execução explícito (porta configurável via PORT)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]


