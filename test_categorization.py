#!/usr/bin/env python3
"""
Тест автоматичної категоризації транзакцій
"""

import logging
from services.ml_categorizer import TransactionCategorizer

# Налаштовуємо логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_categorization():
    """Тестуємо автоматичну категоризацію"""
    
    # Створюємо категоризатор
    categorizer = TransactionCategorizer()
    
    # Тестові категорії користувача
    user_categories = [
        {'id': 1, 'name': 'Продукти', 'type': 'expense'},
        {'id': 2, 'name': 'Транспорт', 'type': 'expense'},
        {'id': 3, 'name': 'Житло', 'type': 'expense'},
        {'id': 4, 'name': 'Розваги', 'type': 'expense'},
        {'id': 5, 'name': 'Техніка', 'type': 'expense'},
        {'id': 6, 'name': 'Кафе та ресторани', 'type': 'expense'},
        {'id': 7, 'name': 'Інше', 'type': 'expense'},
        {'id': 16, 'name': 'Зарплата', 'type': 'income'},
        {'id': 17, 'name': 'Фріланс', 'type': 'income'},
        {'id': 23, 'name': 'Інше', 'type': 'income'},
    ]
    
    # Тестові транзакції
    test_transactions = [
        {'description': 'Uklon', 'type': 'expense', 'amount': 105.0},
        {'description': 'Apple', 'type': 'expense', 'amount': 0.99},
        {'description': 'Сільпо', 'type': 'expense', 'amount': 458.84},
        {'description': 'АТБ', 'type': 'expense', 'amount': 118.5},
        {'description': 'Нова пошта', 'type': 'expense', 'amount': 65.0},
        {'description': 'Spotify', 'type': 'expense', 'amount': 2.49},
        {'description': 'ФОП Мельник Роман Андрийович', 'type': 'income', 'amount': 450.0},
        {'description': 'Степанов Є.', 'type': 'income', 'amount': 1005.03},
        {'description': 'На картку', 'type': 'income', 'amount': 200.0},
        {'description': 'Сім23', 'type': 'income', 'amount': 186.0},
    ]
    
    print("🔍 Тестування автоматичної категоризації\n")
    print("=" * 80)
    
    for i, trans in enumerate(test_transactions, 1):
        description = trans['description']
        trans_type = trans['type']
        amount = trans['amount']
        
        # Фільтруємо категорії за типом
        type_categories = [cat for cat in user_categories if cat['type'] == trans_type]
        
        # Пробуємо категоризацію
        suggested_category = categorizer.get_best_category_for_user(
            description=description,
            amount=amount,
            transaction_type=trans_type,
            user_categories=type_categories
        )
        
        if suggested_category:
            category_name = suggested_category['name']
            category_id = suggested_category['id']
            status = "✅"
        else:
            category_name = "Не визначено"
            category_id = "N/A"
            status = "❌"
        
        print(f"{i:2d}. {status} {description:30s} | {trans_type:7s} | {category_name:15s} (ID: {category_id})")
    
    print("=" * 80)

if __name__ == "__main__":
    test_categorization()
