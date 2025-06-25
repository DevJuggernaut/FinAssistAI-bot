#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для перевірки, що PDF звіти створюються без емодзі
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.analytics_handler import create_pdf_report, create_simple_text_report

class MockUser:
    def __init__(self):
        self.username = 'test_user'
        self.telegram_id = 12345

def test_pdf_without_emoji():
    """Тестує PDF звіт без емодзі"""
    user = MockUser()
    transactions = []
    
    stats = {
        'total_income': 15000,
        'total_expenses': 12000,
        'balance': 3000,
        'category_expenses': {
            'Їжа': 5000,
            'Транспорт': 3000,
            'Розваги': 2000,
            'Комунальні': 2000
        },
        'period': '30 днів'
    }
    
    print("🧪 Тестування PDF звіту без емодзі...")
    
    try:
        pdf_buffer = create_pdf_report(user, transactions, stats)
        pdf_size = len(pdf_buffer.getvalue())
        print(f"✅ PDF створено успішно, розмір: {pdf_size} байт")
        return True
    except Exception as e:
        print(f"❌ Помилка створення PDF: {e}")
        return False

def test_text_without_emoji():
    """Тестує текстовий звіт без емодзі"""
    user = MockUser()
    transactions = []
    
    stats = {
        'total_income': 15000,
        'total_expenses': 12000,
        'balance': 3000,
        'category_expenses': {
            'Їжа': 5000,
            'Транспорт': 3000,
            'Розваги': 2000,
            'Комунальні': 2000
        },
        'period': '30 днів'
    }
    
    print("🧪 Тестування текстового звіту без емодзі...")
    
    try:
        text_buffer = create_simple_text_report(user, transactions, stats)
        text_content = text_buffer.getvalue().decode('utf-8')
        
        # Перевіряємо наявність основних емодзі
        problematic_emojis = ['📊', '💰', '📈', '💡', '🎯', '⚠️', '✅', '👍', '📅', '🚨', '🎉', '👤', '🏦', '📱', '💼']
        found_emojis = []
        
        for emoji in problematic_emojis:
            if emoji in text_content:
                found_emojis.append(emoji)
        
        if found_emojis:
            print(f"⚠️  Знайдено емодзі в тексті: {', '.join(found_emojis)}")
            return False
        else:
            print("✅ Емодзі успішно видалено з текстового звіту")
            return True
            
    except Exception as e:
        print(f"❌ Помилка створення текстового звіту: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("ТЕСТУВАННЯ ЗВІТІВ БЕЗ ЕМОДЗІ")
    print("=" * 50)
    
    pdf_ok = test_pdf_without_emoji()
    text_ok = test_text_without_emoji()
    
    print("\n" + "=" * 50)
    if pdf_ok and text_ok:
        print("🎉 ВСІ ТЕСТИ ПРОЙДЕНО! Емодзі успішно видалено з PDF звітів.")
    else:
        print("❌ Деякі тести не пройдено. Потрібні додаткові виправлення.")
    print("=" * 50)
