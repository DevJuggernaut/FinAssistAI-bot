#!/usr/bin/env python3
"""
Тестування потоку переказу між рахунками
"""
import asyncio
import sys
import os

# Додаємо кореневу папку проекту до sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_operations import (
    get_or_create_user, create_account, get_user_accounts, 
    get_total_balance, transfer_between_accounts
)
from database.models import AccountType

def test_transfer_setup():
    """Тестуємо налаштування тестових рахунків для переказу"""
    print("🔧 Налаштування тестових рахунків...")
    
    # Створюємо тестового користувача
    test_user_id = 999999  # Тестовий ID
    user = get_or_create_user(test_user_id)
    print(f"✅ Користувач створений: {user.id}")
    
    # Створюємо два тестових рахунки
    account1 = create_account(
        user_id=user.id,
        name="Тестовий Картковий",
        account_type=AccountType.BANK_CARD,
        balance=5000.0,
        icon="💳"
    )
    print(f"✅ Рахунок 1 створений: {account1.name} - {account1.balance} UAH")
    
    account2 = create_account(
        user_id=user.id,
        name="Тестовий Готівка",
        account_type=AccountType.CASH,
        balance=1000.0,
        icon="💵"
    )
    print(f"✅ Рахунок 2 створений: {account2.name} - {account2.balance} UAH")
    
    # Показуємо поточний стан
    accounts = get_user_accounts(user.id)
    total_balance = get_total_balance(user.id)
    
    print(f"\n📊 Поточний стан рахунків:")
    for acc in accounts:
        print(f"   {acc.icon} {acc.name}: {acc.balance:,.2f} UAH")
    print(f"💰 Загальний баланс: {total_balance:,.2f} UAH")
    
    return user, account1, account2

def test_transfer_logic():
    """Тестуємо логіку переказу"""
    print("\n💸 Тестування логіки переказу...")
    
    user, account1, account2 = test_transfer_setup()
    
    # Тестуємо переказ
    transfer_amount = 500.0
    print(f"\n🔄 Переказ {transfer_amount} UAH з '{account1.name}' на '{account2.name}'")
    
    # Показуємо баланси до переказу
    print(f"До переказу:")
    print(f"   {account1.icon} {account1.name}: {account1.balance:,.2f} UAH")
    print(f"   {account2.icon} {account2.name}: {account2.balance:,.2f} UAH")
    
    # Виконуємо переказ
    success, message = transfer_between_accounts(
        from_account_id=account1.id,
        to_account_id=account2.id,
        amount=transfer_amount,
        description=f"Тестовий переказ {transfer_amount} UAH"
    )
    
    if success:
        print("✅ Переказ виконано успішно!")
        print(f"   Повідомлення: {message}")
        
        # Оновлюємо дані рахунків
        updated_accounts = get_user_accounts(user.id)
        updated_account1 = next((acc for acc in updated_accounts if acc.id == account1.id), None)
        updated_account2 = next((acc for acc in updated_accounts if acc.id == account2.id), None)
        
        print(f"Після переказу:")
        print(f"   {updated_account1.icon} {updated_account1.name}: {updated_account1.balance:,.2f} UAH")
        print(f"   {updated_account2.icon} {updated_account2.name}: {updated_account2.balance:,.2f} UAH")
        
        # Перевіряємо правильність переказу
        expected_account1_balance = account1.balance - transfer_amount
        expected_account2_balance = account2.balance + transfer_amount
        
        if (abs(updated_account1.balance - expected_account1_balance) < 0.01 and
            abs(updated_account2.balance - expected_account2_balance) < 0.01):
            print("✅ Суми переказу правильні!")
        else:
            print("❌ Помилка в сумах переказу!")
            
        # Перевіряємо загальний баланс
        new_total_balance = get_total_balance(user.id)
        original_total = account1.balance + account2.balance
        if abs(new_total_balance - original_total) < 0.01:
            print("✅ Загальний баланс збережено!")
        else:
            print("❌ Загальний баланс змінився!")
            
    else:
        print(f"❌ Переказ не вдався: {message}")

def test_transfer_validation():
    """Тестуємо валідацію переказу"""
    print("\n🛡️ Тестування валідації переказу...")
    
    user, account1, account2 = test_transfer_setup()
    
    # Тест 1: Переказ більшої суми ніж доступно
    large_amount = account1.balance + 1000
    print(f"\n❌ Тест: переказ {large_amount} UAH (більше ніж доступно)")
    success, message = transfer_between_accounts(
        from_account_id=account1.id,
        to_account_id=account2.id,
        amount=large_amount,
        description="Тест недостатніх коштів"
    )
    
    if not success:
        print(f"✅ Правильно відхилено переказ через недостатність коштів: {message}")
    else:
        print("❌ Переказ виконано незважаючи на недостатність коштів!")
    
    # Тест 2: Переказ нульової суми
    print(f"\n❌ Тест: переказ 0 UAH")
    success, message = transfer_between_accounts(
        from_account_id=account1.id,
        to_account_id=account2.id,
        amount=0,
        description="Тест нульової суми"
    )
    
    if not success:
        print(f"✅ Правильно відхилено переказ нульової суми: {message}")
    else:
        print("❌ Переказ нульової суми виконано!")
    
    # Тест 3: Переказ від'ємної суми
    print(f"\n❌ Тест: переказ -100 UAH")
    success, message = transfer_between_accounts(
        from_account_id=account1.id,
        to_account_id=account2.id,
        amount=-100,
        description="Тест від'ємної суми"
    )
    
    if not success:
        print(f"✅ Правильно відхилено переказ від'ємної суми: {message}")
    else:
        print("❌ Переказ від'ємної суми виконано!")

def main():
    """Головна функція тестування"""
    print("🧪 Тестування функціональності переказу між рахунками")
    print("=" * 60)
    
    try:
        # Основний тест переказу
        test_transfer_logic()
        
        # Тест валідації
        test_transfer_validation()
        
        print(f"\n✅ Всі тести завершено!")
        print(f"\n💡 Важливо: У новій версії боту швидкі кнопки з сумами видалено,")
        print(f"   тепер користувачі можуть вводити тільки суми вручну.")
        
    except Exception as e:
        print(f"❌ Помилка під час тестування: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
