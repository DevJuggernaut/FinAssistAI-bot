#!/usr/bin/env python3
"""
Тестування виправлення проблеми з редагуванням категорій транзакцій
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_operations import get_user_categories, get_transaction_by_id, get_user
from database.models import TransactionType

def test_category_edit_issue():
    """Тестує проблему з редагуванням категорій"""
    print("=== Тестування проблеми з редагуванням категорій ===\n")
    
    # Припустимо, що є користувач з ID 580683833 (реальний telegram_id)
    test_telegram_id = 580683833
    
    # Отримуємо користувача
    user = get_user(test_telegram_id)
    if not user:
        print(f"❌ Користувач з Telegram ID {test_telegram_id} не знайдений")
        return
    
    print(f"✅ Користувач знайдений: {user.telegram_id}")
    
    # Перевіряємо категорії користувача
    all_categories = get_user_categories(user.id)
    print(f"📂 Всього категорій у користувача: {len(all_categories)}")
    
    if all_categories:
        print("Список категорій:")
        for cat in all_categories:
            print(f"  - {cat.name} ({cat.type}) - ID: {cat.id}")
    else:
        print("❌ У користувача немає категорій!")
        return
    
    # Перевіряємо категорії за типами
    expense_categories = get_user_categories(user.id, category_type="expense")
    income_categories = get_user_categories(user.id, category_type="income")
    
    print(f"\n💸 Категорії витрат: {len(expense_categories)}")
    for cat in expense_categories:
        print(f"  - {cat.name}")
    
    print(f"\n💰 Категорії доходів: {len(income_categories)}")
    for cat in income_categories:
        print(f"  - {cat.name}")
    
    # Тестуємо enum values
    print(f"\n🔄 TransactionType.EXPENSE.value = '{TransactionType.EXPENSE.value}'")
    print(f"🔄 TransactionType.INCOME.value = '{TransactionType.INCOME.value}'")
    
    print("\n=== Тест завершено ===")

if __name__ == "__main__":
    test_category_edit_issue()
