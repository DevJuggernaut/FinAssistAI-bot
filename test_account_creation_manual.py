#!/usr/bin/env python3
"""
Тестування створення рахунку з ручним вводом балансу
"""
import asyncio
import sys
import os

# Додаємо кореневу папку проекту до sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_operations import (
    get_or_create_user, create_account, get_user_accounts, 
    get_total_balance, get_accounts_count
)
from database.models import AccountType

def test_manual_account_creation():
    """Тестуємо створення рахунку з ручним вводом балансу"""
    print("🧪 Тестування створення рахунку з ручним вводом")
    print("=" * 60)
    
    # Створюємо тестового користувача
    test_user_id = 999998  # Інший тестовий ID
    user = get_or_create_user(test_user_id)
    print(f"✅ Користувач створений: {user.id}")
    
    # Показуємо початковий стан
    initial_count = get_accounts_count(user.id)
    initial_balance = get_total_balance(user.id)
    print(f"📊 Початковий стан:")
    print(f"   🏦 Кількість рахунків: {initial_count}")
    print(f"   💰 Загальний баланс: {initial_balance:,.2f} UAH")
    
    # Тестуємо створення рахунків з різними балансами
    test_cases = [
        ("Тестовий Картковий", AccountType.BANK_CARD, 2500.75, "💳"),
        ("Тестова Готівка", AccountType.CASH, 0.0, "💵"),
        ("Тестові Заощадження", AccountType.SAVINGS, 50000.0, "🏦"),
    ]
    
    created_accounts = []
    
    for name, account_type, balance, icon in test_cases:
        print(f"\n🔧 Створення рахунку: {name}")
        print(f"   💰 Баланс: {balance:,.2f} UAH")
        
        try:
            new_account = create_account(
                user_id=user.id,
                name=name,
                account_type=account_type,
                balance=balance,
                icon=icon
            )
            
            if new_account:
                print(f"✅ Рахунок створено: ID={new_account.id}")
                created_accounts.append(new_account)
            else:
                print(f"❌ Помилка створення рахунку")
                
        except Exception as e:
            print(f"❌ Помилка: {str(e)}")
    
    # Перевіряємо результат
    print(f"\n📊 Фінальний стан:")
    final_accounts = get_user_accounts(user.id)
    final_count = len(final_accounts)
    final_balance = get_total_balance(user.id)
    
    print(f"   🏦 Кількість рахунків: {final_count}")
    print(f"   💰 Загальний баланс: {final_balance:,.2f} UAH")
    
    print(f"\n📋 Створені рахунки:")
    for acc in final_accounts:
        if acc.id > initial_count:  # Показуємо тільки нові рахунки
            print(f"   {acc.icon} {acc.name}: {acc.balance:,.2f} UAH")
    
    # Перевіряємо правильність розрахунків
    expected_total = initial_balance + sum(case[2] for case in test_cases)
    if abs(final_balance - expected_total) < 0.01:
        print(f"\n✅ Загальний баланс правильний!")
    else:
        print(f"\n❌ Помилка у загальному балансі!")
        print(f"   Очікувано: {expected_total:,.2f}")
        print(f"   Фактично: {final_balance:,.2f}")
    
    return user, created_accounts

def test_balance_validation():
    """Тестуємо валідацію балансу"""
    print(f"\n🛡️ Тестування валідації балансу")
    print("-" * 40)
    
    test_user_id = 999997
    user = get_or_create_user(test_user_id)
    
    # Тест 1: Від'ємний баланс
    print(f"\n❌ Тест: створення рахунку з від'ємним балансом")
    try:
        negative_account = create_account(
            user_id=user.id,
            name="Тест від'ємного балансу",
            account_type=AccountType.CASH,
            balance=-1000.0,
            icon="💵"
        )
        
        if negative_account and negative_account.balance >= 0:
            print("✅ Від'ємний баланс автоматично виправлено або відхилено")
        elif not negative_account:
            print("✅ Створення рахунку з від'ємним балансом відхилено")
        else:
            print("❌ Від'ємний баланс дозволено!")
            
    except Exception as e:
        print(f"✅ Виняток при від'ємному балансі: {str(e)}")
    
    # Тест 2: Нульовий баланс (дозволено)
    print(f"\n✅ Тест: створення рахунку з нульовим балансом")
    try:
        zero_account = create_account(
            user_id=user.id,
            name="Тест нульового балансу",
            account_type=AccountType.CASH,
            balance=0.0,
            icon="💵"
        )
        
        if zero_account and zero_account.balance == 0.0:
            print("✅ Нульовий баланс дозволено")
        else:
            print("❌ Проблема з нульовим балансом")
            
    except Exception as e:
        print(f"❌ Помилка з нульовим балансом: {str(e)}")
    
    # Тест 3: Великий баланс
    print(f"\n✅ Тест: створення рахунку з великим балансом")
    try:
        large_account = create_account(
            user_id=user.id,
            name="Тест великого балансу",
            account_type=AccountType.SAVINGS,
            balance=1000000.0,
            icon="🏦"
        )
        
        if large_account and large_account.balance == 1000000.0:
            print("✅ Великий баланс дозволено")
        else:
            print("❌ Проблема з великим балансом")
            
    except Exception as e:
        print(f"❌ Помилка з великим балансом: {str(e)}")

def main():
    """Головна функція тестування"""
    print("🧪 Тестування створення рахунків з ручним вводом балансу")
    print("=" * 70)
    
    try:
        # Основний тест створення
        test_manual_account_creation()
        
        # Тест валідації
        test_balance_validation()
        
        print(f"\n✅ Всі тести створення рахунків завершено!")
        print(f"\n💡 Важливо: У новій версії боту швидкі кнопки з балансами видалено,")
        print(f"   тепер користувачі можуть вводити тільки баланс вручну.")
        print(f"\n📋 Нові особливості:")
        print(f"   • Ручний ввід будь-якої суми (включно з 0)")
        print(f"   • Валідація від'ємних сум")
        print(f"   • Підтримка десяткових чисел")
        print(f"   • Кращий контроль користувача")
        
    except Exception as e:
        print(f"❌ Помилка під час тестування: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
