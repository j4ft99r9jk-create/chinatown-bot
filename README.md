# Chinatown Bot — Deploy Guide

## Railway ENV Variables

| Переменная     | Что ставить                          |
|----------------|--------------------------------------|
| BOT_TOKEN      | Токен от @BotFather                  |
| LAVA_TOP_URL   | Ссылка на оплату из кабинета Lava    |
| LAVA_SECRET    | Секрет вебхука из кабинета Lava      |
| VIP_CHANNEL    | ID закрытого канала (с минусом -100…)|
| ADMIN_ID       | Твой Telegram ID                     |
| VIP_PRICE      | Строка цены для отображения (2 990)  |
| LINK_CARGO     | Ссылка на топик/канал Карго          |
| LINK_BUYERS    | Ссылка на топик/канал Байеры         |
| LINK_SUPPLIERS | Ссылка на топик Поставщики           |
| LINK_EXCHANGE  | Ссылка на топик Обмен                |
| LINK_VISAS     | Ссылка на топик Визы                 |
| LINK_HOTELS    | Ссылка на топик Отели                |
| LINK_FOOD      | Ссылка на топик Еда                  |
| LINK_ESIM      | Ссылка на топик eSIM                 |
| LINK_ROUTES    | Ссылка на топик Маршруты             |
| LINK_JOBS      | Ссылка на топик Работа               |
| LINK_COMMUNITY | Ссылка на общий чат                  |
| LINK_SUPPORT   | Username поддержки (@chinatown_sup)  |

## Start Command в Railway
```
python main.py
```

## Lava.top Webhook URL
```
https://ВАШ_RAILWAY_URL/webhook/lava
```

## Команды бота (для админа)
- `/confirm USER_ID` — вручную выдать VIP (если вебхук не пришёл)
- `/revoke USER_ID`  — отозвать VIP
- `/stats`           — статистика пользователей

## Как добавить бота в закрытый канал
1. Добавь бота в канал как администратора
2. Дай права: Invite Users, Ban Users
3. Скопируй ID канала (через @userinfobot или из ссылки)
