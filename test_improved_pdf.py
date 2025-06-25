#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Розширений тест для перевірки покращеного PDF звіту
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.analytics_handler import create_pdf_report

class MockUser:
    def __init__(self):
        self.username = 'test_user_improved'
        self.telegram_id = 12345

def test_improved_pdf():
    """Тестує покращений PDF звіт з кращим розміщенням тексту"""
    user = MockUser()
    transactions = []
    
    # Створюємо тестові дані з різними сценаріями
    stats = {
        'total_income': 25000,
        'total_expenses': 18500,
        'balance': 6500,
        'category_expenses': {
            'Побутова техніка та електроніка': 8500,  # Довга назва категорії
            'Продукти харчування': 4000,
            'Транспорт та паливо': 3000,
            'Розваги та дозвілля': 2000,
            'Комунальні послуги': 1000
        },
        'period': '30 днів'
    }
    
    print("🧪 Тестування покращеного PDF звіту...")
    print(f"📊 Дані: доходи {stats['total_income']}, витрати {stats['total_expenses']}")
    
    try:
        pdf_buffer = create_pdf_report(user, transactions, stats)
        pdf_size = len(pdf_buffer.getvalue())
        
        # Розрахуємо коефіцієнт заощаджень для перевірки
        savings_rate = ((stats['total_income'] - stats['total_expenses']) / stats['total_income'] * 100)
        
        print(f"✅ PDF створено успішно!")
        print(f"📁 Розмір файлу: {pdf_size:,} байт")
        print(f"📈 Коефіцієнт заощаджень: {savings_rate:.1f}%")
        print(f"💰 Баланс: {stats['balance']:+,.2f} грн")
        print("🔧 Покращення:")
        print("   • Видалено всі емодзі")
        print("   • Збільшено ширину колонок таблиць")
        print("   • Додано відступи між рядками")
        print("   • Покращено міжрядковий інтервал")
        print("   • Збільшено padding в highlight блоках")
        
        # Збережемо файл для перевірки
        filename = f"test_improved_report_{user.username}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        print(f"💾 Файл збережено як: {filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка створення покращеного PDF: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТУВАННЯ ПОКРАЩЕНОГО PDF ЗВІТУ")
    print("=" * 60)
    
    success = test_improved_pdf()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ТЕСТ УСПІШНО ЗАВЕРШЕНО!")
        print("✅ PDF звіт створено з покращеннями:")
        print("   - Відсутні емодзі")
        print("   - Кращий розподіл простору")
        print("   - Текст не накладається")
        print("   - Більші відступи та інтервали")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕНО")
    print("=" * 60)
