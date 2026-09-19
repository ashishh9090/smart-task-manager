# Multi-stage optimized Dockerfile for Smart Task Manager
FROM python:3.12-slim

# Prevent Python from writing .pyc files & enable unbuffered standard output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system runtime & build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/production.txt

# Copy application source code
COPY . /app/

# Create media and static directories and configure non-root user
RUN mkdir -p /app/media /app/staticfiles && \
    chmod +x /app/entrypoint.sh && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "config.wsgi:application"]
