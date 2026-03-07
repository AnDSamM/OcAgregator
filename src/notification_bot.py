import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot_config import BOT_TOKEN


user_prompts = {}

prompt_counter = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие и инструкция"""
    welcome_text = """
Добро пожаловать в бот семантического мониторинга Telegram!

Я помогу вам отслеживать сообщения по интересующим темам.

Доступные команды:
/subscribe <текст> - подписаться на тему
/list - показать мои подписки
/remove <номер> - удалить подписку
/help - подробная инструкция

Пример: /subscribe новости Python
"""
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подробная инструкция"""
    help_text = """
**Подробная инструкция**

    **Как это работает**
1. Вы создаете подписку с описанием темы
2. Бот слушает все сообщения в Telegram
3. При нахождении похожего сообщения - вы получаете уведомление

    **Советы по составлению промптов**
• Будьте конкретны: "Python новости 2024" лучше чем "Python"
• Используйте ключевые слова: "сроки сдачи отчетности"
• Можно искать упоминания компаний: "ООО Ромашка"

    **Примеры хороших промптов**
• упоминания компании ООО "Ромашка"
• сроки сдачи отчетности до 31 декабря
• договоренности о встрече с клиентами
• Python вакансии удаленная работа

    **Если не приходят уведомления**
• Проверьте /list - активны ли подписки
• Уточните промпт - слишком общие запросы могут не сработать
• Сообщения могут быть в каналах, где не состоит бот

    **Команды:**
/start - начало работы
/subscribe - создать подписку
/list - мои подписки
/remove - удалить подписку
/help - эта справка
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание новой подписки"""
    global prompt_counter
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    print(f"DEBUG: context.args = {context.args}")
    print(f"DEBUG: user_id = {user_id}")
    
    prompt = ' '.join(context.args)
    print(f"DEBUG: prompt = '{prompt}'")
    
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
    
    if user_id not in user_prompts:
        user_prompts[user_id] = []
        print(f"DEBUG: создан новый список для user_id {user_id}")
    
    prompt_id = prompt_counter
    prompt_counter += 1
    
    user_prompts[user_id].append({
        "id": prompt_id,
        "text": prompt
    })
    
    print(f"DEBUG: user_prompts = {user_prompts}")
    
    await update.message.reply_text(
        f"Подписка создана!\n\n"
        f"Промпт: {prompt}\n"
        f"ID подписки: {prompt_id}\n\n"
        f"Теперь я буду искать сообщения по этой теме и присылать вам уведомления."
    )
    
    print(f"Новый пользователь {username} ({user_id}) подписался на: {prompt}")

async def list_prompts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все подписки пользователя"""
    user_id = update.effective_user.id
    
    prompts = user_prompts.get(user_id, [])
    
    if not prompts:
        await update.message.reply_text(
            "У вас нет активных подписок.\n"
            "Создайте подписку командой /subscribe ваш_запрос"
        )
        return
    
    text = "Ваши подписки:\n\n"
    for p in prompts:
        text += f"{p['id']}. {p['text']}\n"
    
    text += "\nЧтобы удалить подписку: /remove <номер>"
    
    await update.message.reply_text(text)


async def remove_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить подписку по ID"""
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
    
    prompts = user_prompts.get(user_id, [])
    found = None
    for p in prompts:
        if p['id'] == prompt_id:
            found = p
            break
    
    if not found:
        await update.message.reply_text(
            "Подписка с таким номером не найдена или не принадлежит вам"
        )
        return
    
    user_prompts[user_id] = [p for p in prompts if p['id'] != prompt_id]
    
    await update.message.reply_text(
        f"Подписка удалена:\n"
        f"«{found['text']}»"
    )


async def notify_user(user_id: int, message_text: str, message_link: str):
    """Функция для отправки уведомления пользователю"""
    pass


def main():
    """Запуск бота"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("list", list_prompts))
    app.add_handler(CommandHandler("remove", remove_prompt))
    
    print("Бот для уведомлений запущен!")
    print("Доступные команды: /start, /help, /subscribe, /list, /remove")
    app.run_polling()


if __name__ == '__main__':
    main()