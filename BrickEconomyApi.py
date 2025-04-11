import os
import requests
import html

# Получаем данные из переменных окружения Railway
BRICKECONOMY_API_KEY = os.environ["BRICKECONOMY_API_KEY"]
BRICKECONOMY_USER_AGENT = os.environ["BRICKECONOMY_USER_AGENT"]

def get_pricing_info(set_num: str) -> str:
	"""
	Получает информацию о ценах из BrickEconomy API по номеру набора (например, '42176-1').
	Возвращает форматированный текст для вставки в Telegram-сообщение.
	"""
	try:
		# BrickEconomy API требует путь вида /api/v1/set/<set_num>, например /api/v1/set/42176-1
		url = f"https://www.brickeconomy.com/api/v1/set/{set_num}"
		headers = {
			"x-apikey": BRICKECONOMY_API_KEY,
			"User-Agent": BRICKECONOMY_USER_AGENT,
			"Accept": "application/json"
		}

		# Выполняем GET-запрос к API BrickEconomy
		response = requests.get(url, headers=headers, timeout=10)

		# Отладка: если ошибка — покажем код и безопасное тело
		if response.status_code != 200:
			escaped_body = html.escape(response.text[:1000])  # обрезаем и экранируем HTML
			return f"⚠️ BrickEconomy error: {response.status_code}\n<pre>{escaped_body}</pre>"

		try:
			data = response.json()
		except Exception as e:
			escaped_body = html.escape(response.text[:1000])
			return f"⚠️ Failed to parse JSON from BrickEconomy:\n<pre>{escaped_body}</pre>"

		# Начинаем формировать текст ответа
		lines = ["\n<b>Price Info from BrickEconomy:</b>"]

		# Добавляем данные, если они доступны в ответе
		retail = data.get("retail_price")
		if retail:
			lines.append(f"Retail: ${retail:.2f}")

		current = data.get("current_value")
		if current:
			lines.append(f"Current Value (New): ${current:.2f}")

		used = data.get("used_value")
		if used:
			lines.append(f"Current Value (Used): ${used:.2f}")

		annual_growth = data.get("annual_growth_rate")
		if annual_growth:
			lines.append(f"Annual Growth: {annual_growth:.2f}%")

		price_trend = data.get("price_trend")
		if price_trend:
			lines.append(f"Price Trend: ${price_trend:.2f}")

		# Если ничего не найдено — выводим предупреждение
		if len(lines) == 1:
			return "⚠️ No pricing data found for this set."

		# Возвращаем собранный текст
		return "\n".join(lines)

	except Exception as e:
		return f"⚠️ Request to BrickEconomy failed:\n{str(e)}"
