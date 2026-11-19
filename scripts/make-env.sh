#!/bin/sh
# Создаёт .env из .env.example и сам заполняет все внутренние пароли и ключи случайными значениями.
# Ключи внешних сервисов (ЮKassa, OpenRouter, UniOne) вписываются потом вручную.
set -e
cd "$(dirname "$0")/.."
[ -f .env ] && { echo ".env уже есть — не трогаю"; exit 0; }
cp .env.example .env
for k in DB_PASSWORD N8N_DB_PASSWORD N8N_ENCRYPTION_KEY INTERNAL_TOKEN SECRET_KEY; do
  sed -i "s|^$k=.*|$k=$(openssl rand -hex 24)|" .env
done
chmod 600 .env
echo "Создан .env. Впишите: ACME_EMAIL, YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, LLM_API_KEY, UNIONE_API_KEY, ADMIN_EMAIL, SUPPORT_EMAIL"
