import os
import requests

# Получаем API-ключ из переменной окружения Railway
BRICKECONOMY_API_KEY = os.environ["BRICKECONOMY_API_KEY"]

def get_pricing_info(set_num: str) -> str:
"""
Получает информацию о ценах из BrickEconomy API по номеру набора (например, '42176-1').
Возвращает форматированный текст для вставки в Telegram-сообщение.
"""
short_set_num = set_num.split("-")[0]
url = f"https://www.brickeconomy.com/api/set/{short_set_num}"
headers = {"x-api-key": BRICKECONOMY_API_KEY}

try:
	response = requests.get(url, headers=headers, timeout=10)

	if response.status_code != 200:
		return f"⚠️ BrickEconomy error: {response.status_code}\n{response.text}"

	try:
		data = response.json()
	except Exception as e:
		return f"⚠️ Failed to parse JSON from BrickEconomy:\n{str(e)}\n{response.text}"

	lines = ["\n<b>Price Info from BrickEconomy:</b>"]

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

	if len(lines) == 1:
		return "⚠️ No pricing data found for this set."

	return "\n".join(lines)

except Exception as e:
	return f"⚠️ Request to BrickEconomy failed:\n{str(e)}"
