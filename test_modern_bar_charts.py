#!/usr/bin/env python3
"""
Тест оновленого стовпчастого графіку з analytics_handler.py
Перевіряємо функцію create_bar_chart з покращеним дизайном
"""

import os
import sys
import matplotlib
matplotlib.use('Agg')

# Додаємо шлях до кореневої директорії
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers.analytics_handler import create_bar_chart
from database.models import Session, Transaction, Category, User, TransactionType
from datetime import datetime, timedelta
import random

def create_bar_chart_test_data():
    """Створюємо тестові дані для стовпчастого графіку"""
    session = Session()
    
    try:
        # Знаходимо або створюємо тестового користувача
        user = session.query(User).filter(User.telegram_id == 999999997).first()
        if not user:
            user = User(
                telegram_id=999999997,
                username="test_bar_chart_user",
                first_name="BarChart",
                last_name="Test"
            )
            session.add(user)
            session.flush()
        
        print(f"✅ Користувач створений/знайдений: ID={user.id}")
        
        # Створюємо тестові категорії
        categories_data = [
            ("Зарплата", "💰", "income"),
            ("Фріланс", "💻", "income"),
            ("Продукти", "🛒", "expense"),
            ("Транспорт", "🚗", "expense"),
            ("Розваги", "🎬", "expense"),
            ("Ресторани", "🍽️", "expense"),
            ("Комунальні", "🏠", "expense")
        ]
        
        categories = []
        for name, icon, cat_type in categories_data:
            existing_cat = session.query(Category).filter(
                Category.name == name,
                Category.user_id == user.id,
                Category.type == cat_type
            ).first()
            
            if not existing_cat:
                category = Category(
                    name=name,
                    icon=icon,
                    type=cat_type,
                    user_id=user.id
                )
                session.add(category)
                session.flush()
                categories.append(category)
            else:
                categories.append(existing_cat)
        
        print(f"✅ Створено/знайдено {len(categories)} категорій")
        
        # Очищуємо старі тестові транзакції
        session.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.description.like('ТЕСТ БАР:%')
        ).delete()
        
        # Створюємо транзакції за останній тиждень (різні дні)
        now = datetime.now()
        transactions_data = []
        
        for i in range(7):  # 7 днів
            transaction_date = now - timedelta(days=i)
            
            # Додаємо доходи (1-2 на день)
            income_cats = [cat for cat in categories if cat.type == 'income']
            for cat in income_cats[:random.randint(1, 2)]:
                amount = random.randint(1000, 5000)
                transaction = Transaction(
                    user_id=user.id,
                    category_id=cat.id,
                    amount=amount,
                    description=f"ТЕСТ БАР: {cat.name} {i}",
                    type=TransactionType.INCOME,
                    transaction_date=transaction_date
                )
                session.add(transaction)
                # Зберігаємо дані для подальшого використання
                transactions_data.append({
                    'amount': amount,
                    'type': TransactionType.INCOME,
                    'transaction_date': transaction_date,
                    'category_name': cat.name
                })
            
            # Додаємо витрати (2-4 на день)
            expense_cats = [cat for cat in categories if cat.type == 'expense']
            for cat in expense_cats[:random.randint(2, 4)]:
                amount = random.randint(100, 1500)
                transaction = Transaction(
                    user_id=user.id,
                    category_id=cat.id,
                    amount=amount,
                    description=f"ТЕСТ БАР: {cat.name} {i}",
                    type=TransactionType.EXPENSE,
                    transaction_date=transaction_date
                )
                session.add(transaction)
                # Зберігаємо дані для подальшого використання
                transactions_data.append({
                    'amount': amount,
                    'type': TransactionType.EXPENSE,
                    'transaction_date': transaction_date,
                    'category_name': cat.name
                })
        
        session.commit()
        print(f"✅ Створено {len(transactions_data)} тестових транзакцій за тиждень")
        
        # Створюємо фейкові об'єкти транзакцій для тестування
        class FakeTransaction:
            def __init__(self, data):
                self.amount = data['amount']
                self.type = data['type']
                self.transaction_date = data['transaction_date']
                self.category = FakeCategory(data['category_name'])
        
        class FakeCategory:
            def __init__(self, name):
                self.name = name
        
        fake_transactions = [FakeTransaction(data) for data in transactions_data]
        return fake_transactions
        
    except Exception as e:
        session.rollback()
        print(f"❌ Помилка створення тестових даних: {e}")
        return []
    finally:
        session.close()

async def test_modern_bar_charts():
    """Тестуємо оновлені стовпчасті графіки"""
    print("🔧 Тестування оновлених стовпчастих графіків...")
    
    # Створюємо тестові дані
    transactions = create_bar_chart_test_data()
    if not transactions:
        print("❌ Не вдалося створити тестові дані")
        return
    
    test_cases = [
        {
            "data_type": "comparison",
            "period": "week",
            "title": "Доходи vs Витрати - Тиждень",
            "filename": "test_modern_bar_chart_comparison_week.png",
            "description": "Порівняння доходів і витрат по днях тижня"
        },
        {
            "data_type": "expenses",
            "period": "week",
            "title": "Витрати по категоріях - Тиждень",
            "filename": "test_modern_bar_chart_expenses.png",
            "description": "Витрати згруповані по категоріях"
        },
        {
            "data_type": "income",
            "period": "week",
            "title": "Доходи по категоріях - Тиждень",
            "filename": "test_modern_bar_chart_income.png",
            "description": "Доходи згруповані по категоріях"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            print(f"\n📊 Тест {i}/{len(test_cases)}: {test_case['description']}")
            
            # Фільтруємо транзакції за типом
            if test_case["data_type"] == "expenses":
                filtered_transactions = [t for t in transactions if t.type == TransactionType.EXPENSE]
            elif test_case["data_type"] == "income":
                filtered_transactions = [t for t in transactions if t.type == TransactionType.INCOME]
            else:  # comparison
                filtered_transactions = transactions
            
            # Генеруємо графік
            chart_buffer = await create_bar_chart(
                filtered_transactions, 
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
            
            if file_size > 100000:  # Більше 100KB означає високу якість
                print("✅ Графік має високу якість")
            else:
                print("⚠️ Графік може мати низьку якість")
                
        except Exception as e:
            print(f"❌ Помилка тестування графіку {i}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n🎯 Перевірте згенеровані файли - графіки повинні мати:")
    print("   • Великі шрифти для всіх елементів (заголовок: 28px, осі: 24px)")
    print("   • Сучасні кольори та градієнти")
    print("   • Значення на стовпцях з великим шрифтом (16px)")
    print("   • Красиву легенду (для порівняння)")
    print("   • Якісну сітку та відступи")
    print("   • Високу роздільну здатність (300 DPI)")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_modern_bar_charts())
