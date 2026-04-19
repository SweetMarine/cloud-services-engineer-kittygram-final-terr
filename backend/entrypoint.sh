#!/bin/bash

echo "Waiting for postgres..."
sleep 5

echo "Applying migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
gunicorn kittygram_backend.wsgi:application --bind 0.0.0.0:8000 