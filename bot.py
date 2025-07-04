import logging
import os
import sys
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler
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
from handlers.setup_callbacks import (
    show_currency_selection, process_currency_selection, back_to_currency,
    process_initial_balance, complete_setup,
    WAITING_CURRENCY_SELECTION, WAITING_BALANCE_INPUT, SETUP_COMPLETE
)
from handlers.ai_assistant_handler import handle_ai_question, WAITING_AI_QUESTION
from database.session import init_db
from database.cleanup import clear_all_tables, reset_database
from services.statement_parser import StatementParser, ReceiptProcessor
from services.ml_categorizer import TransactionCategorizer
from services.openai_service import OpenAIService
from services.analytics_service import AnalyticsService
from services.tavria_receipt_parser import TavriaReceiptParser

# Опціонально: імпортуємо health server для Render
try:
    from health_server import start_health_server
    HEALTH_SERVER_AVAILABLE = True
except ImportError:
    HEALTH_SERVER_AVAILABLE = False

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
tavria_receipt_parser = TavriaReceiptParser()

def main():
    """Запуск бота"""
    # Запускаємо health server для Render (опціонально)
    if HEALTH_SERVER_AVAILABLE:
        health_server = start_health_server()
        if health_server:
            logger.info(f"Health server started on port {os.getenv('PORT', 8000)}")
    
    # Визначаємо, чи знаходимось в режимі розробки
    dev_mode = os.environ.get('DEV_MODE', 'false').lower() == 'true'
    
    # Очищаємо базу даних, якщо це режим розробки
    if dev_mode:
        try:
            logger.info("Запуск у режимі розробки - очищаємо базу даних...")
            clear_all_tables()
        except Exception as e:
            logger.error(f"Не вдалося очистити базу даних: {e}")
            logger.info("Спроба повного скидання бази даних...")
            try:
                reset_database()
            except Exception as e:
                logger.error(f"Не вдалося скинути базу даних: {e}")
                logger.error("Продовження роботи з існуючою базою даних")
    
    # Ініціалізуємо базу даних
    init_db()
    
    # Створюємо застосунок
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Додаємо обробники команд
    application.add_handler(get_setup_handler())  # Обробник налаштування
    
    # Додаємо обробник для початкового налаштування
    # Використовуємо один ConversationHandler для всього процесу налаштування
    setup_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(show_currency_selection, pattern="^setup_initial_balance$")],
        states={
            WAITING_CURRENCY_SELECTION: [
                CallbackQueryHandler(process_currency_selection, pattern="^currency_"),
                CallbackQueryHandler(callback_handler.back_to_main, pattern="^back_to_main$")
            ],
            WAITING_BALANCE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_initial_balance),
                CallbackQueryHandler(back_to_currency, pattern="^back_to_currency$")
            ]
        },
        fallbacks=[CallbackQueryHandler(callback_handler.back_to_main, pattern="^back_to_main$")]
    )
    application.add_handler(setup_handler)
    
    # AI Assistant ConversationHandler
    from handlers.ai_assistant_handler import start_ai_question
    ai_assistant_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_ai_question, pattern="^ai_custom_question$")],
        states={
            WAITING_AI_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_question)
            ]
        },
        fallbacks=[CallbackQueryHandler(callback_handler.back_to_main, pattern="^back_to_main$")]
    )
    application.add_handler(ai_assistant_handler)
    
    # Додаємо обробник для callback "complete_setup"
    application.add_handler(CallbackQueryHandler(complete_setup, pattern="^complete_setup$"))
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
    application.add_handler(MessageHandler(filters.Document.ALL, message_handler.handle_document_message))
    
    # Обробник колбеків від інлайн-кнопок
    application.add_handler(CallbackQueryHandler(callback_handler.handle_callback))
    
    # Запускаємо бота
    logger.info("FinAssistAI Bot started successfully! Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == '__main__':
    main()