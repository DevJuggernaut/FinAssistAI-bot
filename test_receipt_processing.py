#!/usr/bin/env python3
"""
Тест обробки фотографій чеків без запуску бота
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.mida_receipt_parser import mida_receipt_parser
from services.free_receipt_parser import free_receipt_parser
from services.ml_categorizer import transaction_categorizer
from database.db_operations import get_or_create_user, add_transaction, get_user_categories
from datetime import datetime
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_receipt_processing(image_path: str):
    """Тестує обробку чеку без бота"""
    
    # Створюємо тестового користувача
    user = get_or_create_user(
        telegram_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User"
    )
    
    print(f"📱 Тестовий користувач: {user.first_name} (ID: {user.id})")
    
    # Спочатку пробуємо MIDA парсер
    print("\n1️⃣ Тестуємо MIDA парсер...")
    receipt_data = mida_receipt_parser.parse_receipt(image_path)
    
    if receipt_data and 'categorized_items' in receipt_data and receipt_data['categorized_items']:
        print("✅ MIDA парсер успішно розпізнав чек!")
        
        # Обробляємо категоризовані товари
        categorized_items = receipt_data['categorized_items']
        user_categories = get_user_categories(user.id)
        print(f"📂 Доступні категорії користувача: {len(user_categories)}")
        
        for category, data in categorized_items.items():
            if isinstance(data, dict) and 'items' in data:
                category_total = data['total_amount']
                item_count = data['item_count']
                
                print(f"\n📦 Категорія: {category}")
                print(f"💰 Сума: {category_total:.2f} грн")
                print(f"🛍️ Товарів: {item_count}")
                
                # Знаходимо відповідну категорію
                category_id = None
                for cat in user_categories:
                    if cat.name.lower() == category.lower():
                        category_id = cat.id
                        break
                
                if not category_id and user_categories:
                    category_id = user_categories[0].id
                    print(f"⚠️ Категорію '{category}' не знайдено, використовуємо '{user_categories[0].name}'")
                
                try:
                    # Додаємо транзакцію
                    transaction = add_transaction(
                        user_id=user.id,
                        amount=category_total,
                        description=f"MIDA - {category} ({item_count} товарів)",
                        category_id=category_id,
                        transaction_type='expense',
                        transaction_date=receipt_data.get('date', datetime.now()),
                        source='mida_receipt_test'
                    )
                    print(f"✅ Транзакцію створено: ID {transaction.id}")
                    
                except Exception as e:
                    print(f"❌ Помилка створення транзакції: {e}")
        
    else:
        # Використовуємо загальний парсер
        print("⚠️ MIDA парсер не впорався, використовуємо загальний...")
        receipt_data = free_receipt_parser.parse_receipt(image_path)
        
        if receipt_data and receipt_data.get('total_amount', 0) > 0:
            print("✅ Загальний парсер розпізнав чек!")
            
            try:
                # Категоризуємо
                category_name = transaction_categorizer.predict_category(
                    receipt_data.get('raw_text', '') or receipt_data.get('store_name', 'Покупка')
                )[0] if hasattr(transaction_categorizer, 'predict_category') else 'groceries'
                
                # Знаходимо категорію
                user_categories = get_user_categories(user.id)
                category_id = None
                for cat in user_categories:
                    if cat.name.lower() == category_name.lower():
                        category_id = cat.id
                        break
                
                if not category_id and user_categories:
                    category_id = user_categories[0].id
                
                # Додаємо транзакцію
                transaction = add_transaction(
                    user_id=user.id,
                    amount=receipt_data['total_amount'],
                    description=f"Покупка в {receipt_data.get('store_name', 'магазині')}",
                    category_id=category_id,
                    transaction_type='expense',
                    transaction_date=receipt_data.get('date', datetime.now()),
                    source='receipt_test'
                )
                print(f"✅ Транзакцію створено: ID {transaction.id}")
                print(f"💰 Сума: {receipt_data['total_amount']:.2f} грн")
                print(f"🏪 Магазин: {receipt_data.get('store_name', 'Невідомо')}")
                
            except Exception as e:
                print(f"❌ Помилка створення транзакції: {e}")
        else:
            print("❌ Не вдалося розпізнати чек")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Використання: python test_receipt_processing.py <шлях_до_фото>")
        sys.exit(1)
    
    test_receipt_processing(sys.argv[1])
