# One container, one process, one port (01 §6.1). APP_MODE is deliberately unset in the image -> public.
# Stage 1 builds the web/ bundle (Next.js static export -> web/dist); FastAPI serves it at / (app/main.py).
FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM python:3.11-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ app/
COPY ml/ ml/
COPY prompts/ prompts/
COPY schemas/ schemas/
COPY data/ data/
COPY models/ models/
COPY reports/ reports/
COPY scoring.yaml .
COPY config/ config/
COPY failures/ failures/
COPY --from=web /web/dist web/dist
ARG GIT_SHA=dev
ENV GIT_SHA=${GIT_SHA} PYTHONUNBUFFERED=1
CMD ["sh", "-c", "uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
