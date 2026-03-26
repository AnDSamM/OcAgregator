# OcAgregator - Агрегатор переписок в Telegram для обработки большого потока писем и поиск писем по промпту

Система для сбора сообщений из Telegram и семантического поиска по промптам пользователей на базе Yandex Cloud.

## Функциональность

- Сбор сообщений из Telegram через пользовательский аккаунт (Telethon)
- Семантический поиск через YandexGPT Embeddings
- Telegram Bot для управления подписками
- Векторный поиск через FAISS
- Свои сообщения и от бота не обрабатываются 

## Установка

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```


## Пример файла .env

```bash
# Telegram API credentials (получены на my.telegram.org)
API_ID=123456
API_HASH=your_api_hash_here
PHONE_NUMBER=+791234567890

# Telegram Bot token (получен от @BotFather)
BOT_TOKEN=1234567890:xxxxxxxxxxxxxxxxxxxxxx

# Yandex Cloud credentials (получены в Yandex Cloud)
YC_FOLDER_ID=your_YC_FOLDER_ID
YC_API_KEY=your_YC_API_KEY
```


## Настройка переменных окружения

Скопируйте пример переменных и вставьте в свой файл .env

## Запуск

1) Запускаем файл telegram_listener.py

```bash
python src/telegram_listener.py
```

2) Запускаем файл notification_bot.py

```bash
python src/notification_bot.py
```

## Команды бота

/start - Приветствие;  
/help - Подробная инструкция;  
/subscribe <текст> - Подписаться на тему;  
/list - Показать мои подписки;  
/remove <номер> - Удалить подписку;  

## Как это работает

1) Пользователь создаёт подписку через бота с помощью команды /subscribe

2) Слушатель получает все сообщения из Telegram через пользовательский аккаунт

3) Для каждого сообщения выполняется семантический поиск среди всех промптов пользователей

4) Если найдено совпадение, бот отправляет пользователю ссылку на сообщение

5) Сообщения от самого аккаунта и от бота игнорируются

## Требования

- Python 3.9+

- Активный аккаунт Telegram

- Аккаунт Yandex Cloud с включённым API YandexGPT

- Telegram Bot (создаётся через @BotFather)