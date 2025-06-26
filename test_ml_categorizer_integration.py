#!/usr/bin/env python3
"""
Тест ML категоризатора з рахунками
"""

import sys
import os

# Додаємо кореневу папку проекту до sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_operations import (
    get_or_create_user, 
    get_user_accounts, 
    add_transaction,
    get_user_main_account_id,
    create_account,
    get_user_categories
)
from database.models import TransactionType, AccountType
from services.ml_categorizer import TransactionCategorizer

def test_ml_categorizer_with_accounts():
    """Тестує ML категоризатор з системою рахунків"""
    
    print("🤖 ТЕСТУВАННЯ ML КАТЕГОРИЗАТОРА З РАХУНКАМИ")
    print("=" * 60)
    
    # Створюємо тестового користувача
    test_telegram_id = 888888888
    user = get_or_create_user(
        telegram_id=test_telegram_id,
        username="test_ml_user",
        first_name="ML",
        last_name="Test"
    )
    
    print(f"✅ Користувач створений: ID={user.id}")
    
    # Створюємо категоризатор
    categorizer = TransactionCategorizer()
    
    # Отримуємо категорії користувача
    categories = get_user_categories(user.id)
    print(f"📂 Доступних категорій: {len(categories)}")
    
    # Тестуємо категоризацію різних описів
    test_descriptions = [
        "Покупка продуктів в АТБ",
        "Зарплата за червень", 
        "Оплата за інтернет",
        "Кафе з друзями",
        "Заправка автомобіля"
    ]
    
    print("\n🔍 ТЕСТУВАННЯ КАТЕГОРИЗАЦІЇ:")
    for desc in test_descriptions:
        predicted_category, confidence = categorizer.predict_category(desc)
        
        print(f"  💬 '{desc}' → 📂 {predicted_category} (впевненість: {confidence:.2f})")
    
    print("\n✅ Тест ML категоризатора завершено!")

if __name__ == "__main__":
    test_ml_categorizer_with_accounts()
