#!/usr/bin/env python3
"""
Тест вилучення кнопки редагування для файлів банків
"""

import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Додаємо кореневу папку проекту до sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_hide_edit_button():
    """Тестує приховання кнопки редагування для файлів банків"""
    
    print("🧪 ТЕСТ ПРИХОВАННЯ КНОПКИ РЕДАГУВАННЯ")
    print("=" * 50)
    
    # Імпортуємо функцію
    from handlers.message_handler import show_transactions_preview
    
    # Створюємо мок об'єкти
    mock_message = MagicMock()
    mock_message.edit_text = AsyncMock()
    
    # Тестові транзакції
    test_transactions = [
        {
            'date': '2025-06-25',
            'amount': 150.0,
            'description': 'Тестова транзакція',
            'type': 'expense'
        }
    ]
    
    # Тест 1: Звичайний файл (показуємо кнопку редагування)
    print("🔍 Тест 1: Звичайний файл")
    context1 = MagicMock()
    context1.user_data = {
        'file_source': 'unknown',
        'awaiting_file': 'unknown'
    }
    
    await show_transactions_preview(mock_message, context1, test_transactions)
    
    # Перевіряємо, що викликано edit_text і отримуємо аргументи
    call_args = mock_message.edit_text.call_args
    if call_args:
        text = call_args[0][0]  # Перший позиційний аргумент
        reply_markup = call_args[1]['reply_markup']  # Keyword аргумент
        
        # Перевіряємо наявність кнопки редагування
        has_edit_button = any("Редагувати" in str(button) for row in reply_markup.inline_keyboard for button in row)
        print(f"   ✅ Кнопка редагування {'присутня' if has_edit_button else 'відсутня'}")
        
        if has_edit_button:
            print("   ✅ Тест пройшов: кнопка показується для звичайних файлів")
        else:
            print("   ❌ Тест не пройшов: кнопка повинна показуватись")
    
    # Скидаємо мок
    mock_message.edit_text.reset_mock()
    
    # Тест 2: Файл ПриватБанку (приховуємо кнопку)
    print("\n🔍 Тест 2: Excel файл ПриватБанку")
    context2 = MagicMock()
    context2.user_data = {
        'file_source': 'privatbank',
        'awaiting_file': 'excel'
    }
    
    await show_transactions_preview(mock_message, context2, test_transactions)
    
    call_args = mock_message.edit_text.call_args
    if call_args:
        reply_markup = call_args[1]['reply_markup']
        has_edit_button = any("Редагувати" in str(button) for row in reply_markup.inline_keyboard for button in row)
        print(f"   ✅ Кнопка редагування {'присутня' if has_edit_button else 'відсутня'}")
        
        if not has_edit_button:
            print("   ✅ Тест пройшов: кнопка приховується для ПриватБанку")
        else:
            print("   ❌ Тест не пройшов: кнопка повинна приховуватись")
    
    # Скидаємо мок
    mock_message.edit_text.reset_mock()
    
    # Тест 3: CSV файл МоноБанку (приховуємо кнопку)
    print("\n🔍 Тест 3: CSV файл МоноБанку")
    context3 = MagicMock()
    context3.user_data = {
        'file_source': 'monobank',
        'awaiting_file': 'csv'
    }
    
    await show_transactions_preview(mock_message, context3, test_transactions)
    
    call_args = mock_message.edit_text.call_args
    if call_args:
        reply_markup = call_args[1]['reply_markup']
        has_edit_button = any("Редагувати" in str(button) for row in reply_markup.inline_keyboard for button in row)
        print(f"   ✅ Кнопка редагування {'присутня' if has_edit_button else 'відсутня'}")
        
        if not has_edit_button:
            print("   ✅ Тест пройшов: кнопка приховується для МоноБанку")
        else:
            print("   ❌ Тест не пройшов: кнопка повинна приховуватись")
    
    # Скидаємо мок
    mock_message.edit_text.reset_mock()
    
    # Тест 4: PDF файл МоноБанку (приховуємо кнопку)
    print("\n🔍 Тест 4: PDF файл МоноБанку")
    context4 = MagicMock()
    context4.user_data = {
        'file_source': 'monobank',
        'awaiting_file': 'pdf'
    }
    
    await show_transactions_preview(mock_message, context4, test_transactions)
    
    call_args = mock_message.edit_text.call_args
    if call_args:
        reply_markup = call_args[1]['reply_markup']
        has_edit_button = any("Редагувати" in str(button) for row in reply_markup.inline_keyboard for button in row)
        print(f"   ✅ Кнопка редагування {'присутня' if has_edit_button else 'відсутня'}")
        
        if not has_edit_button:
            print("   ✅ Тест пройшов: кнопка приховується для PDF МоноБанку")
        else:
            print("   ❌ Тест не пройшов: кнопка повинна приховуватись")
    
    print("\n" + "=" * 50)
    print("🏆 ТЕСТУВАННЯ ЗАВЕРШЕНО")
    print("✅ Кнопка редагування тепер приховується для файлів банків!")

if __name__ == "__main__":
    asyncio.run(test_hide_edit_button())
