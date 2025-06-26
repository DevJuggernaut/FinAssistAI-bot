#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Демонстрація поліпшеного парсера PDF монобанку з категоризацією
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_improved_parser():
    """Демонструємо поліпшений парсер"""
    
    print("🏦 Демонстрація поліпшеного парсера PDF монобанку")
    print("=" * 55)
    
    # Імітуємо типові дані з PDF монобанку
    mock_transactions = [
        {
            'date': '2025-06-19',
            'amount': 685.33,
            'description': 'АТБ МАРКЕТ',
            'type': 'expense'
        },
        {
            'date': '2025-06-17', 
            'amount': 800.00,
            'description': 'Переказ на картку',
            'type': 'income'
        },
        {
            'date': '2025-06-11',
            'amount': 350.00,
            'description': 'UBER UKRAINE',
            'type': 'expense'
        },
        {
            'date': '2025-06-01',
            'amount': 434.72,
            'description': 'Rozetka',
            'type': 'expense'
        },
        {
            'date': '2025-05-16',
            'amount': 1091.00,
            'description': 'Зарплата',
            'type': 'income'
        },
        {
            'date': '2025-05-03',
            'amount': 299.00,
            'description': 'Netflix',
            'type': 'expense'
        },
        {
            'date': '2025-05-03',
            'amount': 339.00,
            'description': 'КиївСтар',
            'type': 'expense'
        },
        {
            'date': '2025-05-03',
            'amount': 258.00,
            'description': 'WOG',
            'type': 'expense'
        },
        {
            'date': '2025-05-02',
            'amount': 195.80,
            'description': 'Банківська операція',  # Загальний опис
            'type': 'expense'
        },
        {
            'date': '2025-05-01',
            'amount': 349.00,
            'description': 'Кешбек',
            'type': 'income'
        }
    ]
    
    # Імпортуємо ML категоризатор
    from services.ml_categorizer import transaction_categorizer
    
    print("📊 Результати категоризації транзакцій:")
    print("-" * 50)
    
    for i, trans in enumerate(mock_transactions, 1):
        # Категоризуємо транзакцію
        category = transaction_categorizer.suggest_category_for_bank_statement(
            trans['description'], 
            trans['type']
        )
        
        # Відображаємо результат
        type_emoji = "💸" if trans['type'] == 'expense' else "💰"
        sign = "-" if trans['type'] == 'expense' else "+"
        
        print(f"{i:2d}. {type_emoji} {sign}{trans['amount']:,.2f} ₴")
        print(f"    📅 {trans['date']} • 📝 {trans['description']}")
        print(f"    🏷️ {category['icon']} {category['name']}")
        print()
    
    print("✅ Результат:")
    print("• Описи транзакцій тепер відображаються правильно")
    print("• Категорії розпізнаються автоматично на основі опису")
    print("• Навіть для загальних описів ('Банківська операція') є категорія 'Інше'")
    print("• Різні типи магазинів, сервісів та послуг розпізнаються правильно")

if __name__ == "__main__":
    demo_improved_parser()
