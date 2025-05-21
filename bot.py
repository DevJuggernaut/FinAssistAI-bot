import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from config import TELEGRAM_TOKEN
from handlers import command_handler, message_handler, callback_handler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def main():
    """Start the bot"""
    logger.info("Starting FinAssistAI bot...")
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Обробники команд
    application.add_handler(CommandHandler("start", command_handler.start))
    application.add_handler(CommandHandler("help", command_handler.help_command))
    
    # Обробники повідомлень
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler.handle_text_message))
    application.add_handler(MessageHandler(filters.PHOTO, message_handler.handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, message_handler.handle_document))
    
    # Обробник колбеків від інлайн-кнопок
    application.add_handler(CallbackQueryHandler(callback_handler.handle_callback))
    
    # Запуск бота
    logger.info("Bot started. Press Ctrl+C to stop.")
    application.run_polling()
    
if __name__ == "__main__":
    main()