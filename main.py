from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes
)
from handlers.start import start, cancel, CHOOSING_ROLE, choose_role_callback, handle_inline_buttons
import logging
import json
import os
from conf import token

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальные переменные
USERS_FILE = "users.json"
user_data = {}

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

def get_user_role(user_id):
    role = user_data.get(str(user_id), {}).get('role', 'abit')
    return role if role in ('abit', 'student') else 'student'

def main():
    load_user_data_from_file()

    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ROLE: [
                CallbackQueryHandler(choose_role_callback, pattern="^role_.*"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_inline_buttons))
    
    app.run_polling()

if __name__ == "__main__":
    main()
