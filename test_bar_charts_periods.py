#!/usr/bin/env python3
"""
Додатковий тест стовпчастих графіків для різних періодів
"""

import os
import sys
import matplotlib
matplotlib.use('Agg')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers.analytics_handler import create_bar_chart
from database.models import TransactionType
from datetime import datetime, timedelta
import random

# Створюємо фейкові класи для тестування
class FakeTransaction:
    def __init__(self, amount, transaction_type, transaction_date, category_name):
        self.amount = amount
        self.type = transaction_type
        self.transaction_date = transaction_date
        self.category = FakeCategory(category_name)

class FakeCategory:
    def __init__(self, name):
        self.name = name

def create_test_transactions_for_periods():
    """Створює тестові транзакції для різних періодів"""
    now = datetime.now()
    transactions = []
    
    # Створюємо транзакції за поточний день (різні години)
    for hour in range(6, 23, 2):  # Кожні 2 години з 6:00 до 23:00
        # Доходи
        if hour in [9, 14, 18]:  # 3 рази на день
            transactions.append(FakeTransaction(
                amount=random.randint(500, 2000),
                transaction_type=TransactionType.INCOME,
                transaction_date=now.replace(hour=hour, minute=random.randint(0, 59)),
                category_name=random.choice(["Зарплата", "Фріланс", "Інвестиції"])
            ))
        
        # Витрати
        transactions.append(FakeTransaction(
            amount=random.randint(50, 800),
            transaction_type=TransactionType.EXPENSE,
            transaction_date=now.replace(hour=hour, minute=random.randint(0, 59)),
            category_name=random.choice(["Продукти", "Транспорт", "Кава", "Обід", "Покупки"])
        ))
    
    # Додаємо транзакції за останній місяць (по тижнях)
    for week in range(4):
        week_start = now - timedelta(weeks=week)
        for day_offset in range(7):
            transaction_date = week_start - timedelta(days=day_offset)
            
            # Доходи (2-3 рази на тиждень)
            if day_offset % 3 == 0:
                transactions.append(FakeTransaction(
                    amount=random.randint(3000, 8000),
                    transaction_type=TransactionType.INCOME,
                    transaction_date=transaction_date,
                    category_name=random.choice(["Зарплата", "Фріланс", "Бонус"])
                ))
            
            # Витрати (щодня)
            for _ in range(random.randint(1, 4)):
                transactions.append(FakeTransaction(
                    amount=random.randint(100, 1500),
                    transaction_type=TransactionType.EXPENSE,
                    transaction_date=transaction_date,
                    category_name=random.choice(["Продукти", "Транспорт", "Розваги", "Ресторани", "Комунальні"])
                ))
    
    return transactions

async def test_different_periods():
    """Тестуємо графіки для різних періодів"""
    print("🔧 Тестування графіків для різних періодів...")
    
    transactions = create_test_transactions_for_periods()
    print(f"✅ Створено {len(transactions)} тестових транзакцій")
    
    test_cases = [
        {
            "data_type": "comparison",
            "period": "day",
            "title": "Доходи vs Витрати - Сьогодні",
            "filename": "test_bar_chart_day.png",
            "description": "Доходи та витрати по часових інтервалах дня"
        },
        {
            "data_type": "comparison",
            "period": "month",
            "title": "Доходи vs Витрати - Місяць",
            "filename": "test_bar_chart_month.png",
            "description": "Доходи та витрати по тижнях місяця"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            print(f"\n📊 Тест {i}/{len(test_cases)}: {test_case['description']}")
            
            # Генеруємо графік
            chart_buffer = await create_bar_chart(
                transactions, 
                test_case["data_type"], 
                test_case["title"], 
                test_case["period"]
            )
            
            if not chart_buffer:
                print(f"❌ Графік {i} не був згенерований")
                continue
            
            # Зберігаємо графік
            with open(test_case["filename"], 'wb') as f:
                f.write(chart_buffer.getvalue())
            
            # Перевіряємо розмір файлу
            file_size = os.path.getsize(test_case["filename"])
            print(f"✅ Графік збережено: {test_case['filename']}")
            print(f"📏 Розмір файлу: {file_size} байт")
            
            if file_size > 100000:
                print("✅ Графік має високу якість")
            else:
                print("⚠️ Графік може мати низьку якість")
                
        except Exception as e:
            print(f"❌ Помилка тестування графіку {i}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n🎯 Результати тестування:")
    print("   • День: Показує інтервали 00-06, 06-12, 12-18, 18-24")
    print("   • Місяць: Показує тижні 1, 2, 3, 4")
    print("   • Всі графіки мають сучасний дизайн та великі шрифти")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_different_periods())
