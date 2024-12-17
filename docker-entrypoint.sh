#!/bin/sh

echo "Make database migrations"
alembic upgrade head

echo "Starting server"
gunicorn -w 3 wsgi:app -b unix:/app/socket/wsgi.socket