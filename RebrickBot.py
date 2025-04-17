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
from BrickEconomyApi import get_pricing_info  # импортируем функцию из модуля BrickEconomy
from analytics import track_command, track_feature, track_callback  # логирование действий с user_props

# Получаем API-ключ Rebrickable из переменной окружения
REBRICKABLE_API_KEY = os.environ["REBRICKABLE_API_KEY"]

def get_lego_us_url(set_num):
	"""
	Формирует URL для официального сайта LEGO US по формуле.
	Принимает set_num (например, "42176-1") и возвращает URL вида:
	  https://www.lego.com/en-us/product/42176
	Проверка доступности не выполняется, чтобы избежать задержек.
	"""
	base = set_num.split("-")[0]  # Берём только числовую часть
	return f"https://www.lego.com/en-us/product/{base}"

def build_inline_keyboard(set_id: str, set_url: str, lego_us_url: str) -> InlineKeyboardMarkup:
	"""
	Создаёт InlineKeyboard с кнопками для отображения деталей по цветам, типам, ценам и ссылками на Rebrickable и официальный сайт LEGO.
	Эта функция используется как в начальном сообщении, так и при редактировании.
	"""
	return InlineKeyboardMarkup([
		[
			InlineKeyboardButton("Parts by Color", callback_data=f"parts_by_color:{set_id}"),
			InlineKeyboardButton("Parts by Type", callback_data=f"parts_by_type:{set_id}")
		],
		[
			InlineKeyboardButton("View Prices", callback_data=f"pricing:{set_id}")
		],
		[
			InlineKeyboardButton("View on Rebrickable", url=set_url)
		],
		[
			InlineKeyboardButton("View on LEGO US", url=lego_us_url)
		]
	])

def get_all_parts(set_id):
	"""
	Получает все детали набора, обходя все страницы (pagination)
	"""
	parts = []
	url = f"https://rebrickable.com/api/v3/lego/sets/{set_id}/parts/"
	headers = {"Authorization": f"key {os.environ['REBRICKABLE_API_KEY']}"}
	while url:
		response = requests.get(url, headers=headers)
		if response.status_code != 200:
			break
		data = response.json()
		parts.extend(data.get("results", []))
		url = data.get("next")
	return parts

def get_categories():
	"""
	Получает все категории деталей из Rebrickable и возвращает словарь,
	где ключ – идентификатор категории, а значение – название категории.
	Обходит все страницы результата.
	"""
	categories = {}
	url = "https://rebrickable.com/api/v3/lego/part_categories/"
	headers = {"Authorization": f"key {os.environ['REBRICKABLE_API_KEY']}"}
	while url:
		response = requests.get(url, headers=headers)
		if response.status_code != 200:
			break
		data = response.json()
		for cat in data.get("results", []):
			cat_id = cat.get("id")
			cat_name = cat.get("name")
			if cat_id is not None and cat_name is not None:
				categories[cat_id] = cat_name
		url = data.get("next")
	return categories

def group_parts_by_dynamic_category(parts):
	"""
	Группирует детали набора по категориям, полученным динамически через get_categories.
	Возвращает словарь: ключ – название категории, значение – суммарное количество деталей.
	"""
	categories = get_categories()
	category_summary = {}
	for part in parts:
		part_obj = part.get("part", {})
		cat_id = part_obj.get("part_cat_id")
		quantity = part.get("quantity", 0)
		if cat_id is not None:
			cat_name = categories.get(cat_id, f"Category {cat_id}")
			category_summary[cat_name] = category_summary.get(cat_name, 0) + quantity
	return category_summary

def get_set_details(set_id):
	"""
	Получает базовую информацию о наборе (номер, имя, год и количество деталей)
	"""
	url = f"https://rebrickable.com/api/v3/lego/sets/{set_id}/"
	headers = {"Authorization": f"key {REBRICKABLE_API_KEY}"}
	response = requests.get(url, headers=headers)
	if response.status_code == 200:
		data = response.json()
		set_num = data.get("set_num", "n/a")
		name = data.get("name", "n/a")
		year = data.get("year", "n/a")
		num_parts = data.get("num_parts", "n/a")
		return set_num, name, year, num_parts
	return "n/a", "n/a", "n/a", "n/a"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""
	Команда /start — показывает приветственное сообщение.
	"""
	user = update.effective_user
	track_command(
		user.id,
		"start",
		username=user.username,
		language_code=user.language_code
	)
	await update.message.reply_text(
		"Hello! Please send me a LEGO set code (4 or 5 digits).",
		parse_mode="HTML"
	)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""
	Обрабатывает текстовое сообщение, проверяет — это ли код LEGO-набора,
	и, если да, загружает и показывает информацию о наборе.
	"""
	text = update.message.text.strip()
	print(f"Received text: {text}")

	user = update.effective_user
	track_feature(
		user.id,
		"text_query",
		username=user.username,
		language_code=user.language_code
	)
	
	# Проверка, что введено 4 или 5 цифр (код LEGO-набора)
	match = re.fullmatch(r"(\d{4,5})(-\d)?", text)
	if match:
		base = match.group(1)
		suffix = match.group(2) or "-1"
		set_id = f"{base}{suffix}"

		# Запрос к API Rebrickable
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

			# Формируем основное текстовое сообщение
			message = (
				f"<b>Set Number:</b> {set_num}\n"
				f"<b>Name:</b> {name}\n"
				f"<b>Year Released:</b> {year}\n"
				f"<b>Pieces:</b> {num_parts}"
			)

			# Обработка изображения с проверкой размера
			if set_img_url:
				print(f"Photo processing")
				try:
					img_head = requests.head(set_img_url, allow_redirects=True, timeout=5)
					size_str = img_head.headers.get("Content-Length")
					if size_str is not None:
						size = int(size_str)
						print(f"Image size: {size} bytes")
						if size <= 5_000_000:
							await update.message.reply_photo(photo=set_img_url)
							set_img_url = None  # уже отправили
					if set_img_url:
						img_response = requests.get(set_img_url, timeout=10)
						if img_response.status_code == 200:
							import io
							from telegram import InputFile
							image_data = io.BytesIO(img_response.content)
							await update.message.reply_photo(photo=InputFile(image_data, filename="lego.jpg"))
						else:
							print(f"❌ Image download failed: {img_response.status_code}")
				except Exception as e:
					print(f"❌ Failed to send photo: {e}")

			lego_us_url = get_lego_us_url(set_num)
			keyboard = build_inline_keyboard(set_id, set_url, lego_us_url)

			await update.message.reply_text(
				text=message,
				parse_mode="HTML",
				reply_markup=keyboard
			)
		elif response.status_code == 404:
			await update.message.reply_text(f"❌ LEGO set {set_id} not found.")
		else:
			await update.message.reply_text(f"⚠️ API Error: {response.status_code}")
	else:
		await update.message.reply_text("❌ Invalid LEGO code. Please enter exactly 4 or 5 digits.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""
	Обрабатывает нажатие на inline-кнопки: по цвету, типу, ценам и т.д.
	Редактирует сообщение, добавляя соответствующую информацию.
	"""
	query = update.callback_query
	await query.answer()

	user = query.from_user
	track_callback(
		user.id,
		query.data,
		username=user.username,
		language_code=user.language_code
	)

	# Разбираем callback_data: action:set_id
	try:
		action, set_id = query.data.split(":", 1)
	except ValueError:
		await query.message.reply_text("Error: Set information is missing.")
		return

	# Получаем основную информацию о наборе
	set_num, set_name, year, num_parts = get_set_details(set_id)
	main_message = (
		f"<b>Set Number:</b> {set_num}\n"
		f"<b>Name:</b> {set_name}\n"
		f"<b>Year Released:</b> {year}\n"
		f"<b>Pieces:</b> {num_parts}"
	)

	additional_info = ""

	if action == "parts_by_color":
		# Детали по цвету
		parts = get_all_parts(set_id)
		if not parts:
			await query.message.edit_text(
				main_message + "\n⚠️ No parts data found or API error.",
				parse_mode="HTML"
			)
			return
		color_summary = {}
		for part in parts:
			color = part.get("color", {})
			color_name = color.get("name", "Unknown")
			quantity = part.get("quantity", 0)
			color_summary[color_name] = color_summary.get(color_name, 0) + quantity
		sorted_colors = sorted(color_summary.items(), key=lambda item: item[1], reverse=True)
		lines = ["\n<b>Parts Summary by Color:</b>"]
		for color_name, total in sorted_colors:
			lines.append(f"<b>{color_name}</b>: {total}")
		additional_info = "\n".join(lines)

	elif action == "parts_by_type":
		# Детали по типу (категориям)
		parts = get_all_parts(set_id)
		if not parts:
			await query.message.edit_text(
				main_message + "\n⚠️ No parts data found or API error.",
				parse_mode="HTML"
			)
			return
		category_summary = group_parts_by_dynamic_category(parts)
		sorted_categories = sorted(category_summary.items(), key=lambda item: item[1], reverse=True)
		lines = ["\n<b>Parts Summary by Type:</b>"]
		for cat_name, total in sorted_categories:
			lines.append(f"<b>{cat_name}</b>: {total}")
		additional_info = "\n".join(lines)

	elif action == "pricing":
		# Информация о ценах из BrickEconomy API
		# Передаём set_id (например, '42176-1') — функция сама обрежет хвост
		additional_info = get_pricing_info(set_id)
	else:
		additional_info = "\n⚠️ Unknown action."

	set_url = f"https://rebrickable.com/sets/{set_id}/"
	lego_us_url = get_lego_us_url(set_num)
	keyboard = build_inline_keyboard(set_id, set_url, lego_us_url)

	await query.message.edit_text(
		main_message + "\n" + additional_info,
		parse_mode="HTML",
		reply_markup=keyboard
	)

# Регистрация бота и хендлеров
app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(handle_callback))
app.run_polling()