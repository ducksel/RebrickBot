# handlers.py

import re
import requests
import io
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import ContextTypes
from api_brickeconomy import get_pricing_info # работа с api сайта BrickEconomy
from api_rebrickable import get_set_details, get_all_parts, get_categories # работа с api сайта rebrickable
from analytics import track_command, track_feature, track_callback # логирование действий в GA с user_props
from db import get_recent_messages, add_or_update_user # работа с базой данных
from newsletter import format_newsletter_message # работа с рассылкой новостей

def get_lego_us_url(set_num):
	"""
	Формирует URL для официального сайта LEGO US по формуле.
	Принимает set_num (например, "42176-1") и возвращает URL вида:
	  https://www.lego.com/en-us/product/42176
	Проверка доступности не выполняется, чтобы избежать задержек.
	"""
	base = set_num.split("-")[0]
	return f"https://www.lego.com/en-us/product/{base}"

def build_inline_keyboard(set_id: str, set_url: str, lego_us_url: str) -> InlineKeyboardMarkup:
	"""
	Создаёт InlineKeyboard с кнопками для отображения деталей по цветам, типам, ценам и ссылками на Rebrickable и официальный сайт LEGO.
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

def group_parts_by_dynamic_category(parts):
	"""
	Группирует детали набора по категориям, полученным динамически через get_categories.
	Возвращает словарь: {название категории: количество деталей}
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

# ========================
# Команда /start
# ========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user = update.effective_user
	add_or_update_user(user)
	track_command(
		user.id,
		"start",
		username=user.username,
		language_code=user.language_code
	)
	await update.message.reply_text(
		"Hello! Please send me a Lego set code (4 or 5 digits).",
		parse_mode="HTML"
	)

# ========================
# Команда /newsletters
# ========================
async def newsletters(update: Update, context: ContextTypes.DEFAULT_TYPE):
	messages = get_recent_messages(limit=10)
	if not messages:
		await update.message.reply_text("🕳 No newsletter messages found.")
		return
	formatted = [format_newsletter_message(msg) for msg in messages]
	await update.message.reply_text("\n\n".join(formatted), parse_mode="HTML")

# ========================
# Обработка ввода LEGO-кода
# ========================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
	text = update.message.text.strip()
	user = update.effective_user
	track_feature(
		user.id,
		"text_query",
		username=user.username,
		language_code=user.language_code
	)

	match = re.fullmatch(r"(\d{4,5})(-\d)?", text)
	if not match:
		await update.message.reply_text("❌ Invalid LEGO code. Please enter exactly 4 or 5 digits.")
		return

	base = match.group(1)
	suffix = match.group(2) or "-1"
	set_id = f"{base}{suffix}"

	url = f"https://rebrickable.com/api/v3/lego/sets/{set_id}/"
	headers = {"Authorization": f"key {os.environ['REBRICKABLE_API_KEY']}"}
	response = requests.get(url, headers=headers)

	if response.status_code != 200:
		if response.status_code == 404:
			await update.message.reply_text(f"❌ LEGO set {set_id} not found.")
		else:
			await update.message.reply_text(f"⚠️ API Error: {response.status_code}")
		return

	data = response.json()
	set_num = data.get("set_num", "n/a")
	name = data.get("name", "n/a")
	year = data.get("year", "n/a")
	num_parts = data.get("num_parts", "n/a")
	set_img_url = data.get("set_img_url")
	set_url = data.get("set_url", "n/a")

	message = (
		f"<b>Set Number:</b> {set_num}\n"
		f"<b>Name:</b> {name}\n"
		f"<b>Year Released:</b> {year}\n"
		f"<b>Pieces:</b> {num_parts}"
	)

	if set_img_url:
		try:
			img_head = requests.head(set_img_url, allow_redirects=True, timeout=5)
			size = int(img_head.headers.get("Content-Length", 0))
			if size <= 5_000_000:
				await update.message.reply_photo(photo=set_img_url)
			else:
				img_data = requests.get(set_img_url, timeout=10).content
				await update.message.reply_photo(photo=InputFile(io.BytesIO(img_data), filename="lego.jpg"))
		except Exception as e:
			print(f"❌ Failed to send photo: {e}")

	keyboard = build_inline_keyboard(set_id, set_url, get_lego_us_url(set_num))
	await update.message.reply_text(text=message, parse_mode="HTML", reply_markup=keyboard)

# ========================
# Обработка inline-кнопок
# ========================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	user = query.from_user
	track_callback(
		user.id,
		query.data,
		username=user.username,
		language_code=user.language_code
	)

	try:
		action, set_id = query.data.split(":", 1)
	except ValueError:
		await query.message.reply_text("Error: Set information is missing.")
		return

	set_num, set_name, year, num_parts = get_set_details(set_id)
	main_message = (
		f"<b>Set Number:</b> {set_num}\n"
		f"<b>Name:</b> {set_name}\n"
		f"<b>Year Released:</b> {year}\n"
		f"<b>Pieces:</b> {num_parts}"
	)

	additional_info = ""

	if action == "parts_by_color":
		parts = get_all_parts(set_id)
		if not parts:
			await query.message.edit_text(main_message + "\n⚠️ No parts data found or API error.", parse_mode="HTML")
			return
		color_summary = {}
		for part in parts:
			color = part.get("color", {})
			color_name = color.get("name", "Unknown")
			quantity = part.get("quantity", 0)
			color_summary[color_name] = color_summary.get(color_name, 0) + quantity
		lines = ["\n<b>Parts Summary by Color:</b>"]
		for color_name, total in sorted(color_summary.items(), key=lambda x: x[1], reverse=True):
			lines.append(f"<b>{color_name}</b>: {total}")
		additional_info = "\n".join(lines)

	elif action == "parts_by_type":
		parts = get_all_parts(set_id)
		if not parts:
			await query.message.edit_text(main_message + "\n⚠️ No parts data found or API error.", parse_mode="HTML")
			return
		category_summary = group_parts_by_dynamic_category(parts)
		lines = ["\n<b>Parts Summary by Type:</b>"]
		for cat_name, total in sorted(category_summary.items(), key=lambda x: x[1], reverse=True):
			lines.append(f"<b>{cat_name}</b>: {total}")
		additional_info = "\n".join(lines)

	elif action == "pricing":
		additional_info = get_pricing_info(set_id)
	else:
		additional_info = "\n⚠️ Unknown action."

	keyboard = build_inline_keyboard(set_id, f"https://rebrickable.com/sets/{set_id}/", get_lego_us_url(set_num))
	await query.message.edit_text(main_message + "\n" + additional_info, parse_mode="HTML", reply_markup=keyboard)
