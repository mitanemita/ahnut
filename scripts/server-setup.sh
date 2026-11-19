#!/bin/sh
# Первичная настройка чистого сервера Ubuntu 22.04/24.04 (запускать от root один раз):
#   curl -fsSL <ссылка на этот файл> | sh    или    sh scripts/server-setup.sh
set -e
apt-get update
apt-get install -y docker.io docker-compose-v2 git ufw
systemctl enable --now docker
# На сервере с 2–4 ГБ памяти — файл подкачки 2 ГБ, чтобы сборка образов и браузер самопроверки не упирались в память
if [ "$(awk '/MemTotal/{print int($2/1024/1024)}' /proc/meminfo)" -lt 4 ] && ! swapon --show | grep -q swapfile; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  sysctl -w vm.swappiness=10 && echo 'vm.swappiness=10' > /etc/sysctl.d/99-ahnut.conf
fi
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
