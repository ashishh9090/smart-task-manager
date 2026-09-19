#!/bin/sh
set -e

# Wait for PostgreSQL database if configured
if [ -n "$DATABASE_URL" ] && echo "$DATABASE_URL" | grep -q "postgres"; then
    echo "Waiting for PostgreSQL database..."
    
    # Extract host and port from DATABASE_URL
    # Format: postgres://user:pass@host:port/dbname
    DB_HOST=$(echo "$DATABASE_URL" | sed -E 's/.*@([^:]+):([0-9]+).*/\1/')
    DB_PORT=$(echo "$DATABASE_URL" | sed -E 's/.*@([^:]+):([0-9]+).*/\2/')
    
    if [ -z "$DB_PORT" ]; then
        DB_PORT=5432
    fi

    while ! nc -z "$DB_HOST" "$DB_PORT"; do
        sleep 0.5
    done
    echo "PostgreSQL is online and reachable!"
fi

# Run database migrations and collect static files only on web process
if [ "$1" = "gunicorn" ] || [ "$1" = "python" ]; then
    echo "Applying database migrations..."
    python manage.py migrate --noinput
    
    echo "Collecting static assets..."
    python manage.py collectstatic --noinput --clear || true
fi

exec "$@"
