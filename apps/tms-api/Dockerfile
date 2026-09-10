FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for blazing-fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project definition and install dependencies
COPY pyproject.toml README.md ./
RUN uv pip install --system -r <(uv pip compile pyproject.toml)

# Copy application source and migration config
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

EXPOSE 8000

# Render dynamic PORT execution
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
