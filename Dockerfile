# syntax=docker/dockerfile:1.7

# Builder stage: install Python deps to an isolated prefix.
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY requirements.txt ./
RUN pip install --prefix=/install -r requirements.txt

# Runtime stage: minimal image, non-root user.
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0

RUN groupadd --system app \
 && useradd --system --gid app --no-create-home --home /nonexistent app

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --chown=app:app app/ ./app/
COPY --chown=app:app main.py ./

USER app

EXPOSE 8000

# Stdlib HTTP check so we don't need curl in the slim image.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys;\
r=urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2);\
sys.exit(0 if r.status==200 else 1)" || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
