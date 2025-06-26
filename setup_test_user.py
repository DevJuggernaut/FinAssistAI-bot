#!/usr/bin/env python3
"""
Налаштування тестового користувача з рахунками та категоріями
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.session import init_db, Session
from database.models import User, Category, Account, TransactionType
from database.db_operations import get_or_create_user
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_test_user():
    """Налаштовуємо тестового користувача з базовими рахунками та категоріями"""
    try:
        init_db()
        session = Session()
        
        # Створюємо тестового користувача
        test_user_id = 123456789
        user = get_or_create_user(test_user_id)
        print(f"✅ User: {user.id}, telegram_id: {user.telegram_id}")
        
        # Перевіряємо, чи вже є рахунки
        existing_accounts = session.query(Account).filter_by(user_id=user.id).all()
        if not existing_accounts:
            # Створюємо базовий рахунок
            from database.models import AccountType
            account = Account(
                user_id=user.id,
                name="Основна картка",
                account_type=AccountType.BANK_CARD,
                balance=0.0,
                currency="UAH",
                is_main=True
            )
            session.add(account)
            print("✅ Створено основний рахунок")
        else:
            print(f"✅ Знайдено {len(existing_accounts)} рахунків")
        
        # Перевіряємо, чи вже є категорії
        existing_categories = session.query(Category).filter_by(user_id=user.id).all()
        if not existing_categories:
            # Створюємо базові категорії витрат
            expense_categories = [
                ("Продукти", "🛒", "expense"),
                ("Транспорт", "🚗", "expense"),
                ("Розваги", "🎬", "expense"),
                ("Комунальні", "💡", "expense"),
                ("Інше витрати", "💸", "expense"),
            ]
            
            # Створюємо базові категорії доходів
            income_categories = [
                ("Зарплата", "💰", "income"),
                ("Підробіток", "💵", "income"),
                ("Інше доходи", "💸", "income"),
            ]
            
            all_categories = expense_categories + income_categories
            
            for name, icon, cat_type in all_categories:
                category = Category(
                    user_id=user.id,
                    name=name,
                    icon=icon,
                    type=cat_type
                )
                session.add(category)
            
            print(f"✅ Створено {len(all_categories)} категорій")
        else:
            print(f"✅ Знайдено {len(existing_categories)} категорій")
        
        session.commit()
        session.close()
        print("✅ Налаштування користувача завершено")
        
    except Exception as e:
        print(f"❌ Помилка налаштування: {e}")
        logger.exception("Setup error")

if __name__ == "__main__":
    setup_test_user()
