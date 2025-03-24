# Уведомления в телеграм

import logging
from telegram.ext import Application, CommandHandler

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.application = Application.builder().token(token).build()
        self.bot = self.application.bot
        self.chat_id = chat_id
        self.logger = logging.getLogger('telegram_notifier')
        self.is_running = False  # Переменная для управления состоянием бота

        # Регистрация команд
        self.application.add_handler(CommandHandler("start_bot", self.start_bot))
        self.application.add_handler(CommandHandler("stop_bot", self.stop_bot))

    async def send_message(self, message):
        """
        Отправляет сообщение в Telegram.
        """
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            self.logger.info(f"Message sent: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")

    async def start_bot(self, update, context):
        """
        Команда для запуска бота.
        """
        if not self.is_running:
            self.is_running = True
            await update.message.reply_text("✅ Бот запущен.")
            self.logger.info("Бот запущен.")
        else:
            await update.message.reply_text("⚠️ Бот уже запущен.")

    async def stop_bot(self, update, context):
        """
        Команда для остановки бота.
        """
        if self.is_running:
            self.is_running = False
            await update.message.reply_text("⏹️ Бот остановлен.")
            self.logger.info("Бот остановлен.")
        else:
            await update.message.reply_text("⚠️ Бот уже остановлен.")

    async def run(self):
        """
        Запуск Telegram-бота.
        """
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        self.logger.info("Telegram-бот запущен.")