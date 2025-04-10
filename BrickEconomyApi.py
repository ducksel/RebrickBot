import os
import requests

# Получаем API-ключ из переменной окружения Railway
BRICKECONOMY_API_KEY = os.environ["BRICKECONOMY_API_KEY"]

def get_pricing_info(set_num: str) -> str:
	return "TEST"
