#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестовий скрипт для перевірки поліпшеного ML категоризатора
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ml_categorizer import transaction_categorizer

def test_categorization():
    """Тестуємо категоризацію різних типів транзакцій"""
    
    print("🧪 Тестування поліпшеного ML категоризатора")
    print("=" * 50)
    
    # Тестові транзакції для витрат
    expense_tests = [
        "АТБ Маркет",
        "Сільпо",
        "UBER",
        "Bolt Food",
        "КиївСтар",
        "Netflix",
        "Rozetka",
        "Макдональдс",
        "Аптека",
        "WOG",
        "Банківська операція",  # Загальна назва
        "",  # Порожній опис
    ]
    
    # Тестові транзакції для доходів
    income_tests = [
        "Зарплата",
        "Переказ на картку",
        "Фриланс проект",
        "Кешбек",
        "Банківська операція",  # Загальна назва для доходу
        "",  # Порожній опис для доходу
    ]
    
    print("\n💸 Тестування категоризації витрат:")
    print("-" * 40)
    
    for desc in expense_tests:
        category = transaction_categorizer.categorize_transaction(desc, 100.0, 'expense')
        print(f"'{desc}' → {category['icon']} {category['name']} (ID: {category['id']})")
    
    print("\n💰 Тестування категоризації доходів:")
    print("-" * 40)
    
    for desc in income_tests:
        category = transaction_categorizer.categorize_transaction(desc, 100.0, 'income')
        print(f"'{desc}' → {category['icon']} {category['name']} (ID: {category['id']})")
    
    print("\n🔄 Тестування suggest_category_for_bank_statement:")
    print("-" * 50)
    
    test_cases = [
        ("АТБ Супермаркет", 'expense'),
        ("UBER поїздка", 'expense'),
        ("Переказ від клієнта", 'income'),
        ("", 'expense'),  # Порожній опис
        ("", 'income'),   # Порожній опис
    ]
    
    for desc, trans_type in test_cases:
        category = transaction_categorizer.suggest_category_for_bank_statement(desc, trans_type)
        emoji = "💸" if trans_type == 'expense' else "💰"
        print(f"{emoji} '{desc}' ({trans_type}) → {category['icon']} {category['name']} (ID: {category['id']})")

if __name__ == "__main__":
    test_categorization()
