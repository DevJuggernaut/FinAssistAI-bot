#!/usr/bin/env python3
"""
Тест візуальних роздільників для категорій у меню фільтрів
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import MagicMock, AsyncMock
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from handlers.transaction_handler import show_category_filter_menu
from database.models import Category, TransactionType

def test_visual_separators():
    """Тестує додавання візуальних роздільників для категорій"""
    
    # Моки
    query = MagicMock()
    query.from_user.id = 123
    query.edit_message_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {
        'transaction_filters': {'category': 'all'}
    }
    
    # Тестові дані - категорії
    test_categories = [
        Category(id=1, name="Продукти", type=TransactionType.EXPENSE.value, icon="🛒", user_id=123),
        Category(id=2, name="Транспорт", type=TransactionType.EXPENSE.value, icon="🚗", user_id=123),
        Category(id=3, name="Зарплата", type=TransactionType.INCOME.value, icon="💰", user_id=123),
        Category(id=4, name="Бонуси", type=TransactionType.INCOME.value, icon="🎁", user_id=123),
        Category(id=5, name="Кафе", type=TransactionType.EXPENSE.value, icon="☕", user_id=123),
    ]
    
    # Мок для get_user
    def mock_get_user(user_id):
        user_mock = MagicMock()
        user_mock.id = user_id
        return user_mock
    
    # Мок для get_user_categories
    def mock_get_user_categories(user_id):
        return test_categories
    
    # Патчимо функції
    import handlers.transaction_handler
    original_get_user = handlers.transaction_handler.get_user
    original_get_user_categories = handlers.transaction_handler.get_user_categories
    
    handlers.transaction_handler.get_user = mock_get_user
    handlers.transaction_handler.get_user_categories = mock_get_user_categories
    
    try:
        # Тестуємо функцію
        import asyncio
        
        async def run_test():
            await show_category_filter_menu(query, context, page=1)
            
            # Перевіряємо що функція була викликана
            assert query.edit_message_text.called, "edit_message_text should be called"
            
            # Отримуємо аргументи виклику
            call_args = query.edit_message_text.call_args
            
            # Перевіряємо структуру аргументів
            if call_args is None:
                print("❌ Функція edit_message_text не була викликана")
                return False
            
            # Отримуємо аргументи та kwargs
            args = call_args[0] if call_args[0] else []
            kwargs = call_args[1] if call_args[1] else {}
            
            text = args[0] if args else kwargs.get('text', '')
            reply_markup = kwargs.get('reply_markup', None)
            
            if not reply_markup:
                print("❌ reply_markup не знайдено в аргументах")
                return False
            
            print("📄 Текст повідомлення:")
            print(text)
            print("\n" + "="*50 + "\n")
            
            print("🎛️ Структура клавіатури:")
            for i, row in enumerate(reply_markup.inline_keyboard):
                print(f"Ряд {i+1}:")
                for j, button in enumerate(row):
                    button_text = button.text
                    callback_data = button.callback_data
                    print(f"  Кнопка {j+1}: '{button_text}' -> '{callback_data}'")
            
            # Перевіряємо наявність роздільників
            keyboard_buttons = []
            for row in reply_markup.inline_keyboard:
                for button in row:
                    keyboard_buttons.append((button.text, button.callback_data))
            
            # Шукаємо роздільники
            expense_separator_found = any("💸 ── ВИТРАТИ ──" in text for text, _ in keyboard_buttons)
            income_separator_found = any("💰 ── ДОХОДИ ──" in text for text, _ in keyboard_buttons)
            
            print(f"\n✅ Результати перевірки:")
            print(f"   Роздільник витрат знайдено: {expense_separator_found}")
            print(f"   Роздільник доходів знайдено: {income_separator_found}")
            
            # Перевіряємо що роздільники використовують правильний callback
            noop_callbacks = [callback for text, callback in keyboard_buttons if callback == "noop_header"]
            print(f"   Кількість noop_header callbacks: {len(noop_callbacks)}")
            
            # Додаткові перевірки структури
            expense_categories = [cat for cat in test_categories if cat.type == TransactionType.EXPENSE.value]
            income_categories = [cat for cat in test_categories if cat.type == TransactionType.INCOME.value]
            
            print(f"\n📊 Статистика категорій:")
            print(f"   Категорії витрат: {len(expense_categories)}")
            print(f"   Категорії доходів: {len(income_categories)}")
            print(f"   Загалом категорій: {len(test_categories)}")
            
            return expense_separator_found and income_separator_found
        
        # Запускаємо тест
        result = asyncio.run(run_test())
        
        if result:
            print(f"\n🎉 Тест пройшов успішно! Візуальні роздільники працюють коректно.")
        else:
            print(f"\n❌ Тест не пройшов. Роздільники не знайдено.")
            
    finally:
        # Відновлюємо оригінальні функції
        handlers.transaction_handler.get_user = original_get_user
        handlers.transaction_handler.get_user_categories = original_get_user_categories

if __name__ == "__main__":
    print("🔍 Тестування візуальних роздільників для категорій...")
    test_visual_separators()
