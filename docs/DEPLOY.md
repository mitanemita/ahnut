# Запуск на сервере

Всё делается один раз; дальнейшие обновления — `./deploy.sh`.

## 1. Сервер и домены

1. Hostkey vm.v2-mini (Россия), образ **Ubuntu 24.04**. Записать IP.
2. reg.ru: ahnut.ru и ахнуть.рф. В DNS обоих доменов — A-записи на IP сервера:
   `ahnut.ru`, `www.ahnut.ru`, `n8n.ahnut.ru`, `ахнуть.рф`, `www.ахнуть.рф`.
   Плюс записи UniOne для ahnut.ru (DKIM, SPF, домен для трекинга) — UniOne покажет их сам.

## 2. Подготовка сервера

```bash
ssh root@<IP>
apt-get update && apt-get install -y git
git clone https://github.com/mitanemita/ahnut.git /tmp/ahnut-setup 2>/dev/null || true
```

Если репозиторий приватный, сначала выполните `scripts/server-setup.sh` (скопировать текст файла на сервер
и запустить `sh server-setup.sh`) — он поставит Docker, включит файрвол и покажет ключ для GitHub
(Settings → Deploy keys → Add, без права записи). Затем:

```bash
git clone -b claude/eager-thompson-w0ub1u git@github.com:mitanemita/ahnut.git /opt/ahnut
cd /opt/ahnut
./scripts/make-env.sh        # создаст .env и сам заполнит внутренние пароли
nano .env                    # вписать ключи (список ниже)
./deploy.sh
```

## 3. Что вписать в `.env` (ключи — только сюда, не в чат)

| Переменная | Где взять |
|---|---|
| `ACME_EMAIL` | ваша почта — для писем Let's Encrypt о сертификатах |
| `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY` | ЮKassa → Интеграция → Ключи API. Сначала **тестовый магазин** |
| `LLM_API_KEY` | OpenRouter → Keys (на балансе $10–20 для тестов) |
| `UNIONE_API_KEY` | UniOne → Настройки → API-ключ |
| `ADMIN_EMAIL` | куда слать сообщения о сбоях генерации |
| `SUPPORT_EMAIL` | ящик для пользователей и жалоб правообладателей (публикуется в оферте) |

В ЮKassa → Интеграция → HTTP-уведомления: адрес `https://ahnut.ru/yookassa/webhook`,
события `payment.succeeded`, `payment.canceled`.

## 4. Проверка

```bash
docker compose ps                                  # все сервисы Up, migrate — Exited (0)
docker compose exec web python -m app.admin check  # ЮKassa / OpenRouter / UniOne: ok
```

Вывод `check` секретов не содержит — его можно прислать в чат. Если OpenRouter недоступен с российского сервера,
`LLM_BASE_URL` переключается на прокси на сервере в Нидерландах (код не меняется).

Потом в браузере: https://ahnut.ru → тестовый заказ → оплата тестовой картой ЮKassa → открытка.

## 5. Обновления

```bash
cd /opt/ahnut && ./deploy.sh
```
