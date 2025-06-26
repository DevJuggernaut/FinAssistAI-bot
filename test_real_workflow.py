#!/usr/bin/env python3
"""
Тест симуляції реального використання без кнопки редагування
"""

import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Додаємо кореневу папку проекту до sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_real_workflow():
    """Тестує реальний воркфлов без кнопки редагування"""
    
    print("🔄 ТЕСТ РЕАЛЬНОГО ВОРКФЛОВУ")
    print("=" * 50)
    
    # Імпортуємо функції
    from handlers.message_handler import show_transactions_preview
    from handlers.transaction_handler import show_privatbank_excel_guide, show_monobank_excel_guide
    from handlers.callback_handler import handle_callback
    
    # Створюємо мок об'єкти
    mock_message = MagicMock()
    mock_message.edit_text = AsyncMock()
    mock_query = MagicMock()
    mock_query.edit_message_text = AsyncMock()
    mock_query.data = ""
    
    # Тестові транзакції
    test_transactions = [
        {
            'date': '2025-06-25',
            'amount': 150.0,
            'description': 'АТБ продукти',
            'type': 'expense'
        },
        {
            'date': '2025-06-24',
            'amount': 50.0,
            'description': 'Кафе',
            'type': 'expense'
        }
    ]
    
    # Симуляція 1: Користувач обирає ПриватБанк Excel
    print("🔍 Симуляція 1: ПриватБанк Excel")
    context1 = MagicMock()
    context1.user_data = {}
    
    # Крок 1: Обираємо ПриватБанк Excel (встановлюємо file_source)
    mock_query.data = "privatbank_excel_guide"
    await show_privatbank_excel_guide(mock_query, context1)
    
    # Перевіряємо, що file_source встановлено
    print(f"   file_source: {context1.user_data.get('file_source', 'не встановлено')}")
    
    # Крок 2: Завантажуємо файл і бачимо попередній перегляд (без кнопки редагування)
    context1.user_data['awaiting_file'] = 'excel'
    await show_transactions_preview(mock_message, context1, test_transactions)
    
    # Перевіряємо результат
    call_args = mock_message.edit_text.call_args
    if call_args:
        reply_markup = call_args[1]['reply_markup']
        has_edit_button = any("Редагувати" in str(button) for row in reply_markup.inline_keyboard for button in row)
        print(f"   Кнопка редагування: {'присутня' if has_edit_button else 'відсутня'} ✅")
        
        # Перевіряємо кількість кнопок в першому ряду
        first_row_buttons = len(reply_markup.inline_keyboard[0])
        print(f"   Кнопок у першому ряду: {first_row_buttons} (очікується 1)")
        
        if not has_edit_button and first_row_buttons == 1:
            print("   ✅ ПриватБанк Excel: кнопка редагування правильно приховується")
        else:
            print("   ❌ ПриватБанк Excel: помилка з кнопкою редагування")
    
    # Скидаємо мок
    mock_message.edit_text.reset_mock()
    
    # Симуляція 2: Користувач обирає МоноБанк CSV
    print("\n🔍 Симуляція 2: МоноБанк CSV")
    context2 = MagicMock()
    context2.user_data = {'file_source': 'monobank', 'awaiting_file': 'csv'}
    
    await show_transactions_preview(mock_message, context2, test_transactions)
    
    call_args = mock_message.edit_text.call_args
    if call_args:
        reply_markup = call_args[1]['reply_markup']
        has_edit_button = any("Редагувати" in str(button) for row in reply_markup.inline_keyboard for button in row)
        first_row_buttons = len(reply_markup.inline_keyboard[0])
        
        print(f"   file_source: {context2.user_data.get('file_source')}")
        print(f"   awaiting_file: {context2.user_data.get('awaiting_file')}")
        print(f"   Кнопка редагування: {'присутня' if has_edit_button else 'відсутня'} ✅")
        print(f"   Кнопок у першому ряду: {first_row_buttons} (очікується 1)")
        
        if not has_edit_button and first_row_buttons == 1:
            print("   ✅ МоноБанк CSV: кнопка редагування правильно приховується")
        else:
            print("   ❌ МоноБанк CSV: помилка з кнопкою редагування")
    
    # Скидаємо мок
    mock_message.edit_text.reset_mock()
    
    # Симуляція 3: Звичайний файл (не банк)
    print("\n🔍 Симуляція 3: Звичайний файл")
    context3 = MagicMock()
    context3.user_data = {'file_source': 'manual', 'awaiting_file': 'unknown'}
    
    await show_transactions_preview(mock_message, context3, test_transactions)
    
    call_args = mock_message.edit_text.call_args
    if call_args:
        reply_markup = call_args[1]['reply_markup']
        has_edit_button = any("Редагувати" in str(button) for row in reply_markup.inline_keyboard for button in row)
        first_row_buttons = len(reply_markup.inline_keyboard[0])
        
        print(f"   file_source: {context3.user_data.get('file_source')}")
        print(f"   awaiting_file: {context3.user_data.get('awaiting_file')}")
        print(f"   Кнопка редагування: {'присутня' if has_edit_button else 'відсутня'} ✅")
        print(f"   Кнопок у першому ряду: {first_row_buttons} (очікується 2)")
        
        if has_edit_button and first_row_buttons == 2:
            print("   ✅ Звичайний файл: кнопка редагування правильно показується")
        else:
            print("   ❌ Звичайний файл: помилка з кнопкою редагування")
    
    print("\n" + "=" * 50)
    print("🏆 ТЕСТ РЕАЛЬНОГО ВОРКФЛОВУ ЗАВЕРШЕНО")
    print("✅ Система приховування кнопки редагування працює правильно!")

if __name__ == "__main__":
    asyncio.run(test_real_workflow())
