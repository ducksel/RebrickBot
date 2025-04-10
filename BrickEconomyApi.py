import os
import requests

# Получаем API-ключ из переменной окружения Railway
BRICKECONOMY_API_KEY = os.environ["BRICKECONOMY_API_KEY"]

def get_pricing_info(set_num: str) -> str:
	"""
	Получает информацию о ценах из BrickEconomy API по номеру набора (например, '42176-1').
	Возвращает форматированный текст для вставки в Telegram-сообщение.
	"""
	try:
		# BrickEconomy API ожидает короткий номер (без -1)
		short_set_num = set_num.split("-")[0]

		url = f"https://www.brickeconomy.com/api/set/{short_set_num}"
		headers = {"x-api-key": BRICKECONOMY_API_KEY}

		# Выполняем GET-запрос к API BrickEconomy
		response = requests.get(url, headers=headers, timeout=10)

		# Возвращаем собранный текст
		return response.status_code

	except Exception as e:
		return f"⚠️ Request to BrickEconomy failed:\n{str(e)}"
