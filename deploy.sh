#!/bin/sh
# Обновление на сервере: ./deploy.sh
set -e
cd "$(dirname "$0")"
[ -f .env ] || { echo "Нет .env — скопируйте .env.example и заполните"; exit 1; }
git pull --ff-only
docker compose up -d --build
docker compose ps
