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

# Copy project definition and lock file
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using uv sync
RUN uv sync --no-dev --frozen

# Copy application source and migration config
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

EXPOSE 8000

# Run the app from the virtual environment
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
