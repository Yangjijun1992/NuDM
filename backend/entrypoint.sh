#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding initial data..."
python seed.py

echo "Starting FastAPI..."
exec "$@"