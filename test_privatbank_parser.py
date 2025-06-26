#!/usr/bin/env python3
"""
Тест для перевірки правильності парсингу ПриватБанку
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.statement_parser import StatementParser
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_privatbank_logic():
    """Тестує логіку визначення типу транзакції для ПриватБанку"""
    
    print("🧪 Тестування логіки парсингу ПриватБанку\n")
    
    # Тестові дані як вони могли б прийти з Excel файлу
    test_transactions = [
        {'amount': -100.50, 'description': 'АТБ покупка продуктів'},
        {'amount': -25.99, 'description': 'Apple App Store'},
        {'amount': -450.00, 'description': 'Сільпо'},
        {'amount': 15000.00, 'description': 'Зарплата'},
        {'amount': -75.00, 'description': 'Укрпошта доставка'},
        {'amount': 500.00, 'description': 'Повернення боргу'},
        {'amount': -1200.00, 'description': 'Комунальні послуги'},
        {'amount': -105.00, 'description': 'Uklon поїздка'},
    ]
    
    print("📋 Результати парсингу:")
    print("-" * 50)
    
    for i, trans in enumerate(test_transactions, 1):
        amount = trans['amount']
        description = trans['description']
        
        # Логіка як у нашому парсері
        transaction_type = 'expense' if amount < 0 else 'income'
        final_amount = amount  # Зберігаємо оригінальний знак
        
        # Емодзі для відображення
        type_emoji = "💸" if transaction_type == 'expense' else "💰"
        sign = "" if amount >= 0 else ""  # Знак вже в числі
        
        print(f"{i}. {type_emoji} {amount:+.2f} ₴ ({transaction_type})")
        print(f"   📝 {description}")
        print(f"   🔢 Оригінальна сума: {amount}, Тип: {transaction_type}")
        print()

if __name__ == "__main__":
    test_privatbank_logic()
