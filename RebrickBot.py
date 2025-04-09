import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler

# Функция-обработчик для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user = update.effective_user
	print(f"/start от {user.username or user.id}")
	await update.message.reply_text("Привет, мир! Я бот готов.")  # бот отвечает сообщением

# Функция-обработчик для текстовой команды от пользователя
async def handle_text(update: Update, context):
	text = update.message.text
	print(f"Пользователь прислал: {text}")
	

app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()       # создание приложения бота с токеном
app.add_handler(CommandHandler("start", start))             # привязываем команду /start к функции
app.run_polling()                                           # запускаем бота (долгий опрос сервера)
