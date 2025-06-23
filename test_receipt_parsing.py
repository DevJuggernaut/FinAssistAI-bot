#!/usr/bin/env python3
"""
Тест реальної функціональності з фотографією чека
"""
import os
import asyncio
from datetime import datetime
from services.free_receipt_parser import free_receipt_parser

async def test_receipt_parsing():
    """Тестує розпізнавання чека"""
    print("=== Тестування розпізнавання чека ===\n")
    
    # Шукаємо тестовий чек
    test_receipt_path = "/Users/abobina/telegram_bot/FinAssistAI-bot/test_receipt.jpg"
    
    if os.path.exists(test_receipt_path):
        print(f"Знайдено тестовий чек: {test_receipt_path}")
        
        try:
            # Тестуємо розпізнавання
            receipt_data = free_receipt_parser.parse_receipt(test_receipt_path)
            
            if receipt_data:
                print("\n✅ Чек успішно розпізнано!")
                print(f"Сума: {receipt_data.get('total_amount', 'невідомо')}")
                print(f"Магазин: {receipt_data.get('store_name', 'невідомо')}")
                print(f"Дата: {receipt_data.get('date', 'невідомо')}")
                print(f"Сирий текст: {receipt_data.get('raw_text', 'немає')[:100]}...")
                
                # Імітуємо структуру даних, що буде збережена в контексті
                pending_receipt = {
                    'amount': receipt_data['total_amount'],
                    'description': f"Покупка в {receipt_data.get('store_name', 'магазині')}",
                    'category_id': None,  # Буде визначено пізніше
                    'transaction_date': receipt_data.get('date', datetime.now()),
                    'file_path': test_receipt_path,
                    'store_name': receipt_data.get('store_name', 'Невідомо'),
                    'category': 'uncategorized',  # Буде визначено ML моделлю
                    'confidence': 0.0
                }
                
                print(f"\n📋 Дані для збереження в контексті:")
                for key, value in pending_receipt.items():
                    print(f"  {key}: {value}")
                
                # Імітуємо повідомлення, яке побачить користувач
                print(f"\n📱 Повідомлення для користувача:")
                print(f"✅ Чек оброблено!\n")
                print(f"🏪 Магазин: {pending_receipt['store_name']}")
                print(f"💰 Сума: {pending_receipt['amount']:.2f} грн")
                print(f"📅 Дата: {pending_receipt['transaction_date'].strftime('%d.%m.%Y')}")
                print(f"📂 Категорія: {pending_receipt['category']}")
                print(f"🎯 Впевненість: {pending_receipt['confidence']:.1%}")
                print(f"\n[Кнопка: ✅ Додати] [Кнопка: ❌ Назад]")
                
            else:
                print("❌ Не вдалося розпізнати чек")
                
        except Exception as e:
            print(f"❌ Помилка під час розпізнавання: {e}")
    else:
        print(f"❌ Тестовий чек не знайдено: {test_receipt_path}")
        
        # Покажемо доступні файли
        print("\nДоступні файли в директорії:")
        for file in os.listdir("/Users/abobina/telegram_bot/FinAssistAI-bot"):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                print(f"  - {file}")

if __name__ == "__main__":
    asyncio.run(test_receipt_parsing())
