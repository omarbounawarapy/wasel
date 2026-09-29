# Wasel on Render's free web service: the API and the built web UI in one image, one origin (no CORS).
# Build context is the REPOSITORY ROOT; deploy/render/Dockerfile.dockerignore keeps the context small.
FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web ./
RUN npm run build

FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src \
    DB_PATH=/data/app.db
WORKDIR /app
COPY deploy/cloudflare/container/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt
COPY src ./src
COPY config ./config
COPY models ./models
COPY data ./data
COPY --from=web /web/dist ./web/dist
RUN useradd --system --uid 10001 wasel && mkdir /data && chown wasel /data
USER wasel
# Render injects PORT (10000 by default). One worker: the worker loop and the SQLite file are singletons.
CMD ["sh", "-c", "exec python -m uvicorn wasel.main:create_app --factory --host 0.0.0.0 --port ${PORT:-10000} --workers 1 --no-server-header"]
