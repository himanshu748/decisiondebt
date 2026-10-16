FROM python:3.12-slim
ARG DD_COMMIT=unknown
LABEL org.opencontainers.image.source="https://github.com/himanshu748/decisiondebt"
LABEL org.opencontainers.image.revision=$DD_COMMIT
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DD_MODE=public-readonly
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home app
COPY backend/app backend/app
COPY data/synthetic data/synthetic
COPY tools/ingest.py tools/ingest.py
COPY tools/public_snapshot.py tools/public_snapshot.py
COPY web/dist web/dist
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD python -c "import json,urllib.request; d=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/health')); assert d['status']=='ok' and d['mode']=='public-readonly' and not d['provider_configured']"
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-proxy-headers", "--limit-concurrency", "32", "--timeout-keep-alive", "5"]
