#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки створення рахунків та прив'язки транзакцій
"""

from sqlalchemy.orm import sessionmaker
from database.config import DATABASE_URL
from database.models import User, Account, Transaction
from sqlalchemy import create_engine

def create_session():
    """Створює сесію для бази даних"""
    engine_test = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine_test)
    return Session()

def test_accounts():
    """Перевіряє, чи створені рахунки та транзакції з прив'язкою"""
    session = create_session()
    
    try:
        # Знаходимо тестового користувача
        user = session.query(User).filter_by(telegram_id=580683833).first()
        if not user:
            print("❌ Тестовий користувач не знайдений")
            return
        
        print(f"👤 Користувач: {user.first_name} {user.last_name}")
        print(f"   Telegram ID: {user.telegram_id}")
        
        # Перевіряємо рахунки
        accounts = session.query(Account).filter_by(user_id=user.id).all()
        print(f"\n💳 Рахунків знайдено: {len(accounts)}")
        
        for account in accounts:
            print(f"   {account.icon} {account.name}")
            print(f"      Тип: {account.account_type.value}")
            print(f"      Баланс: {account.balance:.2f} {account.currency}")
            print(f"      Головний: {'Так' if account.is_main else 'Ні'}")
            print()
        
        # Перевіряємо транзакції з прив'язкою до рахунків
        transactions_with_accounts = session.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.account_id.isnot(None)
        ).count()
        
        total_transactions = session.query(Transaction).filter_by(user_id=user.id).count()
        
        print(f"💰 Транзакцій всього: {total_transactions}")
        print(f"💰 Транзакцій з рахунками: {transactions_with_accounts}")
        print(f"💰 Покриття рахунками: {(transactions_with_accounts/total_transactions*100):.1f}%")
        
        # Показуємо приклади транзакцій
        print(f"\n🔍 Приклади транзакцій з рахунками:")
        sample_transactions = session.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.account_id.isnot(None)
        ).limit(5).all()
        
        for transaction in sample_transactions:
            account = session.query(Account).filter_by(id=transaction.account_id).first()
            print(f"   {transaction.amount:.2f} UAH - {transaction.description}")
            print(f"      Рахунок: {account.icon} {account.name}")
            print(f"      Дата: {transaction.transaction_date.strftime('%d.%m.%Y %H:%M')}")
            print()
            
    except Exception as e:
        print(f"❌ Помилка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_accounts()
