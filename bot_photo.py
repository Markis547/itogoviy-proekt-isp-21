import telegram.ext
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes
import os
TOKEN = '8582184651:AAH45iNf6IPtqP7mjxEOKW6us8mQAD0NCyY'
from telegram import Bot
bot = Bot(token=TOKEN)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(context.args)
    if not update.message or not update.message.photo:
        return
    file_id = update.message.photo[-1].file_id
    new_file = await context.bot.get_file(file_id)
    print(context.args)
    destination_folder = 'images'
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    file_name = f"{file_id}.jpg"
    destination_path = os.path.join(destination_folder, file_name)

    try:
        await new_file.download_to_drive(custom_path=destination_path)
        # Также используем await для отправки ответа
        await update.message.reply_text("Фотография успешно получена и сохранена!")
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при скачивании файла: {e}")
async def Himessage(update, context):
    user_id = update.effective_chat.id

    # Мы отвечаем в тот же чат, откуда пришло сообщение
    await context.bot.send_message(
        chat_id=user_id, 
        text="Я получил ваше сообщение!"
    )

def main():
    
    application = Application.builder().token(TOKEN).build()
    photo_handler = MessageHandler(telegram.ext.filters.PHOTO, handle_photo)
    application.add_handler(photo_handler)

    # 4. Запускаем бота
    application.run_polling(
        poll_interval=3, 
        on_startup=Himessage # <- Вот здесь мы вызываем функцию при старте
    )

if __name__ == '__main__':
    main()
