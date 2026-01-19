import sqlite3
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (Application,CommandHandler,MessageHandler,CallbackQueryHandler,filters,ContextTypes)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = ''

# СОЗДАНИЕ БД
def init_db():
    conn = sqlite3.connect('NameUser.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Name (
        id INTEGER PRIMARY KEY,
        Username TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем данные пользователя
    user_id = update.effective_user.id
    username = update.effective_user.username if update.effective_user.username else "Unknown"

    # РАБОТА С БД: открываем, записываем, закрываем
    conn = sqlite3.connect('NameUser.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO Name (id, Username) VALUES (?, ?)', (user_id, username))
    conn.commit()
    conn.close() # Теперь ошибка 'Unresolved reference' исчезнет, так как conn создана выше

    keyboard = [["Продавец", "Покупатель"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"Добро пожаловать, {username}! Выберите действие:",
        reply_markup=reply_markup
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Продавец":
        await update.message.reply_text("Вы выбрали режим продавца")
    elif text == "Покупатель":
        keyboard = [
            [InlineKeyboardButton("📱 Электроника", callback_data="cat_elec")],
            [InlineKeyboardButton("👕 Одежда", callback_data="cat_cloth")],
            [InlineKeyboardButton("🏠 Дом", callback_data="cat_home")]
        ]
        await update.message.reply_text("Выберите категорию товаров:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(f"Вы выбрали: {query.data}")

def main():
    # Создаем приложение (ApplicationBuilder актуален для 2026 года)
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    application.add_handler(CallbackQueryHandler(handle_inline_buttons))

    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
    



