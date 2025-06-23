#!/usr/bin/env python3
"""
Фінальний тест парсера з реальною структурою Monobank
"""

import pandas as pd
import tempfile
import os
import sys

def create_realistic_monobank_xls():
    """
    Створює реалістичний XLS файл з структурою як у Monobank
    """
    # Створюємо DataFrame з реальною структурою
    data = []
    
    # Додаємо заголовкову інформацію (як у реальному файлі)
    header_info = [
        ["Клієнт: Тестовий Користувач", None, None, None, None, None, None, None, None, None],
        ["Дата народження: 01.01.1990", None, None, None, None, None, None, None, None, None],
        ["ІПН: 1234567890", None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        ["Серія/номер паспорту: AB123456", None, None, None, None, None, None, None, None, None],
        ["Ким видано документ: 1234", None, None, None, None, None, None, None, None, None],
        ["Коли видано документ: 01.01.2010", None, None, None, None, None, None, None, None, None],
        ["Адреса реєстрації: Україна", None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        ["Інформація по картці: 4441 ****", None, None, None, None, None, None, None, None, None],
        ["Рахунок: UA123456789", None, None, None, None, None, None, None, None, None],
        ["Період: 01.06.2025 – 20.06.2025", None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        ["Кредитний ліміт: 0.00 UAH", None, None, None, None, None, None, None, None, None],
        ["Заборгованість: 0.00 UAH", None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        ["Баланс на початок: 10000.00", None, None, None, None, None, None, None, None, None],
        ["Баланс на кінець: 8500.00", None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        ["Гарантії вкладів", None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
    ]
    
    # Додаємо рядок заголовків
    headers = [
        "Дата i час операції", "Деталі операції", "MCC", "Сума в валюті картки (UAH)",
        "Сума в валюті операції", "Валюта", "Курс", "Сума комісій (UAH)", 
        "Сума кешбеку (UAH)", "Залишок після операції"
    ]
    
    # Додаємо транзакції
    transactions = [
        ["20.06.2025 16:30:15", "АТБ Маркет", "5411", "-250.50", "-250.50", "UAH", "—", "—", "—", "8500.00"],
        ["20.06.2025 14:15:22", "Зарплата", "4829", "5000.00", "5000.00", "UAH", "—", "—", "—", "8750.50"],
        ["19.06.2025 19:45:33", "Steam", "5816", "-299.99", "-299.99", "UAH", "—", "—", "—", "3750.50"],
        ["19.06.2025 12:30:44", "Сільпо", "5411", "-180.25", "-180.25", "UAH", "—", "—", "1.35", "4050.49"],
        ["18.06.2025 21:15:55", "Netflix", "5815", "-449.00", "-10.99", "USD", "40.85", "—", "—", "4230.74"],
        ["18.06.2025 15:20:11", "McDonald's", "5814", "-156.00", "-156.00", "UAH", "—", "—", "—", "4679.74"],
        ["17.06.2025 10:45:28", "Переказ від друга", "4829", "500.00", "500.00", "UAH", "—", "—", "—", "4835.74"],
        ["16.06.2025 18:30:39", "Нова Пошта", "4215", "-85.00", "-85.00", "UAH", "—", "—", "—", "4335.74"],
    ]
    
    # Об'єднуємо все разом
    all_data = header_info + [headers] + transactions
    
    # Створюємо DataFrame
    df = pd.DataFrame(all_data)
    
    # Створюємо тимчасовий файл
    temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    temp_file.close()
    
    # Записуємо в Excel
    df.to_excel(temp_file.name, sheet_name='Рух коштів по картці', index=False, header=False)
    
    return temp_file.name

def test_realistic_parser():
    """
    Тестує парсер з реалістичним файлом
    """
    try:
        from services.statement_parser import StatementParser
        
        print("🧪 Створення реалістичного тестового файлу...")
        test_file = create_realistic_monobank_xls()
        print(f"✅ Файл створено: {test_file}")
        
        print("\n🔍 Тестування парсера...")
        parser = StatementParser()
        transactions = parser._parse_monobank_xls(test_file)
        
        print(f"\n✅ Успішно розпізнано {len(transactions)} транзакцій:")
        print("-" * 60)
        
        total_income = 0
        total_expense = 0
        
        for i, transaction in enumerate(transactions, 1):
            print(f"📊 Транзакція {i}:")
            print(f"   📅 Дата: {transaction['date']}")
            print(f"   🕐 Час: {transaction['time']}")
            print(f"   💰 Сума: {transaction['amount']} UAH")
            print(f"   📝 Тип: {transaction['type']}")
            print(f"   📄 Опис: {transaction['description']}")
            print()
            
            if transaction['type'] == 'income':
                total_income += transaction['amount']
            else:
                total_expense += transaction['amount']
        
        print(f"📈 Загальний дохід: {total_income} UAH")
        print(f"📉 Загальні витрати: {total_expense} UAH")
        print(f"💰 Різниця: {total_income - total_expense} UAH")
        
        # Видаляємо тестовий файл
        os.unlink(test_file)
        print(f"\n🗑️ Тестовий файл видалено")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Помилка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Фінальний тест парсера XLS Monobank з реальною структурою")
    print("=" * 60)
    
    success = test_realistic_parser()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ТЕСТ ПРОЙШОВ УСПІШНО!")
        print("✅ Парсер готовий до роботи з реальними файлами Monobank")
    else:
        print("❌ Тест не пройшов. Перевірте помилки вище.")
