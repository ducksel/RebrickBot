import os
import re
import requests
from telegram import Update
from telegram.ext import (
	ApplicationBuilder, CommandHandler, MessageHandler,
	ContextTypes, filters
)

API_KEY = os.environ["REBRICKABLE_API_KEY"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text("Привет! Отправь LEGO код (4-5 цифр).")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
	text = update.message.text.strip()
	user = update.effective_user
	print(f"Текст от {user.username or user.id}: {text}")

	if re.fullmatch(r"\d{4,5}", text):
		lego_code = text
		set_id = f"{lego_code}-1"  # Rebrickable требует "-1" на конце

		url = f"https://rebrickable.com/api/v3/lego/sets/{set_id}/"
		headers = {"Authorization": f"key {API_KEY}"}
		print(f"Делаем запрос к Rebrickable для {set_id}")

		response = requests.get(url, headers=headers)

		if response.status_code == 200:
			data = response.json()
			name = data.get("name", "no name")
			year = data.get("year", "n/a")
			num_parts = data.get("num_parts", "?")
			await update.message.reply_text(
				f"✅ Набор {set_id}:\n{name} ({year})\n{num_parts} деталей"
			)
		elif response.status_code == 404:
			await update.message.reply_text(f"❌ Набор {set_id} не найден.")
		else:
			await update.message.reply_text(f"⚠️ Ошибка API: {response.status_code}")
	else:
		await update.message.reply_text("❌ Это не LEGO код. Введи 4 или 5 цифр.")

app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.run_polling()