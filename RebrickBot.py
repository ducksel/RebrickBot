from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler

# Функция-обработчик для команды /start
async def start(update: Update, context):
	await update.message.reply_text("Привет, мир! Я бот готов.")  # бот отвечает сообщением

app = ApplicationBuilder().token("BOT_TOKEN").build()       # создание приложения бота с токеном
app.add_handler(CommandHandler("start", start))             # привязываем команду /start к функции
app.run_polling()                                           # запускаем бота (долгий опрос сервера)