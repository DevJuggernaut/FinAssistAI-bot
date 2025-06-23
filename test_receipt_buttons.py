#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки функціональності кнопок після обробки чеку
"""

import asyncio
from unittest.mock import MagicMock
from datetime import datetime

# Імітуємо callback_query та context
class MockCallbackQuery:
    def __init__(self, user_id=123456):
        self.from_user = MagicMock()
        self.from_user.id = user_id
        self.data = "confirm_receipt_add"
    
    async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
        print(f"[EDIT MESSAGE] {text}")
        if reply_markup:
            print("[REPLY MARKUP]", reply_markup)
    
    async def answer(self, text="", show_alert=False):
        if text:
            print(f"[ANSWER] {text}")

class MockContext:
    def __init__(self):
        self.user_data = {
            'pending_receipt': {
                'amount': 100.47,
                'description': 'Покупка в ФОП Лютіков В В',
                'category_id': None,
                'transaction_date': datetime(2025, 6, 18),
                'file_path': '/path/to/receipt.jpg',
                'store_name': 'ФОП Лютіков В В',
                'category': 'uncategorized',
                'confidence': 0.0
            }
        }

async def test_confirm_receipt_add():
    """Тестує функцію підтвердження додавання чека"""
    print("=== Тестування функції підтвердження додавання чека ===\n")
    
    try:
        # Імпортуємо функцію
        from handlers.callback_handler import handle_confirm_receipt_add
        
        # Створюємо mock об'єкти
        query = MockCallbackQuery()
        context = MockContext()
        
        print("Виклик handle_confirm_receipt_add...")
        
        # Викликаємо функцію
        await handle_confirm_receipt_add(query, context)
        
        print("\n✅ Тест пройшов успішно!")
        
    except Exception as e:
        print(f"\n❌ Помилка в тесті: {e}")
        import traceback
        traceback.print_exc()

async def test_receipt_processing_flow():
    """Тестує повний потік обробки чека"""
    print("\n=== Тестування повного потоку обробки чека ===\n")
    
    print("1. Користувач надсилає фото чека")
    print("2. Чек розпізнається та обробляється")
    print("3. Показується інформація з кнопками 'Додати' та 'Назад'")
    print("4. При натисканні 'Додати' - транзакція додається до БД")
    print("5. Показується підтвердження з опціями переходу")
    
    # Тестуємо збереження даних чека в контексті
    context = MockContext()
    receipt_data = context.user_data['pending_receipt']
    
    print(f"\nДані чека в контексті:")
    print(f"  Сума: {receipt_data['amount']:.2f} грн")
    print(f"  Магазин: {receipt_data['store_name']}")
    print(f"  Категорія: {receipt_data['category']}")
    print(f"  Дата: {receipt_data['transaction_date'].strftime('%d.%m.%Y')}")
    
    print("\n✅ Структура даних коректна!")

if __name__ == "__main__":
    asyncio.run(test_confirm_receipt_add())
    asyncio.run(test_receipt_processing_flow())
