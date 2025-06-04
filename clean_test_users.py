#!/usr/bin/env python3
"""
Скрипт для видалення тестових користувачів, залишаючи тільки ваш акаунт
"""

from sqlalchemy.orm import sessionmaker
from database.config import DATABASE_URL
from database.models import (
    User, Category, Transaction, BudgetPlan, 
    CategoryBudget, FinancialAdvice
)
from sqlalchemy import create_engine

# Ваш Telegram ID - НЕ ВИДАЛЯТИ
YOUR_TELEGRAM_ID = 580683833

# Тестові Telegram ID для видалення
TEST_TELEGRAM_IDS = [123456789, 987654321, 555666777]

def create_session():
    """Створює сесію для бази даних"""
    engine_test = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine_test)
    return Session()

def clean_test_users():
    """Видаляє тестових користувачів, залишаючи ваш акаунт"""
    session = create_session()
    
    try:
        print("🧹 Видалення тестових користувачів...")
        print(f"Ваш акаунт (ID: {YOUR_TELEGRAM_ID}) буде збережено.")
        
        # Знаходимо тестових користувачів
        test_users = session.query(User).filter(User.telegram_id.in_(TEST_TELEGRAM_IDS)).all()
        
        if not test_users:
            print("ℹ️  Тестові користувачі не знайдені.")
            return
        
        user_ids = [user.id for user in test_users]
        
        # Видаляємо пов'язані дані
        # 1. CategoryBudget
        category_budgets = session.query(CategoryBudget).join(BudgetPlan).filter(BudgetPlan.user_id.in_(user_ids)).all()
        for cb in category_budgets:
            session.delete(cb)
        print(f"Видалено {len(category_budgets)} записів CategoryBudget")
        
        # 2. BudgetPlan
        budget_plans = session.query(BudgetPlan).filter(BudgetPlan.user_id.in_(user_ids)).all()
        for bp in budget_plans:
            session.delete(bp)
        print(f"Видалено {len(budget_plans)} бюджетних планів")
        
        # 3. FinancialAdvice
        advices = session.query(FinancialAdvice).filter(FinancialAdvice.user_id.in_(user_ids)).all()
        for advice in advices:
            session.delete(advice)
        print(f"Видалено {len(advices)} фінансових порад")
        
        # 4. Transaction
        transactions = session.query(Transaction).filter(Transaction.user_id.in_(user_ids)).all()
        for transaction in transactions:
            session.delete(transaction)
        print(f"Видалено {len(transactions)} транзакцій")
        
        # 5. Category
        categories = session.query(Category).filter(Category.user_id.in_(user_ids)).all()
        for category in categories:
            session.delete(category)
        print(f"Видалено {len(categories)} категорій")
        
        # 6. User
        for user in test_users:
            print(f"Видалення користувача: {user.first_name} {user.last_name} (ID: {user.telegram_id})")
            session.delete(user)
        
        # Підтверджуємо зміни
        session.commit()
        print(f"\n✅ Успішно видалено {len(test_users)} тестових користувачів")
        
        # Перевіряємо, що ваш акаунт збережено
        your_user = session.query(User).filter_by(telegram_id=YOUR_TELEGRAM_ID).first()
        if your_user:
            your_transactions = session.query(Transaction).filter_by(user_id=your_user.id).count()
            your_categories = session.query(Category).filter_by(user_id=your_user.id).count()
            print(f"\n👤 Ваш акаунт збережено:")
            print(f"   {your_user.first_name} (@{your_user.username})")
            print(f"   Транзакції: {your_transactions}")
            print(f"   Категорії: {your_categories}")
        else:
            print("\n⚠️ Ваш акаунт не знайдено в базі даних")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Помилка при видаленні тестових даних: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def main():
    """Основна функція"""
    print("🧹 Очищення від тестових користувачів...")
    print("="*50)
    
    answer = input("Ви впевнені, що хочете видалити тестових користувачів? (y/N): ")
    if answer.lower() not in ['y', 'yes', 'так', 'т']:
        print("Операцію скасовано.")
        return
    
    clean_test_users()

if __name__ == "__main__":
    main()
