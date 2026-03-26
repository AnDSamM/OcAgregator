import asyncio
import logging
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon import functions, types
from yandex_semantic import YandexSemanticSearch
import requests

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
YC_FOLDER_ID = os.getenv('YC_FOLDER_ID')
YC_API_KEY = os.getenv('YC_API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')

logging.getLogger("telethon").setLevel(logging.ERROR)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

os.makedirs("./sessions", exist_ok=True)

client = TelegramClient(
    session='./sessions/OcAgregator',
    api_id=API_ID,
    api_hash=API_HASH,
    connection_retries=10,
    retry_delay=2,
    timeout=30,
    device_model="PC",
    system_version="Linux",
    app_version="1.0",
    lang_code="ru",
    system_lang_code="ru",
    sequential_updates=True,
    flood_sleep_threshold=60,
    request_retries=5,
    auto_reconnect=True,
)

try:
    semantic_search = YandexSemanticSearch(
        folder_id=YC_FOLDER_ID,
        api_key=YC_API_KEY
    )
    print("Семантический поиск инициализирован")
    
    if hasattr(semantic_search, 'prompts_metadata') and semantic_search.prompts_metadata:
        print(f"\nЗАГРУЖЕННЫЕ ПРОМПТЫ ({len(semantic_search.prompts_metadata)}):")
        for i, (user_id, prompt_text, prompt_id) in enumerate(semantic_search.prompts_metadata, 1):
            print(f"   {i}. [ID: {prompt_id}] User {user_id}: {prompt_text}")
        print("")
    else:
        print("Нет загруженных промптов\n")
        
except Exception as e:
    print(f"Ошибка инициализации семантического поиска: {e}")
    semantic_search = None


async def send_notification(user_id: int, message_text: str, chat_id: int, message_id: int, prompt: str):
    if str(chat_id).startswith('-100'):
        chat_part = str(chat_id)[4:]
        message_link = f"https://t.me/c/{chat_part}/{message_id}"
    elif chat_id < 0:
        message_link = f"https://t.me/c/{str(chat_id)[1:]}/{message_id}"
    else:
        try:
            user_entity = await client.get_entity(chat_id)
            if user_entity.username:
                message_link = f"https://t.me/{user_entity.username}"
            else:
                message_link = f"tg://user?id={chat_id}"
        except:
            message_link = f"tg://user?id={chat_id}"
    
    text = (
        f"Найдено сообщение по вашей подписке\n\n"
        f"Промпт: {prompt}\n\n"
        f"Сообщение:\n{message_text[:200]}...\n\n"
        f"Ссылка: {message_link}"
    )
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': user_id,
        'text': text,
        'disable_web_page_preview': True
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"   Уведомление отправлено пользователю {user_id}")
        else:
            print(f"   Ошибка отправки: {response.text}")
    except Exception as e:
        print(f"   Ошибка: {e}")


@client.on(events.NewMessage)
async def normal_handler(event):
    try:
        message = event.message
        if not message.text:
            return
        
        if not hasattr(normal_handler, "my_id"):
            me = await client.get_me()
            normal_handler.my_id = me.id
            print(f"Мой ID: {normal_handler.my_id}")
        
        if message.sender_id == normal_handler.my_id:
            return
        
        if message.sender_id:
            try:
                user = await event.get_sender()
                if user:
                    sender_name = getattr(user, 'first_name', '') or getattr(user, 'title', '')
                    
                    if "OcAgregator" in sender_name:
                        return
            except Exception:
                pass
        
        if "Найдено сообщение по вашей подписке" in message.text:
            return
        
        sender = "Аноним/Канал"
        if message.sender_id:
            try:
                user = await event.get_sender()
                if user:
                    sender = getattr(user, 'first_name', '') or getattr(user, 'title', 'Неизвестно')
            except Exception:
                pass
        
        chat_type = ""
        if message.is_private:
            chat_type = "Личное"
        elif message.is_group:
            chat_type = "Группа"
        elif message.is_channel:
            chat_type = "Канал"
        
        time = datetime.now().strftime('%H:%M:%S')
        print(f"\n{chat_type} | {time}")
        print(f"От: {sender}")
        print(f"Сообщение: {message.text}")
        
        if semantic_search:
            try:
                matches = semantic_search.search(
                    message_text=message.text,
                    threshold=0.3
                )
                
                if matches:
                    print(f"НАЙДЕНЫ СОВПАДЕНИЯ:")
                    
                    notified_users = set()
                    
                    for match in matches:
                        similarity = match['similarity']
                        prompt_text = match['prompt'].lower()
                        message_lower = message.text.lower()
                        
                        if prompt_text in message_lower:
                            print(f"   Промпт найден в тексте")
                            is_valid = True
                        else:
                            prompt_words = prompt_text.split()
                            found = False
                            for word in prompt_words:
                                if len(word) > 2 and word in message_lower:
                                    found = True
                                    print(f"   Слово '{word}' найдено в тексте")
                                    break
                            
                            if not found:
                                for word in prompt_words:
                                    if len(word) < 4:
                                        continue
                                    root = word[:4]
                                    message_words = message_lower.split()
                                    for msg_word in message_words:
                                        if msg_word.startswith(root) or root in msg_word:
                                            found = True
                                            print(f"   Корень '{root}' найден в слове '{msg_word}'")
                                            break
                                    if found:
                                        break
                            
                            is_valid = found
                        
                        if is_valid:
                            bar = "█" * int(similarity * 10) + "░" * (10 - int(similarity * 10))
                            print(f"   {match['prompt']} (сходство: {similarity:.2f} {bar})")
                            
                            if match['user_id'] not in notified_users:
                                await send_notification(
                                    user_id=match['user_id'],
                                    message_text=message.text,
                                    chat_id=message.chat_id,
                                    message_id=message.id,
                                    prompt=match['prompt']
                                )
                                notified_users.add(match['user_id'])
                        else:
                            print(f"   Отклонено: '{match['prompt']}'")
                            
            except Exception as e:
                print(f"   Ошибка поиска: {e}")
        
        print("-" * 50)
                
    except Exception as e:
        print(f"Ошибка: {e}")


async def main():
    try:
        print("=" * 50)
        print("ЗАПУСК МОНИТОРИНГА TELEGRAM (Telethon)")
        print("=" * 50)
        print(f"Номер: {PHONE_NUMBER}")
        print(f"Yandex: {'Да' if semantic_search else 'Нет'}")
        print("=" * 50)
        
        print("Подключение...")
        
        await client.connect()
        print("Клиент подключен к серверам Telegram")
        
        if not await client.is_user_authorized():
            print("Запрос кода подтверждения...")
            
            try:
                result = await client(functions.auth.SendCodeRequest(
                    phone_number=PHONE_NUMBER,
                    api_id=API_ID,
                    api_hash=API_HASH,
                    settings=types.CodeSettings()
                ))
                
                print("Код отправлен на телефон")
                print("Проверьте Telegram в приложении на телефоне")
                
                code = input("Введите код из Telegram: ").strip()
                
                try:
                    await client.sign_in(
                        phone=PHONE_NUMBER, 
                        code=code, 
                        phone_code_hash=result.phone_code_hash
                    )
                    print("Успешный вход!")
                except Exception as e:
                    if "SESSION_PASSWORD_NEEDED" in str(e):
                        print("Требуется двухфакторная аутентификация")
                        password = input("Введите пароль 2FA: ").strip()
                        await client.sign_in(password=password)
                        print("Успешный вход с 2FA!")
                    else:
                        raise e
                        
            except Exception as e:
                print(f"Ошибка при запросе кода: {e}")
                raise
        else:
            print("Уже авторизован")
        
        me = await client.get_me()
        print(f"Аккаунт: {me.first_name}")
        print("=" * 50)
        print("Ожидание сообщений...")
        print("Отправьте тестовое сообщение")
        print("=" * 50)
        
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        print("\nОстановлено")
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client.is_connected():
            await client.disconnect()
            print("Соединение закрыто")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПрограмма завершена")