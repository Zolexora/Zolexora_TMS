# Optional: Render's native Python runtime (see render.yaml) does not need
# this file. Use it if you'd rather deploy as a container (Render, Fly.io,
# Cloud Run, etc.) instead of Render's buildpack-style Python runtime.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
