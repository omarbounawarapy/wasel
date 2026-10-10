# The Wasel backend as a Cloudflare Container. Build context is the REPOSITORY ROOT (wrangler.jsonc sets
# image_build_context); .dockerignore at the root keeps the context to what the API needs at runtime.
# linux/amd64 is what Cloudflare runs. Local: `make cf-image`.
FROM --platform=linux/amd64 python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src \
    DB_PATH=/data/app.db \
    PORT=8000

WORKDIR /app
# Hashed lock (make lock): every transitive package is pinned and verified, not just the direct ones.
COPY deploy/cloudflare/container/requirements.lock /tmp/requirements.lock
RUN pip install --require-hashes -r /tmp/requirements.lock && rm /tmp/requirements.lock

# immutable deployment assets (wasel.paths.ROOT is /app: src/wasel/paths.py -> parents[2])
COPY src ./src
COPY config ./config
COPY models ./models
COPY data ./data

# /data is the only writable path: the SQLite file. The disk is wiped whenever the container sleeps;
# wasel.db.snapshot restores it from R2 at boot and saves it back (docs/operations/cloudflare.md).
RUN useradd --system --uid 10001 wasel && mkdir /data && chown wasel /data
USER wasel

EXPOSE 8000
# one worker process: the 1 s worker loop and the SQLite file are singletons
CMD ["python", "-m", "uvicorn", "wasel.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-server-header"]
