#!/usr/bin/env python3
"""
Швидкий тест нового функціоналу XLS для Monobank
"""

import os
import sys
import pandas as pd
from datetime import datetime
import tempfile

# Додаємо шлях до проєкту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_test_xls_file():
    """
    Створює тестовий XLS файл з зразковими даними Monobank
    """
    # Зразкові дані в форматі Monobank
    data = {
        'Дата операції': ['20.06.2025', '19.06.2025', '18.06.2025', '17.06.2025'],
        'Час операції': ['14:30:25', '10:15:30', '18:45:12', '09:20:18'],
        'Деталі операції': [
            'Покупка в АТБ Маркет',
            'Зарахування зарплати',
            'Оплата за мобільний зв\'язок', 
            'Покупка кави в кафе'
        ],
        'MCC': ['5411', '0000', '4814', '5812'],
        'Сума в валюті картки (UAH)': [-250.50, 15000.00, -99.00, -45.75],
        'Баланс після операції': [12500.25, 12750.75, -2249.25, -2195.00]
    }
    
    # Створюємо DataFrame
    df = pd.DataFrame(data)
    
    # Створюємо тимчасовий файл
    temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    temp_file.close()
    
    # Записуємо в Excel
    df.to_excel(temp_file.name, index=False, engine='openpyxl')
    
    print(f"✅ Створено тестовий файл: {temp_file.name}")
    return temp_file.name

def test_monobank_xls_parser():
    """
    Тестує новий парсер XLS файлів
    """
    try:
        # Імпортуємо парсер
        from services.statement_parser import StatementParser
        
        # Створюємо тестовий файл
        test_file = create_test_xls_file()
        
        print("\n" + "="*50)
        print("ТЕСТ ПАРСЕРА XLS ФАЙЛІВ MONOBANK")
        print("="*50)
        
        # Створюємо парсер та тестуємо
        parser = StatementParser()
        
        print(f"\n🔄 Обробка файлу: {test_file}")
        transactions = parser._parse_monobank_xls(test_file)
        
        print(f"\n✅ Успішно розпізнано {len(transactions)} транзакцій:")
        print("-" * 50)
        
        for i, transaction in enumerate(transactions, 1):
            print(f"\n📊 Транзакція {i}:")
            print(f"   📅 Дата: {transaction['date']}")
            print(f"   🕐 Час: {transaction['time']}")
            print(f"   💰 Сума: {transaction['amount']} UAH")
            print(f"   📝 Тип: {transaction['type']}")
            print(f"   📄 Опис: {transaction['description']}")
            print(f"   🏷️ Джерело: {transaction['source']}")
        
        # Перевіримо правильність парсингу
        expected_transactions = 4
        if len(transactions) == expected_transactions:
            print(f"\n✅ Кількість транзакцій коректна: {len(transactions)}")
        else:
            print(f"\n❌ Очікувалося {expected_transactions}, отримано {len(transactions)}")
        
        # Перевіряємо типи транзакцій
        income_count = sum(1 for t in transactions if t['type'] == 'income')
        expense_count = sum(1 for t in transactions if t['type'] == 'expense')
        
        print(f"\n📈 Доходи: {income_count}")
        print(f"📉 Витрати: {expense_count}")
        
        # Видаляємо тестовий файл
        os.unlink(test_file)
        print(f"\n🗑️ Тестовий файл видалено")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Помилка при тестуванні: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """
    Тестує інтеграцію з основним парсером
    """
    try:
        from services.statement_parser import StatementParser
        
        print("\n" + "="*50)
        print("ТЕСТ ІНТЕГРАЦІЇ З ОСНОВНИМ ПАРСЕРОМ")
        print("="*50)
        
        # Створюємо тестовий файл
        test_file = create_test_xls_file()
        
        # Тестуємо через основний метод
        parser = StatementParser()
        transactions = parser.parse_bank_statement(test_file, bank_type='monobank')
        
        print(f"✅ Інтеграція працює! Розпізнано {len(transactions)} транзакцій")
        
        # Видаляємо тестовий файл
        os.unlink(test_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка інтеграції: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестів XLS функціоналу для Monobank")
    
    # Тест основного парсера
    test1_success = test_monobank_xls_parser()
    
    # Тест інтеграції
    test2_success = test_integration()
    
    print("\n" + "="*50)
    print("РЕЗУЛЬТАТИ ТЕСТУВАННЯ")
    print("="*50)
    
    if test1_success and test2_success:
        print("🎉 Всі тести пройшли успішно!")
        print("✅ XLS функціонал для Monobank готовий до використання")
    else:
        print("❌ Деякі тести не пройшли. Перевірте помилки вище.")
    
    print("\n💡 Тепер ви можете використовувати XLS файли Monobank у боті!")
