#!/usr/bin/env python3
"""
Тест нових емодзі кружків для транзакцій
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import TransactionType

def test_transaction_emojis():
    """Тестує нові емодзі для транзакцій"""
    print("=== Тест нових емодзі для транзакцій ===\n")
    
    # Симулюємо логіку з коду
    transactions = [
        {'type': TransactionType.INCOME, 'amount': 5000, 'description': 'Зарплата'},
        {'type': TransactionType.EXPENSE, 'amount': 150, 'description': 'Продукти'},
        {'type': TransactionType.INCOME, 'amount': 2000, 'description': 'Фріланс'},
        {'type': TransactionType.EXPENSE, 'amount': 800, 'description': 'Комунальні'}
    ]
    
    print("Приклад кнопок транзакцій в історії операцій:\n")
    
    for i, trans in enumerate(transactions, 1):
        # Логіка з коду
        if trans['type'].value == 'income':
            amount_str = f"+{trans['amount']:,.0f} ₴"
            type_emoji = "🟢"
        else:
            amount_str = f"{trans['amount']:,.0f} ₴"
            type_emoji = "🔴"
        
        description = trans['description']
        date_str = "25.06"  # приклад дати
        
        button_text = f"{type_emoji} {amount_str} • {description} • {date_str}"
        print(f"{i}. {button_text}")
    
    print(f"\n📊 Легенда:")
    print(f"🟢 - Доходи (зелений кружок)")
    print(f"🔴 - Витрати (червоний кружок)")
    
    print(f"\n=== Тест завершено ===")

if __name__ == "__main__":
    test_transaction_emojis()
