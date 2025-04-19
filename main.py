# main.py

import os
import asyncio
from telegram.ext import (
	ApplicationBuilder,
	CommandHandler,
	MessageHandler,
	CallbackQueryHandler,
	filters,
)
from db import init_db            # ✅ инициализация базы данных
from newsletter import newsletter_loop  # ✅ запуск фоновой задачи по отправке рассылок
from handlers import (
	start,
	newsletters,
	handle_text,
	handle_callback
)  # ✅ импорт всех хендлеров из handlers.py

# ---------------------------
# 🚀 Функция запуска фоновой рассылки после старта приложения
# ---------------------------
async def post_init(application):
	"""
	Запускает фоновую задачу рассылки новостей после инициализации Telegram-приложения.
	Используется безопасный способ запуска задачи, привязанный к event loop.
	"""
	loop = asyncio.get_running_loop()
	loop.create_task(newsletter_loop(application.bot))


# ========================
# 🚀 Точка входа — регистрация бота, базы данных и хендлеров
# ========================
if __name__ == "__main__":
	init_db()  # 🧱 создаёт таблицы в базе данных при первом запуске (если их ещё нет)
	app = ApplicationBuilder()\
		.token(os.environ["BOT_TOKEN"])\
		.post_init(post_init)\
		.build()

	# 📌 Регистрируем команды и обработчики
	app.add_handler(CommandHandler("start", start))
	app.add_handler(CommandHandler("newsletters", newsletters))
	app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
	app.add_handler(CallbackQueryHandler(handle_callback))

    # ✅ импорт всех хендлеров из handlers.py
	app.run_polling()
