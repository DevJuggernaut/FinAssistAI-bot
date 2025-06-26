#!/usr/bin/env python3
"""
Відлагодження типів транзакцій після імпорту
"""

import logging
from database.session import init_db
from database.db_operations import get_transactions
from database.models import User, Transaction, TransactionType

# Налаштовуємо логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_transaction_types():
    """Перевіряємо типи транзакцій в базі даних"""
    
    init_db()
    
    # Знаходимо користувача з ID 1 (тестового)
    from database.db_operations import Session
    session = Session()
    
    try:
        user = session.query(User).filter_by(id=1).first()
        if not user:
            print("❌ Користувач з ID 1 не знайдений")
            return
            
        print(f"✅ Користувач знайдений: {user.telegram_id}")
        
        # Отримуємо всі транзакції користувача
        transactions = session.query(Transaction).filter_by(user_id=user.id).order_by(Transaction.created_at.desc()).limit(10).all()
        
        print(f"\n📊 Останні 10 транзакцій користувача:")
        print("-" * 80)
        
        for i, trans in enumerate(transactions, 1):
            print(f"{i}. ID: {trans.id}")
            print(f"   Сума: {trans.amount}")
            print(f"   Тип: {trans.type} ({trans.type.value})")
            print(f"   Опис: {trans.description}")
            print(f"   Джерело: {trans.source}")
            print(f"   Дата: {trans.transaction_date}")
            
            # Перевіряємо як це має відображатися в інтерфейсі
            if trans.type.value == 'income':
                display_type = "🟢 Дохід"
                amount_str = f"+{trans.amount:,.0f}"
            else:
                display_type = "🔴 Витрата"  
                amount_str = f"{trans.amount:,.0f}"
                
            print(f"   Відображення: {display_type} {amount_str}")
            print("-" * 40)
            
        # Підрахунок за типами
        income_count = session.query(Transaction).filter_by(user_id=user.id, type=TransactionType.INCOME).count()
        expense_count = session.query(Transaction).filter_by(user_id=user.id, type=TransactionType.EXPENSE).count()
        
        print(f"\n📈 Статистика за типами:")
        print(f"   Доходи: {income_count}")
        print(f"   Витрати: {expense_count}")
        print(f"   Всього: {income_count + expense_count}")
        
    except Exception as e:
        logger.error(f"Помилка: {e}")
        
    finally:
        session.close()

if __name__ == "__main__":
    check_transaction_types()
