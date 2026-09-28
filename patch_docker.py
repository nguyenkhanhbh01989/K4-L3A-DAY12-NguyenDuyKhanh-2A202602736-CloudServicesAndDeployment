import sys
df = """FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim AS runtime

RUN useradd --create-home --uid 10001 appuser
USER appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" || exit 1

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
"""
open('Dockerfile', 'w', encoding='utf-8').write(df)

dfo = """
.git
.gitignore
.env
.venv
__pycache__/
*.pyc
"""
open('.dockerignore', 'w', encoding='utf-8').write(dfo)

dc = """services:
  redis:
    image: redis:7-alpine
    command: ["redis-server", "--appendonly", "yes"]
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      AGENT_API_KEY: ${AGENT_API_KEY}
      REDIS_URL: redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "python -c \\"import urllib.request; urllib.request.urlopen('http://localhost:8000/health')\\" || exit 1"]
      interval: 10s
      timeout: 3s
      retries: 5

volumes:
  redis-data:
"""
open('docker-compose.yml', 'w', encoding='utf-8').write(dc)
