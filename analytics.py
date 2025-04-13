# analytics.py

async def send_ga_event(user_id: int, event_name: str, params: dict = None, user_props: dict = None):
	if not (GA_MEASUREMENT_ID and GA_API_SECRET):
		print("❌ Google Analytics конфигурация не найдена.")
		return

	url = (
		f"https://www.google-analytics.com/mp/collect"
		f"?measurement_id={GA_MEASUREMENT_ID}&api_secret={GA_API_SECRET}"
	)

	payload = {
		"client_id": f"tg-{user_id}",
		"user_properties": {
			key: {"value": value} for key, value in (user_props or {}).items()
		},
		"events": [
			{
				"name": event_name,
				"params": params or {}
			}
		]
	}

	try:
		async with aiohttp.ClientSession() as session:
			async with session.post(url, json=payload) as response:
				if response.status != 204:
					text = await response.text()
					print(f"⚠️ GA responded with status {response.status}: {text}")
	except Exception as e:
		print(f"⚠️ Ошибка отправки события в GA: {e}")
