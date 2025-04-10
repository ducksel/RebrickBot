import os
import requests

# Получаем данные из переменных окружения Railway
BRICKECONOMY_API_KEY = os.environ["BRICKECONOMY_API_KEY"]
BRICKECONOMY_USER_AGENT = os.environ["BRICKECONOMY_USER_AGENT"]

def get_pricing_info(set_num: str) -> str:
	"""
	Получает информацию о ценах из BrickEconomy API по номеру набора (например, '42176-1').
	Возвращает форматированный текст для вставки в Telegram-сообщение.
	"""
	try:
		# BrickEconomy API ожидает короткий номер (без -1)
		short_set_num = set_num.split("-")[0]

		url = f"https://www.brickeconomy.com/api/v1/set?number={short_set_num}-1"
		headers = {
			"x-apikey": BRICKECONOMY_API_KEY,
			"User-Agent": BRICKECONOMY_USER_AGENT,
			"Accept": "application/json"
		}

		# Выполняем GET-запрос к API BrickEconomy
		response = requests.get(url, headers=headers, timeout=10)

		# Отладка: если ошибка — покажем код и тело
		if response.status_code != 200:
			return f"⚠️ BrickEconomy error: {response.status_code}\n{response.text}"

		ry:
			data = response.json()
		except Exception as e:
			return f"⚠️ Failed to parse JSON from BrickEconomy:\n{str(e)}\n{response.text}"

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
