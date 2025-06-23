#!/usr/bin/env python3
"""
Тест фільтрації транзакцій
"""

from database.models import TransactionType
from database.db_operations import get_transactions, get_or_create_user
from datetime import datetime, timedelta
import calendar

def test_transaction_filters():
    """Тестуємо всі типи фільтрів"""
    print("🧪 Тестування фільтрів транзакцій...")
    
    # Отримуємо тестового користувача
    user = get_or_create_user(580683833)
    print(f"👤 Користувач: {user.first_name} (ID: {user.id})")
    
    # Тест 1: Всі транзакції
    all_transactions = get_transactions(user.id, limit=100)
    print(f"📊 Всього транзакцій: {len(all_transactions)}")
    
    # Тест 2: Фільтр по типу
    income_transactions = get_transactions(user.id, limit=100, transaction_type=TransactionType.INCOME)
    expense_transactions = get_transactions(user.id, limit=100, transaction_type=TransactionType.EXPENSE)
    print(f"💰 Доходів: {len(income_transactions)}")
    print(f"💸 Витрат: {len(expense_transactions)}")
    
    # Тест 3: Фільтр по періоду (поточний місяць)
    today = datetime.now()
    start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day = calendar.monthrange(today.year, today.month)[1]
    end_date = today.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    
    month_transactions = get_transactions(
        user.id, 
        limit=100, 
        start_date=start_date, 
        end_date=end_date
    )
    print(f"📅 Транзакції за поточний місяць: {len(month_transactions)}")
    
    # Тест 4: Комбінований фільтр (витрати за місяць)
    month_expenses = get_transactions(
        user.id,
        limit=100,
        transaction_type=TransactionType.EXPENSE,
        start_date=start_date,
        end_date=end_date
    )
    print(f"💸 Витрати за поточний місяць: {len(month_expenses)}")
    
    # Перевірка валідності
    assert len(income_transactions) + len(expense_transactions) <= len(all_transactions), "Помилка в фільтрації по типу"
    assert len(month_transactions) <= len(all_transactions), "Помилка в фільтрації по даті"
    assert len(month_expenses) <= len(month_transactions), "Помилка в комбінованій фільтрації"
    
    print("✅ Всі тести фільтрів пройшли успішно!")
    
    # Показуємо приклад транзакцій
    if all_transactions:
        print("\n📝 Приклад транзакцій:")
        for i, t in enumerate(all_transactions[:3]):
            type_text = "Дохід" if t.type == TransactionType.INCOME else "Витрата"
            print(f"{i+1}. {t.transaction_date.strftime('%d.%m.%Y')} - {type_text}: {t.amount} UAH ({t.description})")

if __name__ == "__main__":
    test_transaction_filters()
