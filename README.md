# OcAgregator - Telegram Semantic Monitor

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


