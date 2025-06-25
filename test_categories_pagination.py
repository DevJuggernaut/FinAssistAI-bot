#!/usr/bin/env python3
"""
Скрипт для тестування пагінації категорій
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import Session, User, Category, TransactionType
from database.db_operations import get_or_create_user

def create_test_categories():
    """Створює тестові категорії для перевірки пагінації"""
    
    # Знаходимо або створюємо тестового користувача
    test_telegram_id = 123456789  # Тестовий ID
    user = get_or_create_user(test_telegram_id)
    
    session = Session()
    
    # Видаляємо існуючі тестові категорії (не системні)
    existing_categories = session.query(Category).filter(
        Category.user_id == user.id,
        Category.is_default == False
    ).all()
    
    for cat in existing_categories:
        session.delete(cat)
    
    # Створюємо тестові категорії витрат
    expense_categories = [
        "Продукти харчування",
        "Транспорт і паливо", 
        "Розваги та відпочинок",
        "Одяг та взуття",
        "Комунальні послуги",
        "Медицина та здоров'я",
        "Освіта та книги",
        "Подарунки та благодійність",
        "Домашні товари",
        "Кафе та ресторани",
        "Спорт та фітнес",
        "Краса та догляд",
        "Хобі та захоплення",
        "Технології та гаджети",
        "Подорожі та туризм"
    ]
    
    # Створюємо тестові категорії доходів
    income_categories = [
        "Основна зарплата",
        "Додаткові доходи",
        "Фріланс проекти",
        "Інвестиційні доходи",
        "Дивіденди",
        "Оренда нерухомості",
        "Продаж товарів",
        "Премії та бонуси",
        "Подарунки грошові",
        "Повернення боргів",
        "Cashback та знижки",
        "Виграші та призи"
    ]
    
    # Додаємо категорії витрат
    for i, name in enumerate(expense_categories):
        category = Category(
            user_id=user.id,
            name=name,
            type=TransactionType.EXPENSE.value,  # Використовуємо .value для строкового значення
            icon="💸",
            is_default=False
        )
        session.add(category)
    
    # Додаємо категорії доходів  
    for i, name in enumerate(income_categories):
        category = Category(
            user_id=user.id,
            name=name,
            type=TransactionType.INCOME.value,  # Використовуємо .value для строкового значення
            icon="💰",
            is_default=False
        )
        session.add(category)
    
    session.commit()
    session.close()
    
    print(f"✅ Створено {len(expense_categories)} категорій витрат")
    print(f"✅ Створено {len(income_categories)} категорій доходів")
    print(f"📱 Тестовий користувач: {test_telegram_id}")
    print("\n🔍 Тепер можна перевірити пагінацію в боті!")
    print("   1. Запустіть бота")
    print("   2. Увійдіть як користувач з ID 123456789")
    print("   3. Перейдіть до Налаштування → Категорії")
    print("   4. Перевірте роботу кнопок пагінації та фільтрів")

if __name__ == "__main__":
    create_test_categories()
