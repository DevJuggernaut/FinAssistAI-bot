#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки роботи фільтрів транзакцій
"""

def test_filter_logic():
    """Тестуємо логіку фільтрів"""
    print("🧪 Тестування логіки фільтрів...")
    
    # Симулюємо контекст користувача
    context_user_data = {}
    
    # Тест 1: Ініціалізація фільтрів
    if 'transaction_filters' not in context_user_data:
        context_user_data['transaction_filters'] = {
            'period': 'month',
            'type': 'all',
            'category': 'all'
        }
    
    if 'transactions_view' not in context_user_data:
        context_user_data['transactions_view'] = {
            'page': 1,
            'per_page': 5,
            'category_id': None,
            'type': None,
            'period': 'month'
        }
    
    print("✅ Ініціалізація фільтрів - OK")
    
    # Тест 2: Синхронізація фільтрів
    filters = context_user_data['transaction_filters']
    view_params = context_user_data['transactions_view']
    
    # Оновлюємо параметри перегляду на основі фільтрів
    view_params['period'] = filters.get('period', 'month')
    view_params['type'] = filters.get('type', 'all') if filters.get('type', 'all') != 'all' else None
    view_params['category_id'] = filters.get('category', 'all') if filters.get('category', 'all') != 'all' else None
    
    assert view_params['period'] == 'month'
    assert view_params['type'] is None
    assert view_params['category_id'] is None
    print("✅ Синхронізація фільтрів - OK")
    
    # Тест 3: Зміна фільтрів
    filters['type'] = 'income'
    filters['category'] = 123  # ID категорії
    filters['period'] = 'week'
    
    # Синхронізація після зміни
    view_params['period'] = filters.get('period', 'month')
    view_params['type'] = filters.get('type', 'all') if filters.get('type', 'all') != 'all' else None
    view_params['category_id'] = filters.get('category', 'all') if filters.get('category', 'all') != 'all' else None
    
    assert view_params['period'] == 'week'
    assert view_params['type'] == 'income'
    assert view_params['category_id'] == 123
    print("✅ Зміна фільтрів - OK")
    
    # Тест 4: Скидання фільтрів
    filters['period'] = 'month'
    filters['type'] = 'all'
    filters['category'] = 'all'
    
    view_params['period'] = filters.get('period', 'month')
    view_params['type'] = filters.get('type', 'all') if filters.get('type', 'all') != 'all' else None
    view_params['category_id'] = filters.get('category', 'all') if filters.get('category', 'all') != 'all' else None
    view_params['page'] = 1
    
    assert view_params['period'] == 'month'
    assert view_params['type'] is None
    assert view_params['category_id'] is None
    assert view_params['page'] == 1
    print("✅ Скидання фільтрів - OK")
    
    print("\n🎉 Всі тести пройшли успішно!")
    print(f"📊 Результуючий стан фільтрів: {filters}")
    print(f"📋 Результуючий стан view_params: {view_params}")

if __name__ == "__main__":
    test_filter_logic()
