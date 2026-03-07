import asyncio
import logging
from pyrogram import Client, types
from config import API_ID, API_HASH, PHONE_NUMBER

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)

app = Client(
    "OcAgregator",
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=PHONE_NUMBER,
    device_model="PC",
    system_version="Linux",
    app_version="1.0",
    lang_code="ru",
    workdir="./sessions",
)


@app.on_message()
async def handle_new_message(client: Client, message: types.Message):
    """Обработчик новых сообщений"""
    try:
        chat_id = message.chat.id
        message_id = message.id
        
        if message.text:
            text = message.text
        elif message.caption:
            text = message.caption
        else:
            text = f"[{message.content_type}]"
        
        print(f"Новое сообщение [ID: {message_id}] в чате {chat_id}:")
        print(f"Текст: {text[:200]}{'...' if len(text) > 200 else ''}")
        print(f"От: {message.from_user.first_name if message.from_user else 'Unknown'}")
        print("-" * 60)
        
    except Exception as e:
        print(f"Ошибка при обработке сообщения: {e}")


async def main():
    try:
        print("=" * 60)
        print("ЗАПУСК КЛИЕНТА TELEGRAM (Pyrogram)")
        print("=" * 60)
        print(f"Номер телефона: {PHONE_NUMBER}")
        print("=" * 60)
        
        print("Подключение к Telegram...")
        
        
        await app.start()
        
      
        me = await app.get_me()
        print(f"Авторизован как {me.first_name}!")
        print(f"Клиент {me.first_name} (ID: {me.id}) запущен и слушает сообщения!")
        print("Ожидание новых сообщений... (нажмите Ctrl+C для остановки)")
        
        
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        print("\n\nОстановка клиента...")
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if app.is_connected:
            try:
                await app.stop()
                print("Соединение закрыто")
            except:
                pass


if __name__ == '__main__':
    asyncio.run(main())