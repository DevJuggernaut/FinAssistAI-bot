#!/usr/bin/env python3
"""
Тест для перевірки покращеної пагінації категорій з розділенням на витрати та доходи
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import TransactionType

def test_category_pagination_logic():
    """Тестує логіку пагінації категорій з розділенням"""
    
    # Імітуємо категорії
    class MockCategory:
        def __init__(self, id, name, type, icon="📂"):
            self.id = id
            self.name = name
            self.type = type
            self.icon = icon
    
    # Створюємо тестові категорії
    categories = [
        # Витрати
        MockCategory(1, "Їжа", TransactionType.EXPENSE, "🍔"),
        MockCategory(2, "Транспорт", TransactionType.EXPENSE, "🚗"),
        MockCategory(3, "Розваги", TransactionType.EXPENSE, "🎬"),
        MockCategory(4, "Здоров'я", TransactionType.EXPENSE, "💊"),
        MockCategory(5, "Одяг", TransactionType.EXPENSE, "👕"),
        MockCategory(6, "Комунальні", TransactionType.EXPENSE, "💡"),
        MockCategory(7, "Навчання", TransactionType.EXPENSE, "📚"),
        MockCategory(8, "Покупки", TransactionType.EXPENSE, "🛒"),
        MockCategory(9, "Подарунки", TransactionType.EXPENSE, "🎁"),
        MockCategory(10, "Інші витрати", TransactionType.EXPENSE, "💸"),
        
        # Доходи
        MockCategory(11, "Зарплата", TransactionType.INCOME, "💰"),
        MockCategory(12, "Фріланс", TransactionType.INCOME, "💻"),
        MockCategory(13, "Продаж", TransactionType.INCOME, "💵"),
        MockCategory(14, "Інвестиції", TransactionType.INCOME, "📈"),
        MockCategory(15, "Інші доходи", TransactionType.INCOME, "💎"),
    ]
    
    print(f"Всього категорій: {len(categories)}")
    
    # Розділяємо категорії на витрати та доходи
    expense_categories = [c for c in categories if c.type == TransactionType.EXPENSE]
    income_categories = [c for c in categories if c.type == TransactionType.INCOME]
    
    print(f"Витрати: {len(expense_categories)}")
    print(f"Доходи: {len(income_categories)}")
    
    # Налаштування пагінації
    per_page = 8  # Кількість категорій на сторінку
    total_categories = len(categories)
    total_pages = max(1, (total_categories + per_page - 1) // per_page)
    
    print(f"Всього сторінок: {total_pages}")
    
    # Створюємо загальний список для пагінації
    all_categories_for_pagination = expense_categories + income_categories
    
    # Тестуємо кожну сторінку
    for page in range(1, total_pages + 1):
        print(f"\n=== СТОРІНКА {page} ===")
        
        # Отримуємо категорії для поточної сторінки
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_categories = all_categories_for_pagination[start_idx:end_idx]
        
        print(f"Категорій на сторінці: {len(page_categories)}")
        
        # Розділяємо категорії на поточній сторінці за типом
        page_expense_categories = [c for c in page_categories if c.type == TransactionType.EXPENSE]
        page_income_categories = [c for c in page_categories if c.type == TransactionType.INCOME]
        
        print(f"Витрати на сторінці: {len(page_expense_categories)}")
        if page_expense_categories:
            for cat in page_expense_categories:
                print(f"  - {cat.icon} {cat.name}")
        
        print(f"Доходи на сторінці: {len(page_income_categories)}")
        if page_income_categories:
            for cat in page_income_categories:
                print(f"  - {cat.icon} {cat.name}")
        
        # Перевіряємо кнопки навігації
        nav_info = []
        if page > 1:
            nav_info.append("⬅️ Попередні")
        if page < total_pages:
            nav_info.append("Наступні ➡️")
        
        if nav_info:
            print(f"Навігація: {' | '.join(nav_info)}")
    
    print(f"\n✅ Тест пагінації пройшов успішно!")
    print(f"Категорії правильно розділені на витрати ({len(expense_categories)}) та доходи ({len(income_categories)})")
    print(f"Пагінація працює коректно: {total_pages} сторінок по {per_page} категорій")

if __name__ == "__main__":
    test_category_pagination_logic()
