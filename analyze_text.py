#!/usr/bin/env python3
"""
Детальний аналіз розпізнаного тексту
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.free_receipt_parser import free_receipt_parser
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)

def analyze_text(image_path: str):
    """Аналізує розпізнаний текст"""
    result = free_receipt_parser.parse_receipt(image_path)
    
    if result:
        print("=== ПОВНИЙ РОЗПІЗНАНИЙ ТЕКСТ ===")
        print(result.get('raw_text', ''))
        print("=== КІНЕЦЬ ТЕКСТУ ===")
    else:
        print("Не вдалося розпізнати текст")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Використання: python analyze_text.py <шлях_до_фото>")
        sys.exit(1)
    
    analyze_text(sys.argv[1])
