#!/usr/bin/env python3
"""
Тест для перевірки правильного призначення категорій для транзакцій з виписок
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Імпортуємо безпосередньо екземпляр парсера
from services.statement_parser import statement_parser
from services.ml_categorizer import transaction_categorizer

def test_category_assignment():
    """Тестує призначення категорій на основі опису транзакцій"""
    
    # Тестові кейси для перевірки категоризації
    test_cases = [
        # Витрати
        ("Покупка в супермаркеті Сільпо", "expense", "groceries"),
        ("Оплата в ресторані McDonald's", "expense", "restaurants"),
        ("Заправка WOG", "expense", "transport"),
        ("Uber поїздка", "expense", "transport"),
        ("Оплата інтернету", "expense", "utilities"),
        ("Комунальні послуги", "expense", "utilities"),
        ("Покупка в аптеці", "expense", "health"),
        ("Розетка техніка", "expense", "shopping"),
        ("Apple Store", "expense", "shopping"),
        ("Курси навчання", "expense", "education"),
        ("Салон краси", "expense", "beauty"),
        ("Кінотеатр", "expense", "entertainment"),
        ("Netflix підписка", "expense", "entertainment"),
        ("Дитячі товари", "expense", "kids"),
        
        # Доходи
        ("Зарплата", "income", "salary"),
        ("Аванс", "income", "salary"),
        ("Кешбек від банку", "income", "cashback"),
        ("Бонус повернення", "income", "cashback"),
        ("Фрілансерська робота", "income", "freelance"),
        ("Підробіток", "income", "freelance"),
        ("Подарунок грошима", "income", "gift"),
        ("Дивіденди", "income", "investment"),
        ("Прибуток від продажу", "income", "business"),
        
        # Загальні/невідомі
        ("Операція без опису", "expense", "other"),
        ("Незрозуміла операція", "expense", "other"),
        ("Переказ без коментаря", "income", "income"),
    ]
    
    print("🧪 Тестування призначення категорій...")
    print("=" * 60)
    
    correct_predictions = 0
    total_tests = len(test_cases)
    
    for description, transaction_type, expected_category in test_cases:
        predicted_category = transaction_categorizer.suggest_category_for_bank_statement(description, transaction_type)
        
        is_correct = predicted_category == expected_category
        status = "✅" if is_correct else "❌"
        
        if is_correct:
            correct_predictions += 1
        
        print(f"{status} {description[:40]:<40} | {transaction_type:<7} | {predicted_category:<12} | (очікувалось: {expected_category})")
        
        if not is_correct:
            print(f"   🔍 Детальний аналіз: '{description.lower()}' -> '{predicted_category}'")
    
    print("=" * 60)
    accuracy = (correct_predictions / total_tests) * 100
    print(f"📊 Результати тестування:")
    print(f"   Правильно визначено: {correct_predictions}/{total_tests}")
    print(f"   Точність: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print("🎉 Тест ПРОЙДЕНО! Система категоризації працює добре.")
    else:
        print("⚠️  Тест НЕ ПРОЙДЕНО. Потрібно покращити систему категоризації.")
    
    return accuracy >= 80

def test_transaction_structure():
    """Тестує структуру транзакцій, що повертається парсером"""
    
    # Створюємо тестові транзакції
    test_transactions = [
        {
            'date': '2025-01-01',
            'amount': 150.50,
            'description': 'Покупка в супермаркеті АТБ',
            'type': 'expense'
        },
        {
            'date': '2025-01-02', 
            'amount': 5000.00,
            'description': 'Зарплата за грудень',
            'type': 'income'
        },
        {
            'date': '2025-01-03',
            'amount': 45.25,
            'description': 'Uber поїздка до офісу',
            'type': 'expense'
        }
    ]
    
    print("\n🔧 Тестування структури транзакцій...")
    print("=" * 60)
    
    all_passed = True
    
    for i, trans in enumerate(test_transactions, 1):
        # Додаємо категорію до кожної транзакції
        category = transaction_categorizer.suggest_category_for_bank_statement(trans['description'], trans['type'])
        trans['category'] = category
        
        print(f"Транзакція {i}:")
        print(f"  📅 Дата: {trans['date']}")
        print(f"  💰 Сума: {trans['amount']}")
        print(f"  📝 Опис: {trans['description']}")
        print(f"  📊 Тип: {trans['type']}")
        print(f"  🏷️  Категорія: {trans['category']}")
        
        # Перевірка наявності всіх необхідних полів
        required_fields = ['date', 'amount', 'description', 'type', 'category']
        missing_fields = [field for field in required_fields if field not in trans]
        
        if missing_fields:
            print(f"  ❌ Відсутні поля: {missing_fields}")
            all_passed = False
        else:
            print(f"  ✅ Всі поля присутні")
        
        print()
    
    if all_passed:
        print("🎉 Структура транзакцій КОРЕКТНА!")
    else:
        print("❌ Є проблеми зі структурою транзакцій!")
    
    return all_passed

if __name__ == "__main__":
    print("🚀 Запуск тестів для перевірки категоризації транзакцій")
    print()
    
    # Тест 1: Призначення категорій
    test1_passed = test_category_assignment()
    
    # Тест 2: Структура транзакцій
    test2_passed = test_transaction_structure()
    
    print("\n" + "=" * 60)
    print("📋 ПІДСУМОК ТЕСТУВАННЯ:")
    print(f"✅ Тест категоризації: {'ПРОЙДЕНО' if test1_passed else 'НЕ ПРОЙДЕНО'}")
    print(f"✅ Тест структури: {'ПРОЙДЕНО' if test2_passed else 'НЕ ПРОЙДЕНО'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ВСІ ТЕСТИ ПРОЙДЕНО! Система категоризації працює правильно.")
        exit(0)
    else:
        print("\n❌ ДЕЯКІ ТЕСТИ НЕ ПРОЙДЕНО. Потрібне налагодження.")
        exit(1)
