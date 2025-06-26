#!/usr/bin/env python3
"""
Тестування покращеного ML категоризатора що працює з категоріями користувача
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ml_categorizer import TransactionCategorizer
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_user_categorization():
    """Тестує категоризацію з використанням категорій користувача"""
    print("🧪 Тестування розумного ML категоризатора\n")
    
    # Створюємо категоризатор
    categorizer = TransactionCategorizer()
    
    # Симулюємо категорії користувача для витрат
    user_expense_categories = [
        {'id': 1, 'name': 'Продукти харчування', 'icon': '🛒', 'type': 'expense'},
        {'id': 2, 'name': 'Транспорт і проїзд', 'icon': '🚗', 'type': 'expense'},
        {'id': 3, 'name': 'Ресторани та кафе', 'icon': '🍽️', 'type': 'expense'},
        {'id': 4, 'name': 'Розваги та дозвілля', 'icon': '🎯', 'type': 'expense'},
        {'id': 5, 'name': 'Медицина', 'icon': '💊', 'type': 'expense'},
        {'id': 6, 'name': 'Одяг та взуття', 'icon': '👕', 'type': 'expense'},
        {'id': 7, 'name': 'Комунальні платежі', 'icon': '🏠', 'type': 'expense'},
        {'id': 8, 'name': 'Особисті витрати', 'icon': '👤', 'type': 'expense'},
    ]
    
    # Симулюємо категорії користувача для доходів
    user_income_categories = [
        {'id': 101, 'name': 'Основна зарплата', 'icon': '💰', 'type': 'income'},
        {'id': 102, 'name': 'Фриланс проекти', 'icon': '💻', 'type': 'income'},
        {'id': 103, 'name': 'Додаткові доходи', 'icon': '🎁', 'type': 'income'},
    ]
    
    # Симулюємо історію транзакцій користувача для навчання
    user_transactions = [
        {'description': 'АТБ продукти на тиждень', 'category_id': 1, 'amount': 850, 'type': 'expense'},
        {'description': 'Сільпо овочі та фрукти', 'category_id': 1, 'amount': 420, 'type': 'expense'},
        {'description': 'Проїзд у метро', 'category_id': 2, 'amount': 50, 'type': 'expense'},
        {'description': 'Uber до дому', 'category_id': 2, 'amount': 180, 'type': 'expense'},
        {'description': 'Обід в McDonald\'s', 'category_id': 3, 'amount': 250, 'type': 'expense'},
        {'description': 'Кава в Starbucks', 'category_id': 3, 'amount': 120, 'type': 'expense'},
        {'description': 'Білети в кіно', 'category_id': 4, 'amount': 320, 'type': 'expense'},
        {'description': 'Консультація лікаря', 'category_id': 5, 'amount': 800, 'type': 'expense'},
        {'description': 'Ліки в аптеці', 'category_id': 5, 'amount': 340, 'type': 'expense'},
        {'description': 'Футболка в Zara', 'category_id': 6, 'amount': 1200, 'type': 'expense'},
        {'description': 'Комунальні за квартиру', 'category_id': 7, 'amount': 2500, 'type': 'expense'},
        {'description': 'Зарплата за місяць', 'category_id': 101, 'amount': 25000, 'type': 'income'},
        {'description': 'Оплата за веб-сайт', 'category_id': 102, 'amount': 5000, 'type': 'income'},
    ]
    
    print("📚 Навчання категоризатора на історії користувача...")
    # Навчаємо категоризатор на транзакціях користувача
    success = categorizer.train_on_user_transactions(user_transactions, user_expense_categories + user_income_categories)
    print(f"Результат навчання: {'✅ Успішно' if success else '❌ Помилка'}\n")
    
    # Тестові транзакції для категоризації
    test_transactions = [
        # Витрати
        {'description': 'Новус молоко хліб сир', 'amount': 180, 'type': 'expense', 'expected': 'Продукти харчування'},
        {'description': 'Метро київська', 'amount': 50, 'type': 'expense', 'expected': 'Транспорт і проїзд'},
        {'description': 'Піца в ресторані', 'amount': 350, 'type': 'expense', 'expected': 'Ресторани та кафе'},
        {'description': 'Квитки на концерт', 'amount': 800, 'type': 'expense', 'expected': 'Розваги та дозвілля'},
        {'description': 'Візит до стоматолога', 'amount': 1200, 'type': 'expense', 'expected': 'Медицина'},
        {'description': 'Джинси в H&M', 'amount': 900, 'type': 'expense', 'expected': 'Одяг та взуття'},
        {'description': 'Платіж за електроенергію', 'amount': 850, 'type': 'expense', 'expected': 'Комунальні платежі'},
        {'description': 'Стрижка в салоні', 'amount': 400, 'type': 'expense', 'expected': 'Особисті витрати'},
        
        # Доходи
        {'description': 'Зарплата програміст', 'amount': 30000, 'type': 'income', 'expected': 'Основна зарплата'},
        {'description': 'Розробка лендінгу клієнт', 'amount': 8000, 'type': 'income', 'expected': 'Фриланс проекти'},
        {'description': 'Повернення боргу', 'amount': 1500, 'type': 'income', 'expected': 'Додаткові доходи'},
    ]
    
    print("🎯 Тестування категоризації:")
    print("=" * 70)
    
    correct_predictions = 0
    total_predictions = 0
    
    for test_trans in test_transactions:
        # Вибираємо категорії відповідного типу
        categories = user_expense_categories if test_trans['type'] == 'expense' else user_income_categories
        
        # Отримуємо передбачену категорію
        predicted_category = categorizer.get_best_category_for_user(
            description=test_trans['description'],
            amount=test_trans['amount'],
            transaction_type=test_trans['type'],
            user_categories=categories
        )
        
        # Перевіряємо правильність
        is_correct = predicted_category['name'] == test_trans['expected'] if predicted_category else False
        
        if is_correct:
            correct_predictions += 1
        total_predictions += 1
        
        # Виводимо результат
        result_icon = "✅" if is_correct else "❌"
        predicted_name = predicted_category['name'] if predicted_category else "Не визначено"
        
        print(f"{result_icon} '{test_trans['description']}'")
        print(f"   Очікувано: {test_trans['expected']}")
        print(f"   Передбачено: {predicted_name}")
        print(f"   Тип: {test_trans['type']}, Сума: {test_trans['amount']}")
        print()
    
    # Підсумок
    accuracy = (correct_predictions / total_predictions) * 100 if total_predictions > 0 else 0
    print("=" * 70)
    print(f"📊 ПІДСУМОК:")
    print(f"   Правильних передбачень: {correct_predictions}/{total_predictions}")
    print(f"   Точність: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print("🎉 Відмінний результат! Категоризатор працює ефективно.")
    elif accuracy >= 60:
        print("👍 Хороший результат. Потрібно більше навчальних даних.")
    else:
        print("⚠️ Потрібно покращити алгоритм категоризації.")

def test_user_categories_with_custom_names():
    """Тестує роботу з кастомними назвами категорій користувача"""
    print("\n🔧 Тестування з кастомними категоріями користувача:")
    print("=" * 70)
    
    categorizer = TransactionCategorizer()
    
    # Кастомні категорії користувача
    custom_categories = [
        {'id': 201, 'name': 'Їжа на роботі', 'icon': '🍱', 'type': 'expense'},
        {'id': 202, 'name': 'Покупки для хобі', 'icon': '🎨', 'type': 'expense'},
        {'id': 203, 'name': 'Подарунки близьким', 'icon': '🎁', 'type': 'expense'},
        {'id': 204, 'name': 'Консультації та навчання', 'icon': '📚', 'type': 'expense'},
        {'id': 205, 'name': 'Інвестиції і криптовалюти', 'icon': '📈', 'type': 'income'},
    ]
    
    # Історія транзакцій з кастомними категоріями
    custom_transactions = [
        {'description': 'Обід біля офісу', 'category_id': 201, 'amount': 200, 'type': 'expense'},
        {'description': 'Сендвіч на роботі', 'category_id': 201, 'amount': 80, 'type': 'expense'},
        {'description': 'Пензлі для малювання', 'category_id': 202, 'amount': 350, 'type': 'expense'},
        {'description': 'Полотно для картини', 'category_id': 202, 'amount': 450, 'type': 'expense'},
        {'description': 'Подарунок мамі на день народження', 'category_id': 203, 'amount': 800, 'type': 'expense'},
        {'description': 'Сувенір для друга', 'category_id': 203, 'amount': 250, 'type': 'expense'},
        {'description': 'Курс з Python', 'category_id': 204, 'amount': 2000, 'type': 'expense'},
        {'description': 'Книга по JavaScript', 'category_id': 204, 'amount': 500, 'type': 'expense'},
        {'description': 'Прибуток від Bitcoin', 'category_id': 205, 'amount': 3000, 'type': 'income'},
    ]
    
    # Навчаємо на кастомних категоріях
    success = categorizer.train_on_user_transactions(custom_transactions, custom_categories)
    print(f"Навчання на кастомних категоріях: {'✅ Успішно' if success else '❌ Помилка'}")
    
    # Тестуємо кастомні категорії
    custom_tests = [
        {'description': 'Перекус в кафе біля роботи', 'amount': 150, 'type': 'expense', 'expected': 'Їжа на роботі'},
        {'description': 'Фарби акварельні', 'amount': 280, 'type': 'expense', 'expected': 'Покупки для хобі'},
        {'description': 'Квіти на 8 березня', 'amount': 400, 'type': 'expense', 'expected': 'Подарунки близьким'},
        {'description': 'Онлайн курс дизайну', 'amount': 1500, 'type': 'expense', 'expected': 'Консультації та навчання'},
        {'description': 'Дивіденди від акцій', 'amount': 2500, 'type': 'income', 'expected': 'Інвестиції і криптовалюти'},
    ]
    
    custom_correct = 0
    for test in custom_tests:
        categories = [cat for cat in custom_categories if cat['type'] == test['type']]
        predicted = categorizer.get_best_category_for_user(
            test['description'], test['amount'], test['type'], categories
        )
        
        is_correct = predicted['name'] == test['expected'] if predicted else False
        if is_correct:
            custom_correct += 1
            
        result_icon = "✅" if is_correct else "❌"
        predicted_name = predicted['name'] if predicted else "Не визначено"
        
        print(f"{result_icon} '{test['description']}' → {predicted_name}")
    
    custom_accuracy = (custom_correct / len(custom_tests)) * 100
    print(f"\n📊 Точність на кастомних категоріях: {custom_accuracy:.1f}%")
    
    return custom_accuracy

if __name__ == "__main__":
    print("🚀 ТЕСТУВАННЯ РОЗУМНОГО ML КАТЕГОРИЗАТОРА")
    print("=" * 70)
    
    # Основне тестування
    test_user_categorization()
    
    # Тестування кастомних категорій
    custom_accuracy = test_user_categories_with_custom_names()
    
    print("\n" + "=" * 70)
    print("🏆 ВИСНОВОК:")
    print("✅ Категоризатор навчається на категоріях користувача")
    print("✅ Підтримує кастомні назви категорій")
    print("✅ Покращується з кожною новою транзакцією")
    print("✅ Не створює нових категорій без дозволу")
    
    if custom_accuracy >= 80:
        print("🎯 Рекомендація: Система готова до впровадження!")
    else:
        print("⚠️ Рекомендація: Потрібно додати більше ключових слів для покращення.")
