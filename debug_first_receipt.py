#!/usr/bin/env python3
"""
Дебаг скрипт для першого чека
"""

import re
import sys
import os

# Додаємо шлях до проекту
sys.path.append('/Users/abobina/telegram_bot/FinAssistAI-bot')

def debug_first_receipt():
    """Дебаг першого чека"""
    
    # Читаємо OCR результат першого чека
    with open('/Users/abobina/telegram_bot/FinAssistAI-bot/analysis_results_photo_2025-06-24 21.09.05.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Витягуємо стандартний OCR
    start = content.find('--- Стандартний OCR ---')
    end = content.find('--- OCR з налаштуваннями для цифр ---')
    ocr_text = content[start:end].replace('--- Стандартний OCR ---', '').strip()
    
    print("=== OCR ТЕКСТ ===")
    print(ocr_text)
    print()
    
    # Тест шаблонів
    store_patterns = [
        r'таврія.*плюс',
        r'таврія.*в',
        r'ставрія.*плюс',
        r'аврія',
        r'tavria.*plus',
        r'торговельний.*центр.*таврія',
        r'торговельний.*центр.*кафе',
        r'торговельний.*центр.*пефій',
        r'товговельним.*пецій',
        r'центр.*кафе.*таврія',
        r'торговельний.*комплекс',
        r'таврія.*премізм',
        r'nтаврі[яa]',
        r'таврі[а-я].*[плюc]',
        r'центрекдо',
        r'торговельний.*центрек',
        r'nn.*ставрія.*плюс',
        r'ставрія'
    ]
    
    text_lower = ocr_text.lower()
    print("=== ТЕСТ ШАБЛОНІВ ===")
    print(f"Текст (lower): {text_lower[:200]}...")
    print()
    
    for pattern in store_patterns:
        match = re.search(pattern, text_lower)
        if match:
            print(f"✅ ЗНАЙДЕНО: {pattern} -> {match.group()}")
        else:
            print(f"❌ НЕ ЗНАЙДЕНО: {pattern}")
    
    print("\n=== АНАЛІЗ СЛІВ ===")
    words = text_lower.split()
    for word in words:
        if 'авр' in word or 'тавр' in word or 'ставр' in word:
            print(f"Слово з 'авр': '{word}'")

if __name__ == "__main__":
    debug_first_receipt()
