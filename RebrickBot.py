import os
import re
from telegram import Update
from telegram.ext import (
	ApplicationBuilder,
	CommandHandler,
	MessageHandler,
	ContextTypes,
	filters
)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user = update.effective_user
	print(f"/start от {user.username or user.id}")
	await update.message.reply_text("Привет! Отправь мне LEGO-код (4 или 5 цифр), и я попробую найти набор.")

# Обработчик текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
	text = update.message.text.strip()
	user = update.effective_user
	print(f"Текст от {user.username or user.id}: {text}")

	if re.fullmatch(r"\d{4,5}", text):
		await update.message.reply_text(f"✅ Похоже, это валидный LEGO код: {text}")
		# Здесь можно будет подгрузить данные с Rebrickable
	else:
		await update.message.reply_text("❌ Это не похоже на LEGO код. Введи 4 или 5 цифр.")

# Инициализация приложения
app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()

# Регистрация обработчиков
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# Запуск
app.run_polling()