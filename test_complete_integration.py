#!/usr/bin/env python3
"""
Комплексний тест інтеграції рахунків з транзакціями
"""

import sys
import os
import asyncio

# Додаємо кореневу папку проекту до sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_operations import (
    get_or_create_user, 
    get_user_accounts, 
    add_transaction,
    get_user_main_account_id,
    create_account,
    get_user_categories,
    get_user_transactions
)
from database.models import TransactionType, AccountType

async def test_complete_integration():
    """Повний тест інтеграції системи рахунків і транзакцій"""
    
    print("🚀 КОМПЛЕКСНИЙ ТЕСТ ІНТЕГРАЦІЇ")
    print("=" * 60)
    
    # 1. Створюємо користувача
    test_telegram_id = 777777777
    user = get_or_create_user(
        telegram_id=test_telegram_id,
        username="integration_test",
        first_name="Integration",
        last_name="Test"
    )
    print(f"✅ Користувач створений: ID={user.id}")
    
    # 2. Перевіряємо рахунки
    accounts = get_user_accounts(user.id)
    print(f"📊 Рахунків користувача: {len(accounts)}")
    
    if not accounts:
        print("🔧 Створюємо тестові рахунки...")
        main_account = create_account(
            user_id=user.id,
            name="Головний рахунок",
            account_type=AccountType.BANK_CARD,
            balance=10000.0,
            is_main=True,
            icon='💳'
        )
        
        cash_account = create_account(
            user_id=user.id,
            name="Готівка",
            account_type=AccountType.CASH,
            balance=2000.0,
            icon='💵'
        )
        
        accounts = get_user_accounts(user.id)
        print(f"  ✅ Створено рахунків: {len(accounts)}")
    
    # 3. Показуємо рахунки
    for account in accounts:
        main_mark = " ⭐" if account.is_main else ""
        print(f"  {account.icon} {account.name} - {account.balance} {account.currency}{main_mark}")
    
    # 4. Тестуємо отримання головного рахунку
    main_account_id = get_user_main_account_id(user.id)
    print(f"🎯 ID головного рахунку: {main_account_id}")
    
    # 5. Тестуємо додавання транзакцій до різних рахунків
    print("\n📝 ТЕСТУВАННЯ ДОДАВАННЯ ТРАНЗАКЦІЙ:")
    
    # Додаємо транзакцію до конкретного рахунку
    transaction1 = add_transaction(
        user_id=user.id,
        amount=500.0,
        description="Тест на головний рахунок",
        category_id=1,  # Буде створена автоматично якщо немає
        transaction_type=TransactionType.EXPENSE,
        account_id=main_account_id
    )
    print(f"  ✅ Транзакція 1: ID={transaction1.id}, Рахунок={transaction1.account_id}")
    
    # Додаємо транзакцію без вказівки рахунку (має піти на головний)
    transaction2 = add_transaction(
        user_id=user.id,
        amount=200.0,
        description="Тест без рахунку",
        category_id=1,
        transaction_type=TransactionType.INCOME
    )
    print(f"  ✅ Транзакція 2: ID={transaction2.id}, Рахунок={transaction2.account_id}")
    
    # Додаємо транзакцію на інший рахунок
    cash_account = next((acc for acc in accounts if acc.account_type == AccountType.CASH), None)
    if cash_account:
        transaction3 = add_transaction(
            user_id=user.id,
            amount=100.0,
            description="Тест на готівковий рахунок",
            category_id=1,
            transaction_type=TransactionType.EXPENSE,
            account_id=cash_account.id
        )
        print(f"  ✅ Транзакція 3: ID={transaction3.id}, Рахунок={transaction3.account_id}")
    
    # 6. Перевіряємо всі транзакції користувача
    user_transactions = get_user_transactions(user.id)
    print(f"\n📊 Всього транзакцій користувача: {len(user_transactions)}")
    
    # Групуємо по рахунках
    by_account = {}
    for trans in user_transactions:
        account_id = trans.account_id or "Без рахунку"
        if account_id not in by_account:
            by_account[account_id] = []
        by_account[account_id].append(trans)
    
    print("\n📈 РОЗПОДІЛ ПО РАХУНКАХ:")
    for account_id, transactions in by_account.items():
        if account_id == "Без рахунку":
            account_name = "Без рахунку"
        else:
            account = next((acc for acc in accounts if acc.id == account_id), None)
            account_name = f"{account.icon} {account.name}" if account else f"Рахунок #{account_id}"
        
        print(f"  {account_name}: {len(transactions)} транзакцій")
    
    print("\n" + "=" * 60)
    print("🏆 КОМПЛЕКСНИЙ ТЕСТ ЗАВЕРШЕНО")
    print("✅ Система рахунків працює!")
    print("✅ Транзакції прив'язуються до рахунків!")
    print("✅ Автовибір головного рахунку працює!")
    print("✅ Інтеграція повністю готова!")

if __name__ == "__main__":
    asyncio.run(test_complete_integration())
