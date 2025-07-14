from telegram.ext import Application, CommandHandler, CallbackQueryHandler,ConversationHandler, ContextTypes
from handlers.start import  start, cancel, CHOOSING_ROLE, choose_role_callback, handle_inline_buttons
from handlers.department import get_department_handlers, get_admin_reply_handler
from handlers.career_test import get_career_test_handler
import logging
from handlers.admin import get_admin_handlers
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)
import json
import os
  # Импортируем обработчик расписания отделов

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

token = 
def load_user_data_from_file():
    global user_data
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
    except FileNotFoundError:
        user_data = {}

def save_user_data_to_file():
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)

def set_user_role(user_id, role):
    user_data[str(user_id)] = user_data.get(str(user_id), {})
    user_data[str(user_id)]['role'] = role
    save_user_data_to_file()
    load_user_data_from_file()  # сразу обновить user_data из файла (если нужна)
def get_user_role(user_id):
    role = user_data.get(str(user_id), {}).get('role', 'abit')
    # Защита от некорректных значений
    return role if role in ('abit', 'student') else 'student'
# === main ===
USERS_FILE = "users.json"


user_data = {}
if __name__ == "__main__":
    load_user_data_from_file()

    app = ApplicationBuilder().token(token).build()  # создаем приложение

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ROLE: [
                CallbackQueryHandler(choose_role_callback, pattern="^role_.*"),
                # Добавляем обработчик для кнопки change_role
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_inline_buttons))  # обработка всех остальных кнопок

    app.run_polling()  # запускаем бота

USERS_FILE = "users.json"



if __name__ == "__main__":
    main()
