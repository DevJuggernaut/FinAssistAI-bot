#!/usr/bin/env python3
"""
Демонстрація повного workflow додавання транзакцій через Telegram бота
"""

import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Додаємо шлях до проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from handlers.transaction_handler import (
    show_add_transaction_menu,
    show_upload_statement_form,
    handle_remove_duplicates,
    handle_set_import_period
)
from handlers.message_handler import handle_document_message, show_transactions_preview

async def demo_transaction_workflow():
    """Демонстрація workflow додавання транзакцій"""
    
    print("🎯 Демонстрація розширеної вкладки 'Додати транзакції'")
    print("=" * 60)
    
    # Імітуємо Telegram объекти
    mock_query = Mock()
    mock_query.edit_message_text = AsyncMock()
    mock_query.message = Mock()
    mock_query.message.reply_text = AsyncMock()
    mock_query.message.edit_text = AsyncMock()
    
    mock_context = Mock()
    mock_context.user_data = {}
    
    # 1. Показуємо головне меню додавання транзакцій
    print("1️⃣ Показуємо головне меню додавання транзакцій:")
    await show_add_transaction_menu(mock_query, mock_context)
    
    # Отримуємо текст повідомлення з mock об'єкта
    call_args = mock_query.edit_message_text.call_args
    if call_args:
        message_text = call_args[0][0] if call_args[0] else call_args[1].get('text', '')
        print(f"📱 Повідомлення боту:\n{message_text}")
    
    print("\n" + "-" * 40)
    
    # 2. Показуємо форму завантаження виписки
    print("2️⃣ Користувач обирає 'Завантажити виписку':")
    await show_upload_statement_form(mock_query, mock_context)
    
    call_args = mock_query.edit_message_text.call_args
    if call_args:
        message_text = call_args[0][0] if call_args[0] else call_args[1].get('text', '')
        print(f"📱 Повідомлення боту:\n{message_text}")
    
    print("\n" + "-" * 40)
    
    # 3. Імітуємо розпізнані транзакції
    print("3️⃣ Імітуємо успішне розпізнавання транзакцій з файлу:")
    
    mock_transactions = [
        {
            'date': datetime(2024, 5, 20),
            'amount': 150.75,
            'description': 'Покупки в супермаркеті',
            'type': 'expense',
            'category': 'Продукти'
        },
        {
            'date': datetime(2024, 5, 21),
            'amount': 3000.00,
            'description': 'Зарплата',
            'type': 'income',
            'category': 'Дохід'
        },
        {
            'date': datetime(2024, 5, 22),
            'amount': 89.50,
            'description': 'Кафе на роботі',
            'type': 'expense',
            'category': 'Кафе та ресторани'
        }
    ]
    
    mock_context.user_data['parsed_transactions'] = mock_transactions
    
    # Показуємо попередній перегляд
    await show_transactions_preview(mock_query.message, mock_context, mock_transactions)
    
    call_args = mock_query.message.edit_text.call_args
    if call_args:
        message_text = call_args[0][0] if call_args[0] else call_args[1].get('text', '')
        print(f"📱 Попередній перегляд транзакцій:\n{message_text}")
    
    print("\n" + "-" * 40)
    
    # 4. Демонстрація функції видалення дублікатів
    print("4️⃣ Користувач натискає 'Виключити дублікати':")
    
    # Додаємо дублікат
    mock_transactions.append({
        'date': datetime(2024, 5, 20),
        'amount': 150.75,
        'description': 'Покупки в супермаркеті (дублікат)',
        'type': 'expense',
        'category': 'Продукти'
    })
    
    mock_context.user_data['parsed_transactions'] = mock_transactions
    
    mock_query.data = "remove_duplicates"
    await handle_remove_duplicates(mock_query, mock_context)
    
    print(f"🧹 Видалено дублікатів. Залишилось транзакцій: {len(mock_context.user_data['parsed_transactions'])}")
    
    print("\n" + "-" * 40)
    
    # 5. Демонстрація налаштування періоду
    print("5️⃣ Користувач налаштовує період імпорту:")
    
    await handle_set_import_period(mock_query, mock_context)
    
    call_args = mock_query.edit_message_text.call_args
    if call_args:
        message_text = call_args[0][0] if call_args[0] else call_args[1].get('text', '')
        print(f"📱 Налаштування періоду:\n{message_text}")
    
    print("\n" + "=" * 60)
    print("✅ Демонстрація завершена!")
    print("\n🎉 Основні функції розширеної вкладки 'Додати транзакції':")
    print("  ✓ Три способи додавання: ручне, виписка, фото чеку")
    print("  ✓ Автоматичний парсинг PDF, Excel, CSV файлів")
    print("  ✓ Попередній перегляд з можливістю редагування")
    print("  ✓ Видалення дублікатів")
    print("  ✓ Налаштування періоду імпорту")
    print("  ✓ Валідація та автокатегоризація")

def main():
    """Запуск демонстрації"""
    asyncio.run(demo_transaction_workflow())

if __name__ == "__main__":
    main()
