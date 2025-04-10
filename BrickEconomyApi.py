import os
import requests

# Получаем API-ключ из переменной окружения Railway
BRICKECONOMY_API_KEY = os.environ["BRICKECONOMY_API_KEY"]

def get_pricing_info(set_num: str) -> str:
	"""
	Получает информацию о ценах из BrickEconomy API по номеру набора (например, '42176').
	Возвращает форматированный текст для вставки в Telegram-сообщение.
	"""
	url = f"https://www.brickeconomy.com/api/set/{set_num}"
	headers = {"x-api-key": BRICKECONOMY_API_KEY}

	# Выполняем GET-запрос к API BrickEconomy
	response = requests.get(url, headers=headers)

	# Обработка ошибок
	if response.status_code != 200:
		return "⚠️ Failed to fetch price data from BrickEconomy."

	data = response.json()

	# Начинаем формировать текст ответа
	lines = ["\n<b>Price Info from BrickEconomy:</b>"]

	# Добавляем данные, если они доступны в ответе
	retail = data.get("retailPrice")
	if retail:
		lines.append(f"Retail: ${retail:.2f}")

	current = data.get("currentValue")
	if current:
		lines.append(f"Current Value (New): ${current:.2f}")

	used = data.get("usedValue")
	if used:
		lines.append(f"Current Value (Used): ${used:.2f}")

	annual_growth = data.get("annualGrowthRate")
	if annual_growth:
		lines.append(f"Annual Growth: {annual_growth:.2f}%")

	price_trend = data.get("priceTrend")
	if price_trend:
		lines.append(f"Price Trend: ${price_trend:.2f}")

	# Если ничего не найдено — выводим предупреждение
	if len(lines) == 1:
		return "⚠️ No pricing data found for this set."

	# Возвращаем собранный текст
	return "\n".join(lines)
