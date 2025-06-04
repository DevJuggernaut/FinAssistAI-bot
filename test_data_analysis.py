#!/usr/bin/env python3
"""
Швидкий тест функціональності бота з тестовими даними
"""

from sqlalchemy.orm import sessionmaker
from database.config import DATABASE_URL
from database.models import User, Transaction, Category, BudgetPlan, TransactionType
from sqlalchemy import create_engine, func
from datetime import datetime, timedelta
import sys

def create_session():
    """Створює сесію для бази даних"""
    engine_test = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine_test)
    return Session()

def test_user_data(telegram_id):
    """Тестує дані для конкретного користувача"""
    session = create_session()
    
    try:
        # Знаходимо користувача
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            print(f"❌ Користувач з ID {telegram_id} не знайдений")
            return
        
        print(f"👤 Тестування даних для користувача: {user.first_name} {user.last_name}")
        print(f"   Telegram ID: {user.telegram_id}")
        print(f"   Username: @{user.username}")
        print(f"   Баланс: {user.initial_balance} {user.currency}")
        print(f"   Місячний бюджет: {user.monthly_budget} {user.currency}")
        print(f"   Налаштування завершено: {'✅' if user.is_setup_completed else '❌'}")
        
        # Статистика по транзакціях
        print("\n💰 ТРАНЗАКЦІЇ:")
        
        # Загальна статистика
        total_transactions = session.query(Transaction).filter_by(user_id=user.id).count()
        total_income = session.query(func.sum(Transaction.amount)).filter_by(
            user_id=user.id, type=TransactionType.INCOME
        ).scalar() or 0
        total_expenses = session.query(func.sum(Transaction.amount)).filter_by(
            user_id=user.id, type=TransactionType.EXPENSE
        ).scalar() or 0
        
        print(f"   Всього транзакцій: {total_transactions}")
        print(f"   Загальний дохід: {total_income:.2f} {user.currency}")
        print(f"   Загальні витрати: {total_expenses:.2f} {user.currency}")
        print(f"   Різниця: {total_income - total_expenses:.2f} {user.currency}")
        
        # Останні 5 транзакцій
        recent_transactions = session.query(Transaction).filter_by(user_id=user.id)\
            .order_by(Transaction.transaction_date.desc()).limit(5).all()
        
        print(f"\n   📝 Останні 5 транзакцій:")
        for t in recent_transactions:
            type_icon = "📈" if t.type == TransactionType.INCOME else "📉"
            category_name = t.category.name if t.category else "Без категорії"
            print(f"      {type_icon} {t.amount:.2f} {user.currency} - {category_name}")
            print(f"         {t.description} ({t.transaction_date.strftime('%d.%m.%Y')})")
        
        # Статистика по категоріях
        print("\n📂 КАТЕГОРІЇ:")
        
        # Топ категорії витрат
        top_expense_categories = session.query(
            Category.name,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).join(Transaction)\
        .filter(Transaction.user_id == user.id, Transaction.type == TransactionType.EXPENSE)\
        .group_by(Category.name)\
        .order_by(func.sum(Transaction.amount).desc())\
        .limit(5).all()
        
        print("   💸 Топ-5 категорій витрат:")
        for cat_name, total, count in top_expense_categories:
            print(f"      {cat_name}: {total:.2f} {user.currency} ({count} транзакцій)")
        
        # Топ категорії доходів
        top_income_categories = session.query(
            Category.name,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).join(Transaction)\
        .filter(Transaction.user_id == user.id, Transaction.type == TransactionType.INCOME)\
        .group_by(Category.name)\
        .order_by(func.sum(Transaction.amount).desc())\
        .limit(3).all()
        
        print("   💰 Топ-3 категорії доходів:")
        for cat_name, total, count in top_income_categories:
            print(f"      {cat_name}: {total:.2f} {user.currency} ({count} транзакцій)")
        
        # Статистика за поточний місяць
        print("\n📊 ПОТОЧНИЙ МІСЯЦЬ:")
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        month_income = session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.INCOME,
            Transaction.transaction_date >= current_month_start
        ).scalar() or 0
        
        month_expenses = session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= current_month_start
        ).scalar() or 0
        
        print(f"   Дохід за місяць: {month_income:.2f} {user.currency}")
        print(f"   Витрати за місяць: {month_expenses:.2f} {user.currency}")
        if user.monthly_budget:
            remaining_budget = user.monthly_budget - month_expenses
            budget_usage = (month_expenses / user.monthly_budget) * 100
            print(f"   Залишок бюджету: {remaining_budget:.2f} {user.currency}")
            print(f"   Використано бюджету: {budget_usage:.1f}%")
        
        # Бюджетні плани
        budget_plans = session.query(BudgetPlan).filter_by(user_id=user.id).count()
        print(f"\n📋 БЮДЖЕТНІ ПЛАНИ: {budget_plans}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"❌ Помилка при аналізі даних: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def list_all_test_users():
    """Виводить список всіх тестових користувачів"""
    session = create_session()
    
    try:
        test_ids = [123456789, 987654321, 555666777]
        users = session.query(User).filter(User.telegram_id.in_(test_ids)).all()
        
        if not users:
            print("❌ Тестові користувачі не знайдені. Запустіть generate_test_data.py")
            return
        
        print("🧪 ТЕСТОВІ КОРИСТУВАЧІ:")
        print("="*60)
        for user in users:
            transaction_count = session.query(Transaction).filter_by(user_id=user.id).count()
            print(f"ID: {user.telegram_id} | @{user.username} | {user.first_name} {user.last_name}")
            print(f"Баланс: {user.initial_balance} UAH | Транзакції: {transaction_count}")
            print("-" * 60)
            
    except Exception as e:
        print(f"❌ Помилка: {e}")
    finally:
        session.close()

def main():
    """Основна функція"""
    print("🔍 Тестування даних FinAssistAI бота\n")
    
    if len(sys.argv) > 1:
        try:
            telegram_id = int(sys.argv[1])
            test_user_data(telegram_id)
        except ValueError:
            print("❌ Невірний формат Telegram ID")
    else:
        print("Використання:")
        print("  python test_data_analysis.py [TELEGRAM_ID]")
        print("\nАбо запустіть без параметрів для перегляду всіх тестових користувачів:")
        print()
        list_all_test_users()
        print("\nПриклад детального аналізу:")
        print("  python test_data_analysis.py 123456789")

if __name__ == "__main__":
    main()
