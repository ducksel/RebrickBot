# analytics.py

import aiohttp
import os
import asyncio

GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID")
GA_API_SECRET = os.getenv("GA_API_SECRET")

async def send_ga_event(user_id: int, event_name: str, params: dict = None, user_props: dict = None):
	if not (GA_MEASUREMENT_ID and GA_API_SECRET):
		print("❌ GA config missing")
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
					print(f"⚠️ GA responded {response.status}: {await response.text()}")
	except Exception as e:
		print(f"⚠️ GA send error: {e}")

def track_command(user_id: int, command_name: str, username: str = None, language_code: str = None):
	props = {}
	if username:
		props["username"] = username
	if language_code:
		props["language"] = language_code
	asyncio.create_task(send_ga_event(user_id, f"command_{command_name}", user_props=props))

def track_feature(user_id: int, feature_name: str):
	asyncio.create_task(send_ga_event(user_id, "feature_used", {"feature": feature_name}))

def track_callback(user_id: int, callback_key: str):
	asyncio.create_task(send_ga_event(user_id, "callback_clicked", {"callback": callback_key}))

def track_error(user_id: int, error_code: str):
	asyncio.create_task(send_ga_event(user_id, "error_occurred", {"error": error_code}))
