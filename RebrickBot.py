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

REBRICKABLE_API_KEY = os.environ["REBRICKABLE_API_KEY"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text("Hello! Please send me a LEGO set code (4 or 5 digits).", parse_mode="HTML")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
	text = update.message.text.strip()
	print(f"Received text: {text}")

	if re.fullmatch(r"\d{4,5}", text):
		lego_code = text
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
			
			# Формируем сообщение с HTML-разметкой
			message = (
				f"<b>Lego set details:</b>\n"
				f"<b>Set Number:</b> {set_num}\n"
				f"<b>Name:</b> {name}\n"
				f"<b>Year Released:</b> {year}\n"
				f"<b>Pieces:</b> {num_parts}"
			)
			
			# Inline-клавиатура: две кнопки для сводных данных по деталям и кнопка-ссылка на Rebrickable
			keyboard = InlineKeyboardMarkup([
				[
					InlineKeyboardButton("Parts by Color", callback_data=f"parts_by_color:{set_id}"),
					InlineKeyboardButton("Parts by Type", callback_data="parts_by_type")
				],
				[InlineKeyboardButton("View on Rebrickable", url=set_url)]
			])
			
			if set_img_url:
				await update.message.reply_photo(photo=set_img_url, caption=message, parse_mode="HTML", reply_markup=keyboard)
			else:
				await update.message.reply_text(message, parse_mode="HTML", reply_markup=keyboard)
		elif response.status_code == 404:
			await update.message.reply_text(f"❌ LEGO set {set_id} not found.")
		else:
			await update.message.reply_text(f"⚠️ API Error: {response.status_code}")
	else:
		await update.message.reply_text("❌ Invalid LEGO code. Please enter exactly 4 or 5 digits.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()

	# Проверяем, что callback_data начинается с "parts_by_color:" и извлекаем set_id
	if query.data.startswith("parts_by_color:"):
		try:
			_, set_id = query.data.split(":", 1)
		except ValueError:
			await query.message.reply_text("Error: Set information is missing.")
			return
	
		# Формируем URL для получения деталей набора по цвету
		url = f"https://rebrickable.com/api/v3/lego/sets/{set_id}/parts/"
		headers = {"Authorization": f"key {os.environ['REBRICKABLE_API_KEY']}"}
		
		# Делаем запрос к API
		response = requests.get(url, headers=headers)
		if response.status_code == 200:
			parts_data = response.json()
			color_summary = {}
	
			# Пройдемся по каждой детали в полученных результатах
			for part in parts_data.get("results", []):
				# Извлекаем имя цвета и количество деталей
				color = part.get("color", {})
				color_name = color.get("name", "Unknown")
				quantity = part.get("quantity", 0)
				color_summary[color_name] = color_summary.get(color_name, 0) + quantity
	
			# Формируем сообщение с HTML-разметкой
			message_lines = ["<b>Parts Summary by Color:</b>"]
			for color_name, total in color_summary.items():
				message_lines.append(f"<b>{color_name}</b>: {total}")
			message = "\n".join(message_lines)
	
			# Убираем клавиатуру и отправляем сообщение с результатами
			await query.edit_message_reply_markup(reply_markup=None)
			await query.message.reply_text(message, parse_mode="HTML")
		else:
			await query.message.reply_text(f"⚠️ API Error: {response.status_code}")


	elif query.data == "parts_by_type":
		await query.message.reply_text("Parts summary by type coming soon!")
		
		
		

app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(handle_callback))
app.run_polling()