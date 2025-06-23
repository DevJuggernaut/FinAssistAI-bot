#!/usr/bin/env python3
"""
Тест нового функціоналу рахунків після міграції.
Перевіряє чи працює створення головного рахунку при налаштуванні.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_operations import *
from database.models import AccountType

def test_accounts_functionality():
    """Тестує основний функціонал рахунків"""
    
    print("🧪 ТЕСТУВАННЯ ФУНКЦІОНАЛУ РАХУНКІВ")
    print("=" * 50)
    
    # Тест користувача (припустимо, користувач з ID 580683833 вже існує)
    test_user_telegram_id = 580683833
    user = get_user(test_user_telegram_id)
    
    if not user:
        print("❌ Тестовий користувач не знайдений")
        return False
    
    print(f"✅ Користувач знайдений: {user.first_name} (ID: {user.id})")
    
    # 1. Тест отримання рахунків
    print("\n📋 Тест 1: Отримання рахунків користувача")
    accounts = get_user_accounts(user.id)
    print(f"   Знайдено рахунків: {len(accounts)}")
    
    for account in accounts:
        print(f"   • {account.name} ({account.account_type.value}): {account.balance} {account.currency}")
        if account.is_main:
            print("     ⭐ Головний рахунок")
    
    # 2. Тест загального балансу
    print("\n💰 Тест 2: Загальний баланс")
    total = get_total_balance(user.id)
    print(f"   Загальний баланс: {total}")
    
    # 3. Тест головного рахунку
    print("\n🏦 Тест 3: Головний рахунок")
    main_account = get_main_account(user.id)
    if main_account:
        print(f"   Головний рахунок: {main_account.name}")
        print(f"   Баланс: {main_account.balance} {main_account.currency}")
        print(f"   Тип: {main_account.account_type.value}")
    else:
        print("   ❌ Головний рахунок не знайдений")
    
    # 4. Тест створення нового рахунку
    print("\n➕ Тест 4: Створення нового рахунку")
    try:
        new_account = create_account(
            user_id=user.id,
            name="Тестовий рахунок",
            account_type=AccountType.BANK_CARD,
            balance=1000.0,
            currency="UAH",
            is_main=False,
            description="Тестовий рахунок для перевірки"
        )
        print(f"   ✅ Створено рахунок: {new_account.name} (ID: {new_account.id})")
    except Exception as e:
        print(f"   ❌ Помилка створення: {str(e)}")
    
    # 5. Тест кількості рахунків
    print("\n📊 Тест 5: Кількість рахунків")
    count = get_accounts_count(user.id)
    print(f"   Активних рахунків: {count}")
    
    # 6. Тест статистики рахунків
    print("\n📈 Тест 6: Статистика рахунків")
    try:
        stats = get_accounts_statistics(user.id)
        print(f"   Всього рахунків: {stats['total_accounts']}")
        print(f"   Загальний баланс: {stats['total_balance']}")
        print(f"   Місячних транзакцій: {stats['monthly_transactions']}")
        print(f"   Місячне зростання: {stats['monthly_growth']}")
        
        print("   По типах:")
        for type_name, data in stats['by_type'].items():
            print(f"     • {type_name}: {data['count']} шт., {data['balance']} грн")
    except Exception as e:
        print(f"   ❌ Помилка статистики: {str(e)}")
    
    print("\n🎉 Тестування завершено!")
    return True

def test_setup_process_simulation():
    """Симулює процес створення головного рахунку при налаштуванні"""
    
    print("\n🚀 СИМУЛЯЦІЯ ПРОЦЕСУ НАЛАШТУВАННЯ")
    print("=" * 50)
    
    # Симулюємо створення головного рахунку
    fake_user_id = 999999  # Не існує в БД
    balance = 5000.0
    currency = "UAH"
    
    print(f"Створюємо головний рахунок для користувача {fake_user_id}")
    print(f"Початковий баланс: {balance} {currency}")
    
    try:
        account = create_account(
            user_id=fake_user_id,
            name="Головний рахунок",
            account_type=AccountType.CASH,
            balance=balance,
            currency=currency,
            is_main=True,
            icon='💰',
            description="Автоматично створений головний рахунок"
        )
        print(f"✅ Рахунок створено: {account.name} (ID: {account.id})")
        return True
    except Exception as e:
        print(f"❌ Помилка: {str(e)}")
        return False

if __name__ == "__main__":
    success1 = test_accounts_functionality()
    success2 = test_setup_process_simulation()
    
    if success1 and success2:
        print("\n🎉 Всі тести пройшли успішно!")
    else:
        print("\n⚠️ Деякі тести не пройшли.")
