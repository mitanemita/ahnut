#!/bin/sh
# Обновление российского сервера через сервер в Нидерландах (с российского не открывается GitHub).
# Запускать НА СЕРВЕРЕ В НИДЕРЛАНДАХ из папки репозитория:
#   RU_HOST=<IP российского сервера> ./scripts/sync-to-ru.sh
# Что делает: забирает свежий код из GitHub, копирует его на российский сервер (без .env и данных),
# там пересобирает и перезапускает сайт. Настройки (.env) и данные на российском сервере не трогаются.
set -e
: "${RU_HOST:?укажите RU_HOST=<IP российского сервера>}"
KEY="${RU_KEY:-/root/.ssh/to_ru}"
DIR="${RU_DIR:-/opt/ahnut}"
cd "$(dirname "$0")/.."
git pull --ff-only
COMMIT=$(git rev-parse --short HEAD)
ssh -i "$KEY" "root@$RU_HOST" "mkdir -p $DIR"
rsync -az --delete -e "ssh -i $KEY" \
  --exclude .git --exclude .env --exclude 'deploy/nl/.env' --exclude data/ --exclude __pycache__ --exclude .pytest_cache \
  ./ "root@$RU_HOST:$DIR/"
ssh -i "$KEY" "root@$RU_HOST" "cd $DIR && echo $COMMIT > REVISION && \
  if [ ! -f .env ]; then ./scripts/make-env.sh; echo 'Первый запуск: заполните .env и повторите'; exit 0; fi && \
  docker compose up -d --build && docker compose ps"
echo "Российский сервер обновлён до $COMMIT"
