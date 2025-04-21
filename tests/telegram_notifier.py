# Уведомления в телеграмм

import logging
from telegram.ext import Application
from telegram import Bot
from telegram.constants import ParseMode

class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        if not token or not chat_id:
            raise ValueError("Telegram token и chat_id должны быть указаны")
        self.token = token
        self.chat_id = chat_id
        self.application = None
        self.bot = None
        self.logger = logging.getLogger('telegram_notifier')

    async def initialize(self):
        """Инициализация приложения Telegram."""
        if self.application is None:
            self.application = await Application.builder().token(self.token).build()
            self.bot = self.application.bot

    async def send_message(self, message: str):
        """Отправка сообщения в Telegram."""
        try:
            if self.bot is None:
                await self.initialize()
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            self.logger.info(f"Message sent: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")