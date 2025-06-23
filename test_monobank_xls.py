#!/usr/bin/env python3
"""
Тест для парсингу XLS файлів Monobank
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.statement_parser import StatementParser
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_monobank_xls_parser():
    """
    Тестує парсер XLS файлів Monobank
    """
    parser = StatementParser()
    
    # Шлях до тестового файлу
    test_file = "data/test_monobank.xls"  # Замініть на реальний шлях
    
    if not os.path.exists(test_file):
        logger.error(f"Тестовий файл не знайдено: {test_file}")
        print("❌ Тестовий файл не знайдено")
        print("Створіть файл data/test_monobank.xls або змініть шлях у коді")
        return False
    
    try:
        logger.info(f"Тестування парсингу файлу: {test_file}")
        transactions = parser._parse_monobank_xls(test_file)
        
        print(f"✅ Успішно розпізнано {len(transactions)} транзакцій")
        
        # Виводимо кілька прикладів
        for i, transaction in enumerate(transactions[:5]):
            print(f"\nТранзакція {i+1}:")
            print(f"  Дата: {transaction['date']}")
            print(f"  Час: {transaction['time']}")
            print(f"  Сума: {transaction['amount']}")
            print(f"  Тип: {transaction['type']}")
            print(f"  Опис: {transaction['description']}")
        
        if len(transactions) > 5:
            print(f"\n... та ще {len(transactions) - 5} транзакцій")
        
        return True
        
    except Exception as e:
        logger.error(f"Помилка при тестуванні: {str(e)}", exc_info=True)
        print(f"❌ Помилка: {str(e)}")
        return False

def test_with_sample_data():
    """
    Тест з зразковими даними
    """
    print("\n" + "="*50)
    print("ТЕСТ ПАРСЕРА XLS ФАЙЛІВ MONOBANK")
    print("="*50)
    
    success = test_monobank_xls_parser()
    
    if success:
        print("\n✅ Всі тести пройшли успішно!")
    else:
        print("\n❌ Тести не пройшли. Перевірте файл та логи.")

if __name__ == "__main__":
    test_with_sample_data()
