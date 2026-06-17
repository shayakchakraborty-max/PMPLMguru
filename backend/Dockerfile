# Backend "brain" — deterministic consulting engine (Python http.server).
# Build context = backend/ . Runs on AWS App Runner / ECS Fargate.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    BRAIN_DATA_DIR=/data

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# /data for the JSONL fallback stores (mount EFS for persistence, or set DATABASE_URL).
RUN useradd -m appuser && mkdir -p /data && chown -R appuser /app /data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/health',timeout=4).status==200 else 1)"

# main.py binds 0.0.0.0:$PORT (ThreadingHTTPServer).
CMD ["python", "main.py"]
