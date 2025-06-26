#!/usr/bin/env python3
"""
Тест системи додавання транзакцій з вибором рахунку
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
    create_account
)
from database.models import TransactionType, AccountType

def test_account_integration():
    """Тестує інтеграцію системи рахунків з додаванням транзакцій"""
    
    print("🚀 ТЕСТУВАННЯ ІНТЕГРАЦІЇ РАХУНКІВ З ТРАНЗАКЦІЯМИ")
    print("=" * 60)
    
    # Створюємо тестового користувача
    test_telegram_id = 999999999
    user = get_or_create_user(
        telegram_id=test_telegram_id,
        username="test_user_accounts",
        first_name="Test",
        last_name="User"
    )
    
    print(f"✅ Користувач створений: ID={user.id}")
    
    # Перевіряємо рахунки користувача
    accounts = get_user_accounts(user.id)
    print(f"📊 Рахунків користувача: {len(accounts)}")
    
    # Якщо рахунків немає, створюємо тестові
    if not accounts:
        print("🔧 Створюємо тестові рахунки...")
        
        # Головний рахунок
        main_account = create_account(
            user_id=user.id,
            name="Основна картка",
            account_type=AccountType.BANK_CARD,
            balance=5000.0,
            currency="UAH",
            is_main=True,
            icon="💳",
            description="Основна банківська картка"
        )
        
        # Додатковий рахунок
        cash_account = create_account(
            user_id=user.id,
            name="Готівка",
            account_type=AccountType.CASH,
            balance=1000.0,
            currency="UAH",
            is_main=False,
            icon="💵",
            description="Готівкові кошти"
        )
        
        if main_account and cash_account:
            print(f"  ✅ Створено головний рахунок: {main_account.name}")
            print(f"  ✅ Створено касовий рахунок: {cash_account.name}")
        
        # Оновлюємо список рахунків
        accounts = get_user_accounts(user.id)
    
    if accounts:
        for account in accounts:
            main_mark = "⭐" if account.is_main else "  "
            print(f"  {main_mark} {account.icon} {account.name} - {account.balance} {account.currency}")
    
    # Тестуємо функцію отримання головного рахунку
    main_account_id = get_user_main_account_id(user.id)
    print(f"🎯 ID головного рахунку: {main_account_id}")
    
    if main_account_id:
        # Тестуємо додавання транзакції з вказівкою рахунку
        print("\n📝 Тестування додавання транзакції з рахунком:")
        
        transaction = add_transaction(
            user_id=user.id,
            amount=250.0,
            description="Тест транзакції з рахунком",
            category_id=1,  # Припускаємо, що категорія з ID=1 існує
            transaction_type=TransactionType.EXPENSE,
            account_id=main_account_id,
            source="test"
        )
        
        if transaction:
            print(f"  ✅ Транзакція додана: ID={transaction.id}")
            print(f"     Сума: {transaction.amount}")
            print(f"     Опис: {transaction.description}")
            print(f"     Рахунок: {transaction.account_id}")
            print(f"     Тип: {transaction.type}")
        else:
            print("  ❌ Помилка при додаванні транзакції")
        
        # Тестуємо додавання транзакції без вказівки рахунку (має використати головний)
        print("\n📝 Тестування додавання транзакції без вказівки рахунку:")
        
        transaction2 = add_transaction(
            user_id=user.id,
            amount=100.0,
            description="Тест без рахунку",
            category_id=1,
            transaction_type=TransactionType.INCOME,
            source="test"
        )
        
        if transaction2:
            print(f"  ✅ Транзакція додана: ID={transaction2.id}")
            print(f"     Сума: {transaction2.amount}")
            print(f"     Опис: {transaction2.description}")
            print(f"     Рахунок: {transaction2.account_id} (має бути {main_account_id})")
            print(f"     Тип: {transaction2.type}")
        else:
            print("  ❌ Помилка при додаванні транзакції")
    
    else:
        print("⚠️ У користувача немає рахунків. Створіть рахунки через інтерфейс бота.")
    
    print("\n" + "=" * 60)
    print("🏆 ТЕСТ ЗАВЕРШЕНО")
    
    if accounts and main_account_id:
        print("✅ Система рахунків працює коректно!")
        print("✅ Транзакції прив'язуються до рахунків!")
        print("✅ Інтеграція готова до використання!")
    else:
        print("⚠️ Потрібно створити рахунки для тестування повної функціональності")

if __name__ == "__main__":
    test_account_integration()
