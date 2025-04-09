import os
import re
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
	ApplicationBuilder,
	CommandHandler,
	MessageHandler,
<<<<<<< HEAD
	CallbackQueryHandler,
=======
>>>>>>> main
	ContextTypes,
	filters
)

# Получаем API-ключ Rebrickable из переменной окружения
REBRICKABLE_API_KEY = os.environ["REBRICKABLE_API_KEY"]

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text("Hello! Please send me a LEGO set code (4 or 5 digits).")

<<<<<<< HEAD
# Обработчик текстовых сообщений с запросом к Rebrickable
=======
# Обработчик текстовых сообщений
>>>>>>> main
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
	text = update.message.text.strip()
	print(f"Received text: {text}")

<<<<<<< HEAD
	# Проверка: LEGO код состоит из 4 или 5 цифр
	if re.fullmatch(r"\d{4,5}", text):
		lego_code = text
		# Формируем ID набора (обычно Rebrickable использует "-1" на конце)
=======
	# Проверка, что введён код состоит из 4 или 5 цифр
	if re.fullmatch(r"\d{4,5}", text):
		lego_code = text
		# Формируем ID набора (обычно Rebrickable использует "-1" в конце)
>>>>>>> main
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
			
<<<<<<< HEAD
			# Формируем сообщение на английском, аккуратно выводя год выпуска
			message = (
				f"LEGO Set Details:\n"
=======
			# Формируем сообщение на английском
			message = (
				f"LEGO Set Details:\n"
				f"-----------------\n"
>>>>>>> main
				f"Set Number: {set_num}\n"
				f"Name: {name}\n"
				f"Year Released: {year}\n"
				f"Pieces: {num_parts}\n\n"
				f"More Info: {set_url}"
			)
			
<<<<<<< HEAD
			# Создаем inline-клавиатуру с двумя кнопками
			keyboard = InlineKeyboardMarkup([
				[InlineKeyboardButton("View on Rebrickable", url=set_url),
				 InlineKeyboardButton("Parts Details", callback_data="parts_details")]
			])
			
			# Если есть изображение набора, отправляем фото с подписью и клавиатурой
			if set_img_url:
				await update.message.reply_photo(photo=set_img_url, caption=message, reply_markup=keyboard)
			else:
				await update.message.reply_text(message, reply_markup=keyboard)
=======
			# Если есть URL изображения, отправляем фотографию с подписью
			if set_img_url:
				await update.message.reply_photo(photo=set_img_url, caption=message)
			else:
				await update.message.reply_text(message)
>>>>>>> main
		elif response.status_code == 404:
			await update.message.reply_text(f"❌ LEGO set {set_id} not found.")
		else:
			await update.message.reply_text(f"⚠️ API Error: {response.status_code}")
	else:
		await update.message.reply_text("❌ Invalid LEGO code. Please enter exactly 4 or 5 digits.")
<<<<<<< HEAD

# Обработчик callback для кнопки "Parts Details"
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()  # уведомляем Telegram, что callback обработан
	if query.data == "parts_details":
		await query.edit_message_reply_markup(reply_markup=None)  # можно убрать клавиатуру, если нужно
		await query.message.reply_text("Parts details coming soon!")  # плейсхолдерное сообщение
=======
>>>>>>> main

# Инициализация приложения
app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()

# Регистрация обработчиков
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(handle_callback))

# Запуск бота (long polling)
app.run_polling()