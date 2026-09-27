# One container, one process, one port (01 §6.1). APP_MODE is deliberately unset in the image -> public.
# Stage 1 (web build) is added when web/ exists; until then FastAPI serves the API only.
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
ARG GIT_SHA=dev
ENV GIT_SHA=${GIT_SHA} PYTHONUNBUFFERED=1
CMD ["sh", "-c", "uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
