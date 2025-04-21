# Уведомления в телеграмм

import logging
from telegram.ext import Application
from telegram import Bot
from telegram.constants import ParseMode

class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        if not token or not chat_id:
            raise ValueError("Telegram token и chat_id должны быть указаны")
        self.application = Application.builder().token(token).build()
        self.bot = self.application.bot
        self.chat_id = chat_id
        self.logger = logging.getLogger('telegram_notifier')

    async def send_message(self, message: str):
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            self.logger.info(f"Message sent: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            