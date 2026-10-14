# Wasel on Render's free web service: the API and the built web UI in one image, one origin (no CORS).
# Build context is the REPOSITORY ROOT; deploy/render/Dockerfile.dockerignore keeps the context small.
# Base images are pinned by digest so a rebuild gets the same OS and Node/Python; bump them on purpose.
FROM node:25-slim@sha256:81db02c4b671288a03915da9534dbd54f96d0e7c24d80ccc54f5b36b2e684370 AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web ./
# The public origin is baked into canonical URLs, share cards and the sitemap; the build fails without it.
# render.yaml sets NEXT_PUBLIC_SITE_URL (Render passes it as a build arg); the default is the demo host.
ARG NEXT_PUBLIC_SITE_URL=https://wasel.runs-on.dev
ENV NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL
RUN npm run build

FROM python:3.11-slim-bookworm@sha256:0a310eeecf4e1f5a0743f9a6520c90c88d089c903ca5fd283f501e3a805f5f89
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src \
    DB_PATH=/data/app.db
WORKDIR /app
# Hashed lock (make lock): every transitive package is pinned and verified, not just the direct ones.
COPY deploy/render/requirements.lock /tmp/requirements.lock
RUN pip install --require-hashes -r /tmp/requirements.lock && rm /tmp/requirements.lock
COPY src ./src
COPY config ./config
COPY models ./models
COPY data ./data
COPY --from=web /web/dist ./web/dist
RUN useradd --system --uid 10001 wasel && mkdir /data && chown wasel /data
USER wasel
# Render injects PORT (10000 by default). One worker: the worker loop and the SQLite file are singletons.
# Render's proxy is not loopback, so trust its X-Forwarded-Proto: otherwise slashless redirects come back as http.
# The service is reachable only through that proxy, so trusting every forwarded peer is safe here.
CMD ["sh", "-c", "exec python -m uvicorn wasel.main:create_app --factory --host 0.0.0.0 --port ${PORT:-10000} --workers 1 --no-server-header --proxy-headers --forwarded-allow-ips '*'"]
