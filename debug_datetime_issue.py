#!/usr/bin/env python3
"""
Тест для діагностики точної причини datetime помилки
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Налаштовуємо детальне логування
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_transaction_processing():
    """Тестує обробку транзакцій step-by-step"""
    print("🔍 Діагностика обробки транзакцій...")
    
    # Імітуємо різні типи транзакцій, які можуть бути в базі
    test_cases = [
        # Нормальна транзакція
        {'amount': 100.0, 'type': 'expense', 'date': '2025-06-20', 'category': 'Їжа'},
        
        # Транзакція з datetime об'єктом
        {'amount': datetime.now(), 'type': 'expense', 'date': '2025-06-20', 'category': 'Їжа'},
        
        # Транзакція з Decimal
        {'amount': '150.50', 'type': 'income', 'date': datetime.now(), 'category': 'Зарплата'},
        
        # Транзакція з None
        {'amount': None, 'type': 'expense', 'date': None, 'category': None},
    ]
    
    print(f"Тестуємо {len(test_cases)} різних типів транзакцій...")
    
    for i, test_transaction in enumerate(test_cases):
        print(f"\n--- Тест {i+1} ---")
        print(f"Input: {test_transaction}")
        
        try:
            # Імітуємо обробку як в нашому коді
            amount = test_transaction.get('amount', 0)
            print(f"Amount: {amount} (type: {type(amount)})")
            
            # Спроба конвертації
            if isinstance(amount, (int, float)):
                converted_amount = float(amount)
                print(f"✅ Converted amount: {converted_amount}")
            elif hasattr(amount, '__float__'):
                converted_amount = float(amount)
                print(f"✅ Converted amount via __float__: {converted_amount}")
            elif amount is None:
                converted_amount = 0.0
                print(f"✅ None converted to: {converted_amount}")
            else:
                print(f"❌ Cannot convert {type(amount)} to float")
                converted_amount = 0.0
                
        except Exception as e:
            print(f"❌ Error: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_transaction_processing()
