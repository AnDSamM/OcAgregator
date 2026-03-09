import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN, YC_FOLDER_ID, YC_API_KEY
from yandex_semantic import YandexSemanticSearch

try:
    semantic_search = YandexSemanticSearch(
        folder_id=YC_FOLDER_ID,
        api_key=YC_API_KEY
    )
    print("Семантический поиск инициализирован")
    
    existing_prompts = semantic_search.get_all_prompts()
    if existing_prompts:
        print(f"Загружено {len(existing_prompts)} промптов из хранилища")
        
except Exception as e:
    print(f"Ошибка инициализации семантического поиска: {e}")
    semantic_search = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
Добро пожаловать в бот семантического мониторинга Telegram!

Доступные команды:
/subscribe <текст> - подписаться на тему
/list - показать мои подписки
/remove <номер> - удалить подписку
/help - подробная инструкция

Пример: /subscribe новости Python
"""
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
Подробная инструкция

Как это работает:
1. Вы создаете подписку с описанием темы
2. Бот слушает все сообщения в Telegram
3. При нахождении похожего сообщения - вы получаете уведомление

Команды:
/start - начало работы
/subscribe - создать подписку
/list - мои подписки
/remove - удалить подписку
/help - эта справка
"""
    await update.message.reply_text(help_text)


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    prompt = ' '.join(context.args)
    
    if not prompt:
        await update.message.reply_text(
            "Ошибка: не указан текст подписки\n"
            "Использование: /subscribe ваш поисковый запрос"
        )
        return
    
    if len(prompt) > 500:
        await update.message.reply_text(
            "Ошибка: промпт слишком длинный (максимум 500 символов)"
        )
        return
    
    if semantic_search:
        prompt_id = semantic_search.add_prompt(user_id, prompt)
        
        all_prompts = semantic_search.get_all_prompts()
        print(f"Текущее количество промптов в индексе: {len(all_prompts)}")
        
        await update.message.reply_text(
            f"Подписка создана!\n\n"
            f"Промпт: {prompt}\n"
            f"ID подписки: {prompt_id}\n\n"
            f"Теперь я буду искать сообщения по этой теме и присылать вам уведомления."
        )
        
        print(f"Новый пользователь {username} ({user_id}) подписался на: {prompt} (ID: {prompt_id})")
    else:
        await update.message.reply_text("Ошибка: семантический поиск не инициализирован")


async def list_prompts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not semantic_search:
        await update.message.reply_text("Ошибка: семантический поиск не инициализирован")
        return
    
    prompts = semantic_search.get_user_prompts(user_id)
    
    if not prompts:
        await update.message.reply_text(
            "У вас нет активных подписок.\n"
            "Создайте подписку командой /subscribe ваш_запрос"
        )
        return
    
    prompts.sort(key=lambda x: x['id'])
    
    text = "Ваши подписки:\n\n"
    for p in prompts:
        text += f"{p['id']}. {p['text']}\n"
    
    text += "\nЧтобы удалить подписку: /remove <номер>"
    
    await update.message.reply_text(text)


async def remove_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "Укажите номер подписки для удаления\n"
            "Пример: /remove 1"
        )
        return
    
    try:
        prompt_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Номер подписки должен быть числом")
        return
    
    if not semantic_search:
        await update.message.reply_text("Ошибка: семантический поиск не инициализирован")
        return
    
    user_prompts = semantic_search.get_user_prompts(user_id)
    prompt_exists = any(p['id'] == prompt_id for p in user_prompts)
    
    if not prompt_exists:
        await update.message.reply_text(
            "Подписка с таким номером не найдена или не принадлежит вам"
        )
        return
    
    removed = semantic_search.remove_prompt_by_id(prompt_id)
    
    if removed:
        await update.message.reply_text(
            f"Подписка удалена:\n"
            f"«{removed[1]}»"
        )
        print(f"Удален промпт ID {prompt_id}: {removed[1]}")
    else:
        await update.message.reply_text("Ошибка при удалении подписки")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("list", list_prompts))
    app.add_handler(CommandHandler("remove", remove_prompt))
    
    print("=" * 50)
    print("БОТ ДЛЯ УВЕДОМЛЕНИЙ ЗАПУЩЕН")
    print("=" * 50)
    print("Загруженные промпты:")
    
    if semantic_search:
        all_prompts = semantic_search.get_all_prompts()
        if all_prompts:
            sorted_prompts = sorted(all_prompts, key=lambda x: x[2])
            for uid, text, pid in sorted_prompts:
                print(f"   [ID: {pid}] User {uid}: {text}")
        else:
            print("   Нет загруженных промптов")
    else:
        print("   Семантический поиск не инициализирован")
    
    print("=" * 50)
    print("Доступные команды:")
    print("  /start - приветствие")
    print("  /help - инструкция")
    print("  /subscribe - создать подписку")
    print("  /list - список подписок")
    print("  /remove - удалить подписку")
    print("=" * 50)
    
    app.run_polling()


if __name__ == '__main__':
    main()