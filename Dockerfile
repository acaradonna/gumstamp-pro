FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY .env.example ./.env.example
COPY healthcheck.py ./healthcheck.py

# Render expects Docker web services to listen on $PORT (defaults to 10000)
ENV PORT=10000
EXPOSE 10000

# Health check for container monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python healthcheck.py

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
