#!/bin/sh
# Обновление российского сервера через сервер в Нидерландах (с российского не открывается GitHub).
# Запускать НА СЕРВЕРЕ В НИДЕРЛАНДАХ из папки репозитория:
#   RU_HOST=<IP российского сервера> ./scripts/sync-to-ru.sh
# Связь «Нидерланды → Россия» по SSH бывает нестабильной, поэтому каждое действие повторяется до 5 раз,
# копирование докачивается, а сборка запускается на российском сервере в фоне (обрыв SSH её не прерывает).
# Настройки (.env) и данные на российском сервере не трогаются.
set -e
: "${RU_HOST:?укажите RU_HOST=<IP российского сервера>}"
KEY="${RU_KEY:-/root/.ssh/to_ru}"
DIR="${RU_DIR:-/opt/ahnut}"
SSH="ssh -i $KEY -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 -o ServerAliveInterval=10 -o ServerAliveCountMax=3"

retry() {  # retry <описание> <команда…>
  what="$1"; shift
  for n in 1 2 3 4 5; do
    if "$@"; then return 0; fi
    echo "   …не вышло ($what), попытка $n из 5, жду 10 с"; sleep 10
  done
  echo "Не удалось: $what. Связь между серверами нестабильна — попробуйте позже или запустите скрипт со своего компьютера (docs/DEPLOY.md)."
  exit 1
}

cd "$(dirname "$0")/.."
echo "1/4 Забираю код из GitHub…"
git pull --ff-only
COMMIT=$(git rev-parse --short HEAD)

echo "2/4 Проверяю доступ к $RU_HOST…"
retry "подключение" $SSH "root@$RU_HOST" "mkdir -p $DIR && command -v rsync >/dev/null || { echo 'На российском сервере нет rsync: apt-get install -y rsync'; exit 1; }"

echo "3/4 Копирую код…"
retry "копирование" rsync -az --partial --delete --timeout=60 -e "$SSH" \
  --exclude .git --exclude .env --exclude 'deploy/nl/.env' --exclude data/ --exclude __pycache__ --exclude .pytest_cache \
  ./ "root@$RU_HOST:$DIR/"

echo "4/4 Запускаю сборку на российском сервере (в фоне)…"
retry "запуск сборки" $SSH "root@$RU_HOST" "cd $DIR && echo $COMMIT > REVISION && \
  if [ ! -f .env ]; then ./scripts/make-env.sh; echo 'ПЕРВЫЙ ЗАПУСК: заполните $DIR/.env на российском сервере и запустите этот скрипт ещё раз'; exit 0; fi && \
  nohup sh -c 'docker compose up -d --build && docker compose ps' > $DIR/deploy.log 2>&1 &
  echo 'Сборка идёт. Следить на российском сервере: tail -f $DIR/deploy.log'"
echo "Код $COMMIT передан."
