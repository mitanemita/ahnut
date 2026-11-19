#!/bin/sh
# Первичная настройка чистого сервера Ubuntu 22.04/24.04 (запускать от root один раз):
#   curl -fsSL <ссылка на этот файл> | sh    или    sh scripts/server-setup.sh
set -e
apt-get update
apt-get install -y docker.io docker-compose-v2 git ufw
systemctl enable --now docker
# Наружу открыты только SSH и веб (n8n и база — только внутри Docker)
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
# Ключ для скачивания кода с GitHub (только чтение)
[ -f /root/.ssh/ahnut_deploy ] || ssh-keygen -t ed25519 -N "" -f /root/.ssh/ahnut_deploy -C "ahnut-server"
grep -q ahnut_deploy /root/.ssh/config 2>/dev/null || printf 'Host github.com\n  IdentityFile /root/.ssh/ahnut_deploy\n  StrictHostKeyChecking accept-new\n' >> /root/.ssh/config
echo
echo "Готово. Добавьте этот ключ в GitHub: репозиторий ahnut → Settings → Deploy keys → Add deploy key (без права записи):"
cat /root/.ssh/ahnut_deploy.pub
