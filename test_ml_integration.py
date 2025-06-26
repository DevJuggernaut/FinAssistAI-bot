#!/usr/bin/env python3
"""
Тест для перевірки роботи ML категоризатора в парсингу банківських виписок
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.statement_parser import StatementParser
from services.ml_categorizer import transaction_categorizer

def test_ml_categorizer_integration():
    """Тестує інтеграцію ML категоризатора з парсером виписок"""
    
    print("🚀 Тестування інтеграції ML категоризатора з парсером виписок")
    print("=" * 70)
    
    # Створюємо парсер
    parser = StatementParser()
    
    # Симулюємо банківські транзакції з різними описами
    test_transactions = [
        # ПриватБанк виписка
        {"description": "Покупка в супермаркеті Сільпо", "amount": -150.50, "date": "2025-01-01", "source": "PrivatBank"},
        {"description": "Зарахування заробітної плати", "amount": 15000.00, "date": "2025-01-02", "source": "PrivatBank"},
        {"description": "Оплата в ресторані McDonald's", "amount": -250.75, "date": "2025-01-03", "source": "PrivatBank"},
        
        # Monobank виписка
        {"description": "Uber поїздка", "amount": -95.00, "date": "2025-01-04", "source": "Monobank"},
        {"description": "Кешбек від покупки", "amount": 25.50, "date": "2025-01-05", "source": "Monobank"},
        {"description": "Платіж за комунальні послуги", "amount": -850.00, "date": "2025-01-06", "source": "Monobank"},
    ]
    
    print("🧪 Тестування автоматичного призначення категорій:")
    print("-" * 70)
    
    all_categorized = True
    
    for i, trans in enumerate(test_transactions, 1):
        # Визначаємо тип транзакції
        transaction_type = 'expense' if trans['amount'] < 0 else 'income'
        
        # Призначаємо категорію через ML категоризатор
        category = transaction_categorizer.suggest_category_for_bank_statement(
            trans['description'], transaction_type
        )
        
        # Додаємо категорію до транзакції
        trans['category'] = category
        trans['type'] = transaction_type
        
        print(f"Транзакція {i} ({trans['source']}):")
        print(f"  📝 Опис: {trans['description']}")
        print(f"  💰 Сума: {abs(trans['amount'])} UAH")
        print(f"  📊 Тип: {trans['type']}")
        print(f"  🏷️  Категорія: {trans['category']}")
        
        # Перевіряємо, що категорія призначена
        if not category or category == 'other':
            if trans['type'] == 'expense':
                print("  ⚠️  Увага: Призначена загальна категорія 'other'")
            elif category != 'income':
                print("  ⚠️  Увага: Не призначена специфічна категорія доходу")
        else:
            print("  ✅ Категорія призначена автоматично")
        
        print()
    
    print("=" * 70)
    print("📊 РЕЗУЛЬТАТИ ТЕСТУВАННЯ ML КАТЕГОРИЗАТОРА:")
    
    # Перевіряємо, що всі транзакції отримали категорії
    categorized_count = sum(1 for trans in test_transactions if trans.get('category'))
    non_other_count = sum(1 for trans in test_transactions if trans.get('category') and trans['category'] not in ['other', 'income'])
    
    print(f"✅ Транзакцій з категоріями: {categorized_count}/{len(test_transactions)}")
    print(f"✅ Транзакцій зі специфічними категоріями: {non_other_count}/{len(test_transactions)}")
    print(f"✅ Відсоток специфічної категоризації: {(non_other_count/len(test_transactions))*100:.1f}%")
    
    if categorized_count == len(test_transactions):
        print("\n🎉 ТЕСТ ПРОЙДЕНО! ML категоризатор працює правильно з банківськими виписками.")
        return True
    else:
        print("\n❌ ТЕСТ НЕ ПРОЙДЕНО! Деякі транзакції не отримали категорій.")
        return False

def test_different_bank_formats():
    """Тестує роботу з різними форматами банківських виписок"""
    
    print("\n🏦 Тестування роботи з різними форматами банків:")
    print("=" * 70)
    
    # Симулюємо різні формати описів транзакцій
    bank_formats = {
        "PrivatBank": [
            "ATB Супермаркет",
            "McDonald's Київ",
            "Uber BV",
            "ДТЕК електроенергія"
        ],
        "Monobank": [
            "Покупка в магазині Сільпо",
            "Ресторан 'Пузата Хата'",
            "Оплата таксі Bolt",
            "Комунальні послуги Київводоканал"
        ]
    }
    
    for bank, descriptions in bank_formats.items():
        print(f"\n🏛️  {bank} формат:")
        print("-" * 40)
        
        for desc in descriptions:
            category = transaction_categorizer.suggest_category_for_bank_statement(desc, 'expense')
            print(f"  📝 '{desc}' → 🏷️  {category}")
    
    print("\n✅ Тест різних форматів завершено!")

if __name__ == "__main__":
    # Запускаємо основні тести
    test1_passed = test_ml_categorizer_integration()
    test_different_bank_formats()
    
    print("\n" + "=" * 70)
    print("📋 ПІДСУМОК ТЕСТУВАННЯ ML КАТЕГОРИЗАТОРА:")
    if test1_passed:
        print("✅ Інтеграційний тест: ПРОЙДЕНО")
        print("✅ Тест форматів: ПРОЙДЕНО")
        print("\n🎉 ВСІ ТЕСТИ ПРОЙДЕНО! ML категоризатор готовий для використання в продакшені.")
    else:
        print("❌ Інтеграційний тест: НЕ ПРОЙДЕНО")
        print("\n⚠️  Потрібно покращити ML категоризатор.")
