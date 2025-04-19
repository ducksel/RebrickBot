# newsletter.py

import asyncio
from datetime import datetime
from pg_db import get_pending_messages, mark_message_sent, get_subscribed_users
from analytics import track_feature
from telegram import Bot

# Интервал проверки запланированных сообщений (в секундах)
CHECK_INTERVAL_SECONDS = 60  # 👉 на проде можно поставить 3600 (раз в час)

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
				for user in users:
					try:
						title = message.get("title", "").strip()
						content = message.get("content", "").strip()
						send_at = message.get("send_at")
						date_str = send_at.strftime("%d %b %Y") if send_at else ""

						full_text = f"🗓 {date_str} {title}\n\n{content}"

						await bot.send_message(
							chat_id=user["user_id"],
							text=full_text,
							parse_mode="HTML"
						)

						track_feature(
							user["user_id"],
							feature_name="newsletter_delivered",
							username=user.get("username"),
							params={
								"message_id": message["id"],
								"message_title": title
								"sent_at": str(send_at) if send_at else None
							}
						)
						delivered += 1
					except Exception as e:
						print(f"⚠️ Failed to send message to {user['user_id']}: {e}")

				print(f"✅ Message ID {message['id']} delivered to {delivered} users.")
				mark_message_sent(message["id"])

		await asyncio.sleep(CHECK_INTERVAL_SECONDS)
