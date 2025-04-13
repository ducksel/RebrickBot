import os
import requests
import html
import datetime

# Получаем данные из переменных окружения Railway
BRICKECONOMY_API_KEY = os.environ["BRICKECONOMY_API_KEY"]
BRICKECONOMY_USER_AGENT = os.environ["BRICKECONOMY_USER_AGENT"]

def get_pricing_info(set_num: str) -> str:
	try:
		url = f"https://www.brickeconomy.com/api/v1/set/{set_num}"
		headers = {
			"x-apikey": BRICKECONOMY_API_KEY,
			"User-Agent": BRICKECONOMY_USER_AGENT,
			"Accept": "application/json"
		}
		response = requests.get(url, headers=headers, timeout=10)
	
		if response.status_code != 200:
			escaped_body = html.escape(response.text[:1000])
			return f"⚠️ BrickEconomy error: {response.status_code}\\n<pre>{escaped_body}</pre>"
	
		try:
			json_data = response.json()
		except Exception:
			escaped_body = html.escape(response.text[:1000])
			return f"⚠️ Failed to parse JSON from BrickEconomy:\\n<pre>{escaped_body}</pre>"
	
		data = json_data.get("data", {})
		lines = ["\\n<b>📦 BrickEconomy Set Info:</b>"]
	
		name = data.get("name")
		year = data.get("year")
		if name or year:
			lines.append(f"<b>{name}</b> ({year})")
	
		start_date = data.get("release_date")
		end_date = data.get("retired_date") if data.get("retired") else None
		if start_date:
			try:
				start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
				if end_date:
					end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
					delta_months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
					lines.append(f"🗓 {start_date} – {end_date} ({delta_months} months)")
				else:
					lines.append(f"🟢 On sale since: {start_date}")
			except Exception as e:
				lines.append(f"⚠️ Date parsing error: {e}")
	
		availability = data.get("availability")
		retired = data.get("retired", False)
		if retired:
			lines.append(f"Availability: ❌ Retired")
		elif availability:
			availability_map = {
				"retail": "🛒 Retail",
				"retaillimited": "🏷 Limited Retail",
				"exclusive": "⭐️ Exclusive",
				"giftwithpurchase": "🎁 Gift with Purchase",
				"other": "📦 Other"
			}
			lines.append(f"Availability: {availability_map.get(availability, availability)}")
	
		retail_us = data.get("retail_price_us")
		retail_eu = data.get("retail_price_eu")
		if retail_us or retail_eu:
			retail_str = "<b>Retail Prices:</b>"
			if retail_us:
				retail_str += f" 🇺🇸 ${retail_us:.2f}"
			if retail_eu:
				retail_str += f"  🇪🇺 €{retail_eu:.2f}"
			lines.append(retail_str)
	
		current = data.get("current_value_new")
		num_parts = data.get("num_parts")
		if current:
			lines.append(f"<b>🔄 Current Value (New):</b> ${current:.2f}")
			if num_parts and isinstance(num_parts, int) and num_parts > 0 and retail_eu:
				ppp = retail_eu / num_parts
				lines.append(f"<b>🧮 PPP (€/piece):</b> €{ppp:.2f}")
	
		forecast_2y = data.get("forecast_value_new_2_years")
		forecast_5y = data.get("forecast_value_new_5_years")
		if forecast_2y or forecast_5y:
			lines.append("<b>📈 Forecast:</b>")
			if forecast_2y:
				lines.append(f"• 2 years: ${forecast_2y:.2f}")
			if forecast_5y:
				lines.append(f"• 5 years: ${forecast_5y:.2f}")
	
		if len(lines) == 1:
			return "⚠️ No pricing data found for this set."
	
		return "\\n".join(lines)
	
	except Exception as e:
		return f"⚠️ Request to BrickEconomy failed:\\n{str(e)}"
