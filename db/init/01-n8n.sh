#!/bin/sh
# Отдельная база и пользователь для n8n в том же Postgres (выполняется один раз при создании тома)
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
CREATE USER n8n WITH PASSWORD '${N8N_DB_PASSWORD}';
CREATE DATABASE n8n OWNER n8n;
SQL
