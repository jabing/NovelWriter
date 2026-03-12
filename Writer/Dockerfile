# Dockerfile for Novel Writing Agent System
# Production deployment image

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -e .

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/novels /app/data/memory /app/backups /app/logs && \
    chown -R app:app /app

# Switch to app user
USER app

# Expose port (if needed for future web interface)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.monitoring import get_health_monitor; import asyncio; asyncio.run(get_health_monitor().run_all_checks())" || exit 1

# Default command
CMD ["python", "-m", "src.main", "--mode", "production"]
