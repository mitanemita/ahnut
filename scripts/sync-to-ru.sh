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
SSH="ssh -i $KEY -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -o ServerAliveInterval=15"
cd "$(dirname "$0")/.."
echo "1/4 Забираю код из GitHub…"
git pull --ff-only
COMMIT=$(git rev-parse --short HEAD)
echo "2/4 Проверяю доступ к $RU_HOST…"
$SSH "root@$RU_HOST" "mkdir -p $DIR && command -v rsync >/dev/null || { echo 'На российском сервере нет rsync: apt-get install -y rsync'; exit 1; }"
echo "3/4 Копирую код…"
rsync -az --delete --stats -e "$SSH" \
  --exclude .git --exclude .env --exclude 'deploy/nl/.env' --exclude data/ --exclude __pycache__ --exclude .pytest_cache \
  ./ "root@$RU_HOST:$DIR/"
echo "4/4 Собираю и запускаю сайт на российском сервере (первый раз — 5–10 минут)…"
$SSH "root@$RU_HOST" "cd $DIR && echo $COMMIT > REVISION && \
  if [ ! -f .env ]; then ./scripts/make-env.sh; echo 'Первый запуск: заполните .env и повторите'; exit 0; fi && \
  docker compose up -d --build && docker compose ps"
echo "Российский сервер обновлён до $COMMIT"
