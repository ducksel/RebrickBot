# api_rebrickable.py

"""
Работа с Rebrickable API:
- Получение информации о LEGO-наборе
- Загрузка всех деталей набора
- Получение категорий деталей
"""

import os
import requests

# Получаем API-ключ Rebrickable из переменной окружения
REBRICKABLE_API_KEY = os.environ["REBRICKABLE_API_KEY"]

# ============================
# 🧱 Получение информации о наборе
# ============================
def get_set_details(set_id):
	"""
	Получает базовую информацию о наборе (номер, имя, год и количество деталей)
	Возвращает кортеж:
		(set_num, name, year, num_parts)
	или ("n/a", ...) если не удалось получить данные.
	"""
	url = f"https://rebrickable.com/api/v3/lego/sets/{set_id}/"
	headers = {"Authorization": f"key {REBRICKABLE_API_KEY}"}
	response = requests.get(url, headers=headers)
	if response.status_code == 200:
		data = response.json()
		set_num = data.get("set_num", "n/a")
		name = data.get("name", "n/a")
		year = data.get("year", "n/a")
		num_parts = data.get("num_parts", "n/a")
		return set_num, name, year, num_parts
	return "n/a", "n/a", "n/a", "n/a"

# ============================
# 🧩 Получение всех деталей набора
# ============================
def get_all_parts(set_id):
	"""
	Получает все детали набора, обходя все страницы (pagination)
	Возвращает список словарей, каждый словарь описывает одну деталь.
	"""
	parts = []
	url = f"https://rebrickable.com/api/v3/lego/sets/{set_id}/parts/"
	headers = {"Authorization": f"key {REBRICKABLE_API_KEY}"}
	while url:
		response = requests.get(url, headers=headers)
		if response.status_code != 200:
			break
		data = response.json()
		parts.extend(data.get("results", []))
		url = data.get("next")
	return parts

# ============================
# 🏷 Получение всех категорий деталей
# ============================
def get_categories():
	"""
	Получает все категории деталей из Rebrickable и возвращает словарь:
		{ category_id: category_name }
	Обходит все страницы результата.
	"""
	categories = {}
	url = "https://rebrickable.com/api/v3/lego/part_categories/"
	headers = {"Authorization": f"key {REBRICKABLE_API_KEY}"}
	while url:
		response = requests.get(url, headers=headers)
		if response.status_code != 200:
			break
		data = response.json()
		for cat in data.get("results", []):
			cat_id = cat.get("id")
			cat_name = cat.get("name")
			if cat_id is not None and cat_name is not None:
				categories[cat_id] = cat_name
		url = data.get("next")
	return categories
