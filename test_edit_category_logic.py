#!/usr/bin/env python3
"""
Тест конкретно для функції handle_edit_category
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_operations import get_user_categories, get_transaction_by_id, get_user
from database.models import TransactionType

def test_edit_category_logic():
    """Тестує логіку функції handle_edit_category"""
    print("=== Тест логіки handle_edit_category ===\n")
    
    # Отримуємо користувача
    user = get_user(580683833)
    if not user:
        print("❌ Користувач не знайдений")
        return
        
    print(f"✅ Користувач: {user.telegram_id}")
    
    # Отримуємо будь-яку транзакцію користувача
    from database.session import Session
    from database.models import Transaction
    session = Session()
    
    transaction = session.query(Transaction).filter(Transaction.user_id == user.id).first()
    if not transaction:
        print("❌ Транзакції не знайдені")
        session.close()
        return
    
    print(f"📝 Тестова транзакція: ID={transaction.id}, Type={transaction.type}, Amount={transaction.amount}")
    
    # Відтворюємо логіку з handle_edit_category
    transaction_type_str = transaction.type.value if hasattr(transaction.type, 'value') else str(transaction.type)
    print(f"🔍 Шукаємо категорії типу: '{transaction_type_str}'")
    
    categories = get_user_categories(user.id, category_type=transaction_type_str)
    print(f"📂 Знайдено категорій: {len(categories)}")
    
    if not categories:
        # Спробуємо отримати всі категорії користувача для діагностики
        all_categories = get_user_categories(user.id)
        print(f"📋 Всього категорій: {len(all_categories)}")
        category_types = [f'{cat.name}({cat.type})' for cat in all_categories]
        print(f"📋 Список: {category_types}")
        
        # Якщо у користувача є категорії, але не цього типу, показуємо всі
        if all_categories:
            categories = all_categories
            print("✅ Буде показано всі категорії")
        else:
            print("❌ Категорій взагалі немає")
    else:
        print("✅ Знайдено відповідні категорії")
        for cat in categories[:5]:  # показуємо перші 5
            print(f"  - {cat.name} ({cat.type})")
    
    session.close()
    print("\n=== Тест завершено ===")

if __name__ == "__main__":
    test_edit_category_logic()
