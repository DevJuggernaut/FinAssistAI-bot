#!/usr/bin/env python3
"""
Швидкий тест для перевірки реальних транзакцій з бази
"""

import sys
import os
import logging
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Налаштовуємо детальне логування
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

from database.db_operations import get_user_transactions, get_user

def inspect_real_transactions():
    """Інспектує реальні транзакції з бази даних"""
    print("🔍 Інспекція реальних транзакцій...")
    
    # ID користувача з логів
    user_id = 580683833
    
    try:
        user = get_user(user_id)
        if not user:
            print(f"❌ Користувач {user_id} не знайдений")
            return
        
        print(f"✅ Користувач знайдений: {user}")
        print(f"User ID в БД: {user.id}")
        
        # Отримуємо транзакції
        now = datetime.now()
        start_date = now - timedelta(days=30)
        transactions = get_user_transactions(user.id, limit=1000, start_date=start_date, end_date=now)
        
        print(f"📊 Знайдено {len(transactions)} транзакцій")
        
        # Інспектуємо перші 3 транзакції детально
        for i, t in enumerate(transactions[:3]):
            print(f"\n=== Транзакція {i+1} ===")
            print(f"Type: {type(t)}")
            print(f"Object: {t}")
            
            # Перевіряємо всі атрибути
            for attr in dir(t):
                if not attr.startswith('_'):
                    try:
                        value = getattr(t, attr)
                        print(f"  {attr}: {value} (type: {type(value)})")
                    except Exception as e:
                        print(f"  {attr}: ERROR - {e}")
                        
            # Особлива увага до amount
            if hasattr(t, 'amount'):
                amount = t.amount
                print(f"\n🔍 AMOUNT DETAILED:")
                print(f"  Raw value: {amount}")
                print(f"  Type: {type(amount)}")
                print(f"  Dir: {dir(amount) if hasattr(amount, '__dict__') else 'No __dict__'}")
                
                # Спроба конвертації
                try:
                    converted = float(amount)
                    print(f"  ✅ Float conversion successful: {converted}")
                except Exception as e:
                    print(f"  ❌ Float conversion failed: {e}")
                    print(f"  Exception type: {type(e)}")
                    
    except Exception as e:
        print(f"❌ Помилка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_real_transactions()
