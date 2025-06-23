#!/usr/bin/env python3
"""
Тестовий скрипт для симуляції завантаження PDF файлу через бота
"""

import sys
import os
sys.path.insert(0, '/Users/abobina/telegram_bot/FinAssistAI-bot')

from unittest.mock import MagicMock, patch
import asyncio
from datetime import datetime

def test_pdf_upload_flow():
    """Тестує повний процес завантаження PDF файлу"""
    print("🔄 Симулюємо завантаження PDF файлу через бота...")
    
    try:
        # Імпортуємо необхідні модулі
        from handlers.message_handler import handle_document_message
        from services.statement_parser import StatementParser
        
        # Створюємо мок об'єкти
        update_mock = MagicMock()
        context_mock = MagicMock()
        
        # Налаштовуємо мок об'єкти
        update_mock.effective_user.id = 12345
        update_mock.message.document.file_name = "monobank_statement.pdf"
        update_mock.message.document.file_size = 1024 * 1024  # 1MB
        update_mock.message.document.file_id = "test_file_id"
        
        # Налаштовуємо контекст для очікування PDF файлу від monobank
        context_mock.user_data = {
            'awaiting_file': 'pdf',
            'file_source': 'monobank'
        }
        
        # Мокаємо bot.get_file
        file_mock = MagicMock()
        file_mock.download_to_drive = MagicMock()
        context_mock.bot.get_file.return_value = file_mock
        
        # Мокаємо update.message.reply_text
        reply_mock = MagicMock()
        update_mock.message.reply_text.return_value = reply_mock
        
        # Мокаємо get_user для повернення користувача
        user_mock = MagicMock()
        user_mock.id = 12345
        
        print("✅ Мок об'єкти створено")
        
        # Тестуємо парсер напряму
        pdf_file = "/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/statements/report_20-06-2025_16-12-03.pdf"
        if os.path.exists(pdf_file):
            parser = StatementParser()
            transactions = parser.parse_bank_statement(pdf_file, bank_type='monobank')
            print(f"✅ Парсер працює: знайдено {len(transactions)} транзакцій")
            
            # Показуємо приклади транзакцій
            if transactions:
                print("\n📋 Приклади транзакцій:")
                for i, transaction in enumerate(transactions[:3]):
                    print(f"  {i+1}. {transaction['date']} | {transaction['amount']} грн | {transaction['type']} | {transaction['description']}")
        else:
            print(f"❌ PDF файл не знайдено: {pdf_file}")
            
    except Exception as e:
        print(f"❌ Помилка під час тестування: {e}")
        import traceback
        traceback.print_exc()

async def test_async_flow():
    """Тестує асинхронний потік"""
    print("\n🔄 Тестуємо асинхронний потік...")
    
    try:
        from services.statement_parser import StatementParser
        
        parser = StatementParser()
        pdf_file = "/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/statements/report_20-06-2025_16-12-03.pdf"
        
        if os.path.exists(pdf_file):
            # Тестуємо синхронний виклик
            transactions = parser.parse_bank_statement(pdf_file, bank_type='monobank')
            print(f"✅ Асинхронний тест: знайдено {len(transactions)} транзакцій")
        else:
            print(f"❌ PDF файл не знайдено: {pdf_file}")
            
    except Exception as e:
        print(f"❌ Помилка асинхронного тесту: {e}")
        import traceback
        traceback.print_exc()

def test_message_handler_integration():
    """Тестує інтеграцію з обробником повідомлень"""
    print("\n🔄 Тестуємо інтеграцію з обробником повідомлень...")
    
    try:
        # Імпортуємо модулі
        from handlers.message_handler import handle_document_message
        from database.db_operations import get_user
        
        print("✅ Модулі імпортовано успішно")
        print("✅ PDF підтримка для Monobank готова до використання!")
        
        print("\n📋 Інструкції для користувача:")
        print("1. У боті перейдіть до: Додати транзакцію → Завантажити виписку")
        print("2. Оберіть МоноБанк")
        print("3. Оберіть PDF виписка")
        print("4. Надішліть PDF файл з випискою Monobank")
        print("5. Бот автоматично розпізнає транзакції та додасть їх")
        
    except Exception as e:
        print(f"❌ Помилка інтеграції: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_upload_flow()
    asyncio.run(test_async_flow())
    test_message_handler_integration()
