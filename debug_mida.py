#!/usr/bin/env python3
"""
Тестування розпізнавання MIDA індикаторів
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.free_receipt_parser import free_receipt_parser
from services.mida_receipt_parser import mida_receipt_parser
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)

def test_mida_detection(image_path: str):
    """Тестує розпізнавання MIDA індикаторів"""
    result = free_receipt_parser.parse_receipt(image_path)
    
    if result:
        text = result.get('raw_text', '')
        print("=== ПОВНИЙ ТЕКСТ ===")
        print(text)
        print("\n=== ТЕСТ MIDA ІНДИКАТОРІВ ===")
        
        # Тестуємо кожен індикатор
        indicators = ['міда', 'mida', 'лютіков', '2903314199']
        for indicator in indicators:
            if indicator in text.lower():
                print(f"✅ Знайдено: {indicator}")
            else:
                print(f"❌ Не знайдено: {indicator}")
        
        # Тестуємо функцію is_mida_receipt безпосередньо
        print(f"\n=== РЕЗУЛЬТАТ is_mida_receipt ===")
        is_mida = mida_receipt_parser.is_mida_receipt(text)
        print(f"Розпізнано як MIDA: {is_mida}")
    else:
        print("Не вдалося розпізнати текст")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Використання: python debug_mida.py <шлях_до_фото>")
        sys.exit(1)
    
    test_mida_detection(sys.argv[1])
