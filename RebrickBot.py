import os
import re
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
	ApplicationBuilder,
	CommandHandler,
	MessageHandler,
	CallbackQueryHandler,
	ContextTypes,
	filters
)

# Получаем API ключ Rebrickable из переменной окружения
REBRICKABLE_API_KEY = os.environ["REBRICKABLE_API_KEY"]

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text("Hello! Please send me a LEGO set code (4 or 5 digits).")

# Обработчик текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
	text = update.message.text.strip()
	print(f"Received text: {text}")

	# Проверка: LEGO код состоит из 4 или 5 цифр
	if re.fullmatch(r"\d{4,5}", text):
		lego_code = text
		# Формируем ID набора (обычно Rebrickable использует "-1" на конце)
		set_id = f"{lego_code}-1"
		
		url = f"https://rebrickable.com/api/v3/lego/sets/{set_id}/"
		headers = {"Authorization": f"key {REBRICKABLE_API_KEY}"}
		print(f"Making request for set {set_id}")
		
		response = requests.get(url, headers=headers)
		if response.status_code == 200:
			data = response.json()
			set_num = data.get("set_num", "n/a")
			name = data.get("name", "n/a")
			year = data.get("year", "n/a")
			num_parts = data.get("num_parts", "n/a")
			set_img_url = data.get("set_img_url")
			set_url = data.get("set_url", "n/a")
			
			# Формируем сообщение на английском
			message = (
				f"LEGO Set Details:\n"
				f"-----------------\n"
				f"Set Number: {set_num}\n"
				f"Name: {name}\n"
				f"Year Released: {year}\n"
				f"Pieces: {num_parts}\n\n"
				f"More Info: {set_url}"
			)
			
			# Создаем inline клавиатуру: две кнопки для сводных данных по деталям и кнопка-ссылка
			keyboard = InlineKeyboardMarkup([
				[
					InlineKeyboardButton("Parts by Color", callback_data="parts_by_color"),
					InlineKeyboardButton("Parts by Type", callback_data="parts_by_type")
				],
				[InlineKeyboardButton("View on Rebrickable", url=set_url)]
			])
			
			# Отправляем фото с подписью, если изображение набора есть, иначе текст
			if set_img_url:
				await update.message.reply_photo(photo=set_img_url, caption=message, reply_markup=keyboard)
			else:
				await update.message.reply_text(message, reply_markup=keyboard)
		elif response.status_code == 404:
			await update.message.reply_text(f"❌ LEGO set {set_id} not found.")
		else:
			await update.message.reply_text(f"⚠️ API Error: {response.status_code}")
	else:
		await update.message.reply_text("❌ Invalid LEGO code. Please enter exactly 4 or 5 digits.")

# Обработчик callback для кнопок "Parts by Color" и "Parts by Type"
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()  # уведомляем Telegram о том, что callback обработан
	if query.data == "parts_by_color":
		await query.edit_message_reply_markup(reply_markup=None)
		await query.message.reply_text("Parts summary by color coming soon!")
	elif query.data == "parts_by_type":
		await query.edit_message_reply_markup(reply_markup=None)
		await query.message.reply_text("Parts summary by type coming soon!")

# Инициализация приложения
app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()

# Регистрация обработчиков
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(handle_callback))

# Запуск бота (long polling)
app.run_polling()