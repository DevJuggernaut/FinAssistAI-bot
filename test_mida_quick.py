#!/usr/bin/env python3
"""
Швидкий тест для перевірки роботи MIDA парсера
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.mida_receipt_parser import mida_receipt_parser
from services.free_receipt_parser import free_receipt_parser

def test_mida_parser():
    """Тестує роботу MIDA парсера"""
    
    # Тестовий текст MIDA чеку
    test_text = """
    ФОП ЛЮТІКОВ ВІТАЛІЙ ВАЛЕРІЮОВИЧ
    ЄДРПОУ 2903314199
    vul. Lazurna, 19, Mykolaiv, Mykolaivska oblast
    
    АРТ. № 12345 / Хліб білий 25.50
    АРТ. № 23456 / Молоко 3,2% 45.80
    АРТ. № 34567 / Цукерки Roshen 125.90
    АРТ. № 45678 / Coca-Cola 0,5л 32.00
    
    СУМА ДО СПЛАТИ: 229.20
    25.02.2024 14:30:25
    """
    
    print("🧪 Тестуємо розпізнавання MIDA...")
    
    # Симулюємо парсинг (без реального файлу)
    result = mida_receipt_parser._parse_text(test_text)
    
    print(f"Результат: {result}")
    
    if result:
        print("✅ MIDA розпізнано успішно!")
        print(f"Загальна сума: {result.get('total_amount', 'невідомо')}")
        print(f"Категорізовані товари: {len(result.get('categorized_items', {}))}")
        
        for category, data in result.get('categorized_items', {}).items():
            if isinstance(data, dict):
                print(f"  📂 {category}: {data.get('item_count', 0)} товарів, {data.get('total_amount', 0):.2f} грн")
    else:
        print("❌ MIDA не розпізнано")
    
    return result

if __name__ == "__main__":
    test_mida_parser()
