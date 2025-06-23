#!/usr/bin/env python3
"""
Тест для перевірки виправлення помилки з datetime
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.ai_assistant_handler import generate_personal_advice

async def test_fixed_datetime_error():
    """Тестує виправлення помилки з datetime"""
    print("🔧 Тестування виправлення datetime помилки...")
    
    # Створюємо тестового користувача
    class TestUser:
        def __init__(self):
            self.id = 123456
            self.monthly_budget = 15000
            self.currency = "UAH"
    
    # Створюємо тестові транзакції з різними форматами дат
    test_transactions = [
        {
            'amount': 500.0,
            'category': 'Їжа',
            'type': 'expense',
            'date': '2025-06-20T10:30:00',  # ISO формат
            'description': 'Супермаркет'
        },
        {
            'amount': 200.0,
            'category': 'Транспорт',
            'type': 'expense',
            'date': '2025-06-18',  # Простий формат дати
            'description': 'Метро'
        },
        {
            'amount': 25000.0,
            'category': 'Зарплата',
            'type': 'income',
            'date': datetime.now().isoformat(),  # Поточна дата
            'description': 'Місячна зарплата'
        }
    ]
    
    user = TestUser()
    
    try:
        advice = await generate_personal_advice(user, test_transactions)
        print("✅ Тест пройшов успішно!")
        print("📝 Отримана порада:")
        print(advice[:200] + "..." if len(advice) > 200 else advice)
        return True
    except Exception as e:
        print(f"❌ Тест не пройшов: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_fixed_datetime_error())
    print(f"\n🎯 Результат: {'УСПІШНО' if success else 'ПОМИЛКА'}")
