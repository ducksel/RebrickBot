# analytics.py

import aiohttp
import os
import asyncio
import uuid

# Получаем переменные окружения
GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID")
GA_API_SECRET = os.getenv("GA_API_SECRET")


def generate_client_id(user_id: int) -> str:
	"""
	Генерирует client_id на основе Telegram user_id.
	Использует UUIDv5, чтобы избежать конфликта и сохранить уникальность.
	"""
	return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"tg-{user_id}"))


async def send_ga_event(user_id: int, event_name: str, params: dict = None, user_props: dict = None):
	"""
	Отправляет событие в Google Analytics 4 через Measurement Protocol.
	"""
	if not (GA_MEASUREMENT_ID and GA_API_SECRET):
		print("❌ GA config not found")
		return

	url = (
		f"https://www.google-analytics.com/mp/collect"
		f"?measurement_id={GA_MEASUREMENT_ID}&api_secret={GA_API_SECRET}"
	)

	# Добавляем базовые параметры
	event_params = {
			"user_engagement": 1,
			"debug_mode": 1  # ⬅️ Включить для отладки, выключить для использования
		}
	
	if params:
		event_params.update(params)

	# Добавляем user_id в user_properties
	final_user_props = {
		"user_id": str(user_id)
	}
	if user_props:
		final_user_props.update(user_props)

	payload = {
		"client_id": generate_client_id(user_id),
		"user_properties": {
			key: {"value": value}
			for key, value in final_user_props.items()
		},
		"events": [
			{
				"name": event_name,
				"params": event_params
			}
		]
	}

	try:
		async with aiohttp.ClientSession() as session:
			async with session.post(url, json=payload) as response:
				if response.status != 204:
					print(f"⚠️ GA responded with {response.status}: {await response.text()}")
	except Exception as e:
		print(f"⚠️ Error sending GA event: {e}")


def track_command(user_id: int, command_name: str, username: str = None, language_code: str = None):
	"""
	Отправка события при вводе команды (/start, /help и т.п.)
	"""
	props = {}
	if username:
		props["username"] = username
	if language_code:
		props["language"] = language_code

	asyncio.create_task(send_ga_event(
		user_id,
		event_name=f"command_{command_name}",
		user_props=props
	))


def track_feature(user_id: int, feature_name: str):
	"""
	Отправка события использования функции (поиск, фильтрация и т.п.)
	"""
	asyncio.create_task(send_ga_event(
		user_id,
		event_name="feature_used",
		params={"feature": feature_name}
	))


def track_callback(user_id: int, callback_key: str, username: str = None, language_code: str = None):
	"""
	Отправка события при нажатии inline-кнопки
	"""
	props = {}
	if username:
		props["username"] = username
	if language_code:
		props["language"] = language_code

	asyncio.create_task(send_ga_event(
		user_id,
		event_name="callback_clicked",
		params={"callback": callback_key},
		user_props=props
	))


def track_error(user_id: int, error_code: str):
	"""
	Отправка события ошибки, если что-то пошло не так
	"""
	asyncio.create_task(send_ga_event(
		user_id,
		event_name="error_occurred",
		params={"error": error_code}
	))
