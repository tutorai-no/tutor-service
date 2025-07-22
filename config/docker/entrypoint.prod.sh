#!/bin/bash
set -e

echo "Starting Aksio Backend in production mode..."

# Run migrations (Cloud Run will handle this on deployment)
echo "Running database migrations..."
python manage.py migrate --noinput

# Start Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn aksio.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers ${GUNICORN_WORKERS:-2} \
    --threads ${GUNICORN_THREADS:-4} \
    --timeout ${GUNICORN_TIMEOUT:-0} \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL:-info}