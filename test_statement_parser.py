#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки функціональності парсингу банківських виписок
"""

import asyncio
import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Додаємо шлях до проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.statement_parser import StatementParser

async def test_csv_parsing():
    """Тестує парсинг CSV файлу"""
    print("🧪 Тестуємо парсинг CSV файлу...")
    
    # Створюємо тестовий CSV файл
    test_data = {
        'Дата': ['01.01.2024', '02.01.2024', '03.01.2024'],
        'Сума': [-150.00, 3500.00, -89.50],
        'Опис': ['Покупки в магазині', 'Зарплата', 'Кафе']
    }
    
    test_csv_path = 'test_transactions.csv'
    df = pd.DataFrame(test_data)
    df.to_csv(test_csv_path, index=False, encoding='utf-8')
    
    try:
        parser = StatementParser()
        transactions = await parser.parse_csv(test_csv_path)
        
        print(f"✅ Успішно розпізнано {len(transactions)} транзакцій:")
        for i, trans in enumerate(transactions, 1):
            print(f"  {i}. {trans['date']} - {trans['amount']:.2f} ₴ - {trans['description']} ({trans['type']})")
        
        return True
    except Exception as e:
        print(f"❌ Помилка при парсингу CSV: {str(e)}")
        return False
    finally:
        # Видаляємо тестовий файл
        if os.path.exists(test_csv_path):
            os.remove(test_csv_path)

async def test_excel_parsing():
    """Тестує парсинг Excel файлу"""
    print("\n🧪 Тестуємо парсинг Excel файлу...")
    
    # Створюємо тестовий Excel файл
    test_data = {
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'Amount': [-75.25, 2000.00, -42.80],
        'Description': ['Grocery store', 'Salary payment', 'Coffee shop']
    }
    
    test_excel_path = 'test_transactions.xlsx'
    df = pd.DataFrame(test_data)
    df.to_excel(test_excel_path, index=False)
    
    try:
        parser = StatementParser()
        transactions = await parser.parse_excel(test_excel_path)
        
        print(f"✅ Успішно розпізнано {len(transactions)} транзакцій:")
        for i, trans in enumerate(transactions, 1):
            print(f"  {i}. {trans['date']} - {trans['amount']:.2f} ₴ - {trans['description']} ({trans['type']})")
        
        return True
    except Exception as e:
        print(f"❌ Помилка при парсингу Excel: {str(e)}")
        return False
    finally:
        # Видаляємо тестовий файл
        if os.path.exists(test_excel_path):
            os.remove(test_excel_path)

async def test_validation():
    """Тестує валідацію транзакцій"""
    print("\n🧪 Тестуємо валідацію та очищення транзакцій...")
    
    parser = StatementParser()
    
    # Тестові дані з різними проблемами
    test_transactions = [
        {'date': datetime(2024, 1, 1), 'amount': 100.0, 'description': 'Нормальна транзакція', 'type': 'expense'},
        {'date': None, 'amount': 50.0, 'description': 'Без дати', 'type': 'expense'},  # Має бути відфільтрована
        {'date': datetime(2020, 1, 1), 'amount': 200.0, 'description': 'Стара транзакція', 'type': 'expense'},  # Стара дата
        {'date': datetime(2024, 1, 2), 'amount': 1500000.0, 'description': 'Дуже велика сума', 'type': 'expense'},  # Велика сума
        {'date': datetime(2024, 1, 3), 'amount': 75.0, 'description': '', 'type': 'expense'},  # Без опису
    ]
    
    cleaned = parser._clean_and_validate_transactions(test_transactions)
    
    print(f"📊 Результати валідації:")
    print(f"  Початкових транзакцій: {len(test_transactions)}")
    print(f"  Валідних транзакцій: {len(cleaned)}")
    print(f"  Відфільтровано: {len(test_transactions) - len(cleaned)}")
    
    for i, trans in enumerate(cleaned, 1):
        print(f"  {i}. {trans['date'].strftime('%Y-%m-%d')} - {trans['amount']:.2f} ₴ - {trans['description']}")
    
    return len(cleaned) > 0

async def main():
    """Основна функція тестування"""
    print("🚀 Запуск тестів StatementParser...")
    print("=" * 50)
    
    tests = [
        ("CSV парсинг", test_csv_parsing),
        ("Excel парсинг", test_excel_parsing),
        ("Валідація", test_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критична помилка в тесті '{test_name}': {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📋 Результати тестування:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕНО" if result else "❌ ПРОВАЛЕНО"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Загальний результат: {passed}/{len(tests)} тестів пройдено")
    
    if passed == len(tests):
        print("🎉 Усі тести пройдено успішно! StatementParser готовий до роботи.")
    else:
        print("⚠️  Деякі тести провалилися. Перевірте помилки вище.")

if __name__ == "__main__":
    asyncio.run(main())
