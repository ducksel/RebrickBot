# pg_db.py

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Получаем URL подключения к PostgreSQL из переменной окружения Railway
DATABASE_URL = os.environ["DATABASE_URL"]

# ============================
# 📦 ФУНКЦИЯ: ИНИЦИАЛИЗАЦИЯ БАЗЫ
# ============================
def init_db():
	"""
	Создаёт таблицу messages, если она ещё не существует.
	Таблица содержит:
		- id: уникальный идентификатор
		- title: заголовок сообщения (необязательный)
		- content: HTML-сообщение для отправки
		- send_at: дата и время планируемой отправки (UTC)
		- sent: флаг, было ли сообщение уже отправлено
	"""
	with psycopg2.connect(DATABASE_URL) as conn:
		with conn.cursor() as cur:
			cur.execute("""
				CREATE TABLE IF NOT EXISTS messages (
					id SERIAL PRIMARY KEY,
					title TEXT,
					content TEXT NOT NULL,
					send_at TIMESTAMP NOT NULL,
					sent BOOLEAN DEFAULT FALSE
				)
			""")
		conn.commit()

# ============================
# ➕ ФУНКЦИЯ: ДОБАВЛЕНИЕ СООБЩЕНИЯ
# ============================
def add_message(title: str, content: str, send_at: datetime):
	"""
	Добавляет новое сообщение в таблицу для будущей отправки.
	Аргументы:
		- title: заголовок (можно None)
		- content: HTML-текст, который будет отправлен ботом
		- send_at: время, когда сообщение должно быть отправлено
	"""
	with psycopg2.connect(DATABASE_URL) as conn:
		with conn.cursor() as cur:
			cur.execute(
				"INSERT INTO messages (title, content, send_at) VALUES (%s, %s, %s)",
				(title, content, send_at)
			)
		conn.commit()

# ============================
# 📬 ФУНКЦИЯ: ПОЛУЧЕНИЕ ГОТОВЫХ К ОТПРАВКЕ
# ============================
def get_pending_messages(current_time: datetime):
	"""
	Возвращает список сообщений, которые нужно отправить сейчас.
	Условия:
		- сообщение ещё не отправлено (sent = FALSE)
		- запланировано на время <= current_time
	"""
	with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
		with conn.cursor() as cur:
			cur.execute(
				"SELECT * FROM messages WHERE sent = FALSE AND send_at <= %s ORDER BY send_at ASC",
				(current_time,)
			)
			return cur.fetchall()

# ============================
# ✅ ФУНКЦИЯ: ПОМЕТКА КАК ОТПРАВЛЕННОГО
# ============================
def mark_message_sent(message_id: int):
	"""
	Обновляет статус сообщения: помечает его как отправленное.
	"""
	with psycopg2.connect(DATABASE_URL) as conn:
		with conn.cursor() as cur:
			cur.execute(
				"UPDATE messages SET sent = TRUE WHERE id = %s",
				(message_id,)
			)
		conn.commit()

def get_recent_messages(limit=10):
		"""
		Возвращает последние N новостных сообщений, отсортированных по дате отправки
		"""
		with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
			with conn.cursor() as cur:
				cur.execute(
					"SELECT * FROM messages ORDER BY send_at DESC LIMIT %s",
					(limit,)
				)
				return cur.fetchall()