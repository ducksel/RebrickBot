# analytics.py

import aiohttp
import os
import asyncio
import uuid

# Получаем идентификаторы из переменных окружения
GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID")
GA_API_SECRET = os.getenv("GA_API_SECRET")

def generate_client_id(user_id: int) -> str:
	"""
	Генерирует client_id, уникальный идентификатор для GA4, основанный на Telegram user_id.
	GA требует client_id для идентификации сессии/пользователя.
	UUIDv5 гарантирует одинаковый результат для одного и того же user_id.
	"""
	return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"tg-{user_id}"))

async def send_ga_event(
		user_id: int,
		event_name: str,
		params: dict = None,
		user_props: dict = None
	):
	"""
	Формирует и отправляет событие в GA4 через Measurement Protocol.
	
	:param user_id: Telegram user.id (уникальный идентификатор пользователя)
	:param event_name: Название события (например: command_start, feature_used)
	:param params: Параметры события (feature, callback, error и т.д.)
	:param user_props: Пользовательские свойства (username, language и т.п.)
	"""
	
	if not (GA_MEASUREMENT_ID and GA_API_SECRET):
		print("❌ GA config not found")
		return
	
	url = (
		f"https://www.google-analytics.com/mp/collect"
		f"?measurement_id={GA_MEASUREMENT_ID}&api_secret={GA_API_SECRET}"
	)
	
	# Добавляем базовые параметры события
	event_params = {
		"user_engagement": 1  # обязательный параметр GA4 для учета вовлеченности
	}
	
	if params:
		event_params.update(params)
	
	# user_properties — это то, что "приклеивается" к пользователю
	final_user_props = {}
	if user_props:
		final_user_props.update(user_props)
	
	payload = {
		"client_id": generate_client_id(user_id), # нужен для GA, не виден в отчетах
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
	
	# 👉 Логируем финальный payload для отладки
	import json
	print("📤 Sending GA event:")
	print(json.dumps(payload, indent=2, ensure_ascii=False))
	
	# Асинхронная отправка события
	try:
		async with aiohttp.ClientSession() as session:
			async with session.post(url, json=payload) as response:
				if response.status != 204:
					print(f"⚠️ GA responded with {response.status}: {await response.text()}")
	except Exception as e:
		print(f"⚠️ Error sending GA event: {e}")


def track_command(user_id: int, command_name: str, username: str = None, language_code: str = None):
	"""
	Фиксирует команду (/start, /help и т.п.) с привязкой к пользователю
	"""
	props = {
		"tg_user_id": str(user_id)  # ⬅️ обязательно!
	}
	if username:
		props["username"] = username
	if language_code:
		props["language"] = language_code

	asyncio.create_task(send_ga_event(
		user_id,
		event_name=f"command_{command_name}",
		user_props=props
	))

def track_feature(user_id: int, feature_name: str, username: str = None, language_code: str = None, params: dict = None):
	"""
	Отправка события использования функции ("text_query" и т.п.)
	"""
	props = {
		"tg_user_id": str(user_id)  # ⬅️ обязательно!
	}
	if username:
		props["username"] = username
	if language_code:
		props["language"] = language_code
	
	event_params = {"feature": feature_name}
	if params:
		event_params.update(params)
	
	asyncio.create_task(send_ga_event(
		user_id,
		event_name="feature_used",
		params=event_params,
		user_props=props
	))

def track_callback(user_id: int, callback_key: str, username: str = None, language_code: str = None):
	"""
	Фиксирует нажатие на inline-кнопку
	Пример: callback = "pricing:42176-1"
	"""
	props = {
		"tg_user_id": str(user_id)  # ⬅️ обязательно!
	}
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
	Фиксирует ошибку, например: timeouts, API failures, parsing issues
	"""
	asyncio.create_task(send_ga_event(
		user_id,
		event_name="error_occurred",
		params={"error": error_code}
	))