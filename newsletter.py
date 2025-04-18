# newsletter.py

import asyncio
from datetime import datetime
from pg_db import get_pending_messages, mark_message_sent, get_subscribed_users
from analytics import track_feature
from telegram import Bot

# Интервал проверки запланированных сообщений (в секундах)
CHECK_INTERVAL_SECONDS = 60  # 👉 на проде можно поставить 3600 (раз в час)

async def newsletter_loop(bot: Bot):
	print("📡 Newsletter job started...")

	while True:
		print("🔍 Checking for scheduled messages...")
		now = datetime.utcnow()
		messages = get_pending_messages(now)

		if not messages:
			print("📭 No messages to send.")
		else:
			users = get_subscribed_users()
			for message in messages:
				delivered = 0
				for user in users:
					try:
						await bot.send_message(
							chat_id=user["user_id"],
							text=message["content"],
							parse_mode="HTML"
						)
						# 🔗 Логируем в GA факт доставки
						track_feature(
							user["user_id"],
							feature_name="newsletter_delivered",
							username=user.get("username"),
							message_id=message["id"],
							message_title=message.get("title"),
							sent_at=str(message.get("send_at")) if message.get("send_at") else None
						)
						delivered += 1
					except Exception as e:
						print(f"⚠️ Failed to send message to {user['user_id']}: {e}")

				print(f"✅ Message ID {message['id']} delivered to {delivered} users.")
				mark_message_sent(message["id"])

		await asyncio.sleep(CHECK_INTERVAL_SECONDS)
