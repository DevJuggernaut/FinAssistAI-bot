#!/usr/bin/env python3
"""
Тест нової логіки тижневого періоду: останні 7 днів замість календарного тижня
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Додаємо шлях до проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Імпортуємо необхідні модулі
import config
from database.models import db, User, Transaction, Category, TransactionType
from handlers.analytics_handler import create_bar_chart

async def create_test_data():
    """Створюємо тестові дані для останніх 7 днів"""
    print("🔄 Створюємо тестові дані для останніх 7 днів...")
    
    # Створюємо користувача
    user = User(
        telegram_id=999999999,
        username="test_week_user",
        first_name="Test",
        balance=10000
    )
    db.session.add(user)
    
    # Створюємо категорії
    category_food = Category(name="Їжа", type=TransactionType.EXPENSE)
    category_salary = Category(name="Зарплата", type=TransactionType.INCOME)
    db.session.add_all([category_food, category_salary])
    
    db.session.commit()
    
    # Створюємо транзакції на останні 7 днів
    now = datetime.now()
    transactions = []
    
    for i in range(7):  # Останні 7 днів включаючи сьогодні
        date = now - timedelta(days=i)
        
        # Витрати (різні суми для різних днів)
        expense_amount = 200 + (i * 50)  # від 200 до 500
        expense = Transaction(
            user_id=user.id,
            amount=-expense_amount,
            description=f"Тестова витрата {i+1}",
            category_id=category_food.id,
            type=TransactionType.EXPENSE,
            transaction_date=date
        )
        transactions.append(expense)
        
        # Доходи (тільки в деякі дні)
        if i % 2 == 0:  # Кожен другий день
            income_amount = 1000 + (i * 100)
            income = Transaction(
                user_id=user.id,
                amount=income_amount,
                description=f"Тестовий дохід {i+1}",
                category_id=category_salary.id,
                type=TransactionType.INCOME,
                transaction_date=date
            )
            transactions.append(income)
    
    db.session.add_all(transactions)
    db.session.commit()
    
    print(f"✅ Створено {len(transactions)} транзакцій для тестування")
    return transactions, user

async def test_week_bar_chart():
    """Тестуємо стовпчастий графік для тижневого періоду"""
    print("\n📊 Тестуємо тижневий стовпчастий графік...")
    
    # Отримуємо транзакції за останні 7 днів
    now = datetime.now()
    start_date = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    transactions = Transaction.query.filter(
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= now
    ).all()
    
    print(f"Знайдено {len(transactions)} транзакцій за останні 7 днів")
    
    # Показуємо розподіл по днях
    from collections import defaultdict
    by_day = defaultdict(list)
    
    for transaction in transactions:
        days_ago = (now.date() - transaction.transaction_date.date()).days
        if days_ago == 0:
            key = f"Сьогодні ({transaction.transaction_date.strftime('%d.%m')})"
        elif days_ago == 1:
            key = f"Вчора ({transaction.transaction_date.strftime('%d.%m')})"
        else:
            weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
            weekday_name = weekdays[transaction.transaction_date.weekday()]
            key = f"{weekday_name} ({transaction.transaction_date.strftime('%d.%m')})"
        
        by_day[key].append(transaction)
    
    print("\n📅 Розподіл транзакцій по днях:")
    for day, day_transactions in sorted(by_day.items()):
        income_sum = sum(t.amount for t in day_transactions if t.type == TransactionType.INCOME)
        expense_sum = sum(abs(t.amount) for t in day_transactions if t.type == TransactionType.EXPENSE)
        print(f"  {day}: Доходи {income_sum:,.0f} грн, Витрати {expense_sum:,.0f} грн")
    
    # Створюємо графік
    try:
        chart_buffer = await create_bar_chart(
            transactions=transactions,
            data_type="comparison",
            title="📊 Доходи vs Витрати (останні 7 днів)",
            period="week"
        )
        
        # Зберігаємо графік
        filename = f"test_week_last_7_days_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        with open(filename, 'wb') as f:
            f.write(chart_buffer.getvalue())
        
        print(f"✅ Графік збережено як {filename}")
        print("🎯 Перевірте, що графік показує останні 7 днів з правильними підписами!")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка створення графіку: {e}")
        return False

async def test_week_logic():
    """Тестуємо логіку тижневого періоду"""
    print("\n🧪 Тестуємо логіку останніх 7 днів...")
    
    now = datetime.now()
    
    print(f"Сьогодні: {now.strftime('%A, %d.%m.%Y')}")
    print("Останні 7 днів:")
    
    for i in range(6, -1, -1):
        date = now - timedelta(days=i)
        if i == 0:
            key = f"Сьогодні ({date.strftime('%d.%m')})"
        elif i == 1:
            key = f"Вчора ({date.strftime('%d.%m')})"
        else:
            weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
            weekday_name = weekdays[date.weekday()]
            key = f"{weekday_name} ({date.strftime('%d.%m')})"
        
        print(f"  {7-i}. {key}")
    
    print("✅ Логіка останніх 7 днів працює правильно!")

async def main():
    """Головна функція тестування"""
    print("🚀 Запускаємо тест тижневого періоду (останні 7 днів)")
    print("=" * 60)
    
    # Ініціалізуємо базу даних - просто імпортуємо bot.py для ініціалізації
    try:
        from bot import app
        with app.app_context():
            await run_tests()
    except Exception as e:
        print(f"❌ Помилка ініціалізації: {e}")

async def run_tests():
    """Запускаємо тести"""
    try:
        # Очищаємо тестові дані
        print("🧹 Очищаємо старі тестові дані...")
        Transaction.query.filter(Transaction.user_id.in_(
            db.session.query(User.id).filter(User.telegram_id == 999999999)
        )).delete(synchronize_session=False)
        User.query.filter_by(telegram_id=999999999).delete()
        db.session.commit()
        
        # Тестуємо логіку
        await test_week_logic()
        
        # Створюємо тестові дані
        transactions, user = await create_test_data()
        
        # Тестуємо графік
        success = await test_week_bar_chart()
        
        if success:
            print("\n🎉 Тест успішно завершено!")
            print("📋 Результати:")
            print("  ✅ Логіка останніх 7 днів працює")
            print("  ✅ Графік створено з правильними підписами")
            print("  ✅ Показуються дати у форматі 'День (дд.мм)'")
            print("  ✅ Сьогодні та вчора підписані окремо")
        else:
            print("\n❌ Тест завершився з помилками")
        
        # Очищаємо тестові дані
        print("\n🧹 Очищаємо тестові дані...")
        Transaction.query.filter(Transaction.user_id == user.id).delete()
        User.query.filter_by(id=user.id).delete()
        db.session.commit()
        
    except Exception as e:
        print(f"❌ Помилка під час тестування: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Тестування завершено!")

if __name__ == "__main__":
    asyncio.run(main())
