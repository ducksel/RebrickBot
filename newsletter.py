# newsletter.py

import asyncio
from datetime import datetime
from pg_db import get_pending_messages, mark_message_sent, get_subscribed_users
from analytics import track_feature
from telegram import Bot

# Интервал проверки запланированных сообщений (в секундах)
CHECK_INTERVAL_SECONDS = 30  # 👉 на проде можно поставить 3600 (раз в час)

# ============================
# 🧾 ФУНКЦИЯ: ФОРМАТИРОВАНИЕ ОДНОГО СООБЩЕНИЯ
# ============================
def format_newsletter_message(message: dict) -> str:
	"""
	Форматирует одно сообщение рассылки (title + content с датой)
	в виде готового HTML для Telegram.
	"""
	title = message.get("title", "").strip()
	content = message.get("content", "").strip()
	send_at = message.get("send_at")
	date_str = send_at.strftime("%d %b %Y") if send_at else ""

	return f"🗓 {date_str} <b>{title}</b>\n\n{content}"

# ============================
# 🔄 ФУНКЦИЯ: ФОНОВАЯ РАССЫЛКА НОВОСТЕЙ
# ============================
async def newsletter_loop(bot: Bot):
	print(f"📡 Newsletter job started with interval {CHECK_INTERVAL_SECONDS} seconds...")

	while True:
		now = datetime.utcnow()
		messages = get_pending_messages(now)

		if not messages:
			print("📭 Checked for scheduled messages, no messages to send.")
		else:
			users = get_subscribed_users()
			for message in messages:
				delivered = 0
				full_text = format_newsletter_message(message)

				for user in users:
					try:
						await bot.send_message(
							chat_id=user["user_id"],
							text=full_text,
							parse_mode="HTML"
						)

						# Логируем в GA успешную доставку
						track_feature(
							user["user_id"],
							feature_name="newsletter_delivered",
							username=user.get("username"),
							params={
								"message_id": message["id"],
								"message_title": message.get("title"),
								"sent_at": str(message.get("send_at")) if message.get("send_at") else None
							}
						)
						delivered += 1
					except Exception as e:
						print(f"⚠️ Failed to send message to {user['user_id']}: {e}")

				print(f"✅ Message ID {message['id']} delivered to {delivered} users.")
				mark_message_sent(message["id"])

		await asyncio.sleep(CHECK_INTERVAL_SECONDS)
