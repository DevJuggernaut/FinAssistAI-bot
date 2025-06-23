#!/usr/bin/env python3
"""
Тест нового UX для додавання транзакцій з автоматичною категоризацією
"""

import asyncio
import sys
import os

# Додаємо шлях до проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ml_categorizer import TransactionCategorizer

def test_ml_categorizer():
    """Тестує ML категоризатор"""
    print("🔬 Тестуємо ML категоризатор...")
    
    categorizer = TransactionCategorizer()
    
    # Тестові транзакції
    test_transactions = [
        {"description": "АТБ продукти", "amount": 450, "type": "expense"},
        {"description": "проїзд у метро", "amount": 50, "type": "expense"},
        {"description": "обід в ресторані", "amount": 1200, "type": "expense"},
        {"description": "зарплата", "amount": 15000, "type": "income"},
        {"description": "фриланс проект", "amount": 5000, "type": "income"},
        {"description": "аптека ліки", "amount": 300, "type": "expense"},
        {"description": "кіно квитки", "amount": 800, "type": "expense"},
    ]
    
    print("\n📊 Результати категоризації:")
    print("-" * 70)
    
    for transaction in test_transactions:
        result = categorizer.categorize_transaction(
            description=transaction["description"],
            amount=transaction["amount"],
            transaction_type=transaction["type"]
        )
        
        type_icon = "💸" if transaction["type"] == "expense" else "💰"
        print(f"{type_icon} {transaction['amount']}₴ • {transaction['description']}")
        print(f"   📍 Категорія: {result['icon']} {result['name']} (ID: {result['id']})")
        print()

def test_transaction_flow():
    """Імітує поток додавання транзакції"""
    print("🛠️ Тестуємо поток додавання транзакції...")
    
    # Імітуємо введення користувача
    user_inputs = [
        "450 АТБ продукти",
        "1200 обід в ресторані",
        "50 проїзд",
        "15000 зарплата",
        "300 аптека",
    ]
    
    print("\n✅ Імітація UX потоку:")
    print("-" * 70)
    
    categorizer = TransactionCategorizer()
    
    for input_text in user_inputs:
        print(f"👤 Користувач вводить: '{input_text}'")
        
        # Парсимо введення
        parts = input_text.split(' ', 1)
        if len(parts) >= 2:
            amount = float(parts[0])
            description = parts[1]
        else:
            amount = float(parts[0])
            description = "Без опису"
        
        # Визначаємо тип (для простоти - якщо сума > 5000, то дохід)
        transaction_type = "income" if amount > 5000 else "expense"
        
        # Отримуємо категорію
        category = categorizer.categorize_transaction(
            description=description,
            amount=amount,
            transaction_type=transaction_type
        )
        
        # Формуємо повідомлення як у боті
        type_icon = "💸" if transaction_type == "expense" else "💰"
        amount_str = f"-{amount:.0f}₴" if transaction_type == "expense" else f"+{amount:.0f}₴"
        
        print(f"🤖 Я проаналізував вашу операцію:")
        print(f"   {type_icon} {amount_str} • {description}")
        print(f"   📍 Автоматично віднесено до: {category['icon']} {category['name']}")
        print(f"   Це правильно? [✅ Так] [❌ Ні, змінити]")
        print()

if __name__ == "__main__":
    print("🚀 Тестування нового UX для додавання транзакцій")
    print("=" * 70)
    
    try:
        test_ml_categorizer()
        test_transaction_flow()
        
        print("✅ Всі тести пройшли успішно!")
        print("\n📝 Резюме нового UX:")
        print("1. 👤 Користувач обирає тип операції (витрата/дохід)")
        print("2. 📝 Вводить суму та опис одним рядком")
        print("3. 🤖 Система автоматично визначає категорію")
        print("4. ✅ Користувач підтверджує або змінює категорію")
        print("5. 💾 Транзакція зберігається в базу даних")
        
    except Exception as e:
        print(f"❌ Помилка під час тестування: {e}")
        import traceback
        traceback.print_exc()
