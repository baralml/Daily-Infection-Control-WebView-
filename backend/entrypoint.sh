#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Waiting for PostgreSQL database to start..."
# We run a simple python script to check if the DB is available before running migrations
python -c "
import time
import psycopg2
from app.core.config import settings

# Parse connection params from DATABASE_URL
url = settings.DATABASE_URL
# Strip the dialect driver prefix if present
if url.startswith('postgresql+psycopg2://'):
    url = url.replace('postgresql+psycopg2://', 'postgresql://')

print('Connecting to:', url)

retries = 10
while retries > 0:
    try:
        conn = psycopg2.connect(url)
        conn.close()
        print('PostgreSQL is up and accepting connections.')
        break
    except Exception as err:
        print('DB not ready yet. Retrying in 2 seconds...', err)
        retries -= 1
        time.sleep(2)
"

echo "Running Alembic Database Migrations..."
alembic upgrade head

echo "Starting FastAPI Application..."
exec "$@"
