# Запуск на серверах

Два сервера:

| Россия (Hostkey, 2 ГБ) | Нидерланды (сервер второго проекта) |
|---|---|
| сайт, база, фото и музыка, HTTPS для ahnut.ru | браузер самопроверки «Принца» (`check.ahnut.ru`) |
| все персональные данные хранятся здесь | прокси к OpenRouter (`llm.ahnut.ru`), если нужен |

Сайт и база в России — требование 152-ФЗ о хранении. В Нидерланды уходят только скриншоты-проверки «Принца»
(страница открытки с фото) и, если включён прокси, запросы к нейросети — это трансграничная передача, её нужно
указать в уведомлении в Роскомнадзор (Нидерланды — страна с адекватной защитой, в черновике уже есть).

Всё делается один раз; дальнейшие обновления — `./deploy.sh`.

## 1. Сервер и домены

1. Hostkey vm.v2-mini (Россия), образ **Ubuntu 24.04**. Записать IP.
2. reg.ru: ahnut.ru и ахнуть.рф. В DNS обоих доменов — A-записи на IP сервера:
   `ahnut.ru`, `www.ahnut.ru`, `ахнуть.рф`, `www.ахнуть.рф`.
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

## 3. Сервер в Нидерландах

1. В DNS ahnut.ru: A-записи `check.ahnut.ru` и `llm.ahnut.ru` → IP нидерландского сервера.
2. Проверить, свободны ли порты 80/443 (второй проект их не использует, но проверить стоит):
   ```bash
   ss -ltnp | grep -E ':(80|443) '
   ```
   Пусто — всё ок. Если заняты другим веб-сервером — пришлите вывод, подскажу, как добавить туда два адреса.
3. Запуск (рядом со вторым проектом, он не затрагивается):
   ```bash
   git clone -b claude/eager-thompson-w0ub1u git@github.com:mitanemita/ahnut.git /opt/ahnut-nl
   cd /opt/ahnut-nl/deploy/nl
   cp .env.example .env && nano .env   # IP российского сервера, секретный путь: openssl rand -hex 16
   docker compose up -d --build
   ```
   Если у российского сервера есть и IPv6 — впишите в `RU_SERVER_IP` оба адреса через пробел.
4. На российском сервере в `.env`: `PLAYWRIGHT_WS=wss://check.ahnut.ru/<тот же секретный путь>`.
   Если OpenRouter не открывается с российского сервера — ещё `LLM_BASE_URL=https://llm.ahnut.ru/api`.
5. Проверка — командой `check` (раздел 5): строка «Браузер самопроверки: ok». С любого другого IP
   `curl https://check.ahnut.ru/` отвечает 403.

## 4. Что вписать в `.env` (ключи — только сюда, не в чат)

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

## 5. Проверка

```bash
docker compose ps                                  # все сервисы Up, migrate — Exited (0)
docker compose exec web python -m app.admin check  # ЮKassa / OpenRouter / UniOne / браузер: ok
```

Вывод `check` секретов не содержит — его можно прислать в чат. Если OpenRouter недоступен с российского сервера,
`LLM_BASE_URL` переключается на прокси на сервере в Нидерландах (код не меняется).

Потом в браузере: https://ahnut.ru → тестовый заказ → оплата тестовой картой ЮKassa → открытка.

## 6. Обновления

```bash
cd /opt/ahnut && ./deploy.sh
```
