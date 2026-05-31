# Root-level Dockerfile so Railway/any platform builds the Python brain correctly
# even when the service Root Directory is left at the repo root.
# Build context = repo root; we copy only backend/.
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE 8000
# main.py binds 0.0.0.0:$PORT (falls back to 8000)
CMD ["python", "main.py"]
