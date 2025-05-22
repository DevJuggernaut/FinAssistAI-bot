import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)

from database.config import TELEGRAM_TOKEN, OPENAI_API_KEY
from handlers.command_handler import (
    start,
    help_command,
    stats_command,
    add_transaction_command,
    budget_command,
    settings,
    notifications_command,
    get_setup_handler
)
from handlers import message_handler, callback_handler
from database.session import init_db
from services.statement_parser import StatementParser, ReceiptProcessor
from services.ml_categorizer import TransactionCategorizer
from services.openai_service import OpenAIService
from services.analytics_service import AnalyticsService

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Initialize services
statement_parser = StatementParser()
receipt_processor = ReceiptProcessor()
transaction_categorizer = TransactionCategorizer()
openai_service = OpenAIService(OPENAI_API_KEY)
analytics_service = AnalyticsService()

def main():
    """Запуск бота"""
    # Ініціалізуємо базу даних
    init_db()
    
    # Створюємо застосунок
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Додаємо обробники команд
    application.add_handler(get_setup_handler())  # Обробник налаштування
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("add", add_transaction_command))
    application.add_handler(CommandHandler("budget", budget_command))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CommandHandler("notifications", notifications_command))
    
    # Нові команди для аналітики та порад
    application.add_handler(CommandHandler("report", message_handler.handle_report_command))
    application.add_handler(CommandHandler("advice", message_handler.handle_advice_command))
    application.add_handler(CommandHandler("analyze", message_handler.handle_analyze_command))
    
    # Обробники повідомлень
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler.handle_text_message))
    application.add_handler(MessageHandler(filters.PHOTO, message_handler.handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, message_handler.handle_document))
    
    # Обробник колбеків від інлайн-кнопок
    application.add_handler(CallbackQueryHandler(callback_handler.handle_callback))
    
    # Запускаємо бота
    logger.info("Bot started. Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == '__main__':
    main()