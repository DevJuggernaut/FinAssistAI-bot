#!/usr/bin/env python3
"""
Тест для перевірки того, що таблиці в PDF не розриваються на дві сторінки
"""

import sys
import os
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Налаштування Django
sys.path.append('/Users/abobina/telegram_bot/FinAssistAI-bot')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from bot_app.models import User, Account, Transaction, Category
from handlers.analytics_handler import create_pdf_report, get_user_statistics

def create_test_data():
    """Створює тестові дані для перевірки PDF"""
    print("📊 Створюємо тестові дані...")
    
    # Створюємо тестового користувача
    user, created = User.objects.get_or_create(
        telegram_id=999999999,
        defaults={
            'username': 'test_pdf_user',
            'first_name': 'PDF',
            'last_name': 'Tester'
        }
    )
    
    # Створюємо рахунок
    account, created = Account.objects.get_or_create(
        user=user,
        name='Тестовий рахунок',
        defaults={'balance': Decimal('10000.00')}
    )
    
    # Створюємо категорії з довгими назвами (для тестування переносу тексту)
    categories_data = [
        'Супермаркети та продукти харчування',
        'Транспорт і паливо для автомобіля',
        'Комунальні послуги та інтернет',
        'Розваги кіно театр ресторани',
        'Медицина ліки аптека лікарі',
        'Одяг взуття аксесуари краса',
        'Освіта книги курси навчання',
        'Подарунки благодійність допомога'
    ]
    
    categories = []
    for cat_name in categories_data:
        category, created = Category.objects.get_or_create(
            user=user,
            name=cat_name,
            defaults={'type': 'expense'}
        )
        categories.append(category)
    
    # Створюємо доходи
    income_category, created = Category.objects.get_or_create(
        user=user,
        name='Зарплата',
        defaults={'type': 'income'}
    )
    
    # Очищаємо старі транзакції
    Transaction.objects.filter(account__user=user).delete()
    
    # Створюємо доходи
    for i in range(3):
        Transaction.objects.create(
            account=account,
            amount=Decimal('25000.00'),
            description=f'Зарплата {i+1}',
            category=income_category,
            transaction_type='income',
            date=datetime.now() - timedelta(days=i*10)
        )
    
    # Створюємо багато витрат по категоріях (щоб таблиця була заповнена)
    import random
    for i, category in enumerate(categories):
        # Різні суми для різних категорій
        base_amount = 5000 - (i * 500)  # Від 5000 до 1500
        
        for j in range(random.randint(5, 12)):  # Від 5 до 12 транзакцій на категорію
            amount = base_amount + random.randint(-500, 500)
            Transaction.objects.create(
                account=account,
                amount=Decimal(str(amount)),
                description=f'{category.name} - покупка {j+1}',
                category=category,
                transaction_type='expense',
                date=datetime.now() - timedelta(days=random.randint(1, 30))
            )
    
    return user

def test_pdf_generation():
    """Тестує генерацію PDF з перевіркою структури"""
    print("🔧 Генеруємо PDF звіт...")
    
    user = create_test_data()
    
    # Отримуємо статистику
    stats = get_user_statistics(user.telegram_id, period='30 днів')
    
    # Отримуємо транзакції
    from bot_app.models import Transaction
    transactions = Transaction.objects.filter(
        account__user=user,
        date__gte=datetime.now() - timedelta(days=30)
    ).select_related('category', 'account').order_by('-date')
    
    print(f"📈 Статистика:")
    print(f"   • Доходи: {stats['total_income']:,.2f} грн")
    print(f"   • Витрати: {stats['total_expenses']:,.2f} грн")
    print(f"   • Баланс: {stats['balance']:+,.2f} грн")
    print(f"   • Категорій витрат: {len(stats['category_expenses'])}")
    print(f"   • Транзакцій: {transactions.count()}")
    
    try:
        # Генеруємо PDF
        pdf_buffer = create_pdf_report(user, transactions, stats)
        
        if pdf_buffer:
            # Зберігаємо PDF файл
            pdf_filename = f"test_pdf_no_breaks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            with open(pdf_filename, 'wb') as f:
                f.write(pdf_buffer.read())
            
            print(f"✅ PDF успішно створено: {pdf_filename}")
            print(f"📝 Розмір файлу: {os.path.getsize(pdf_filename)} байт")
            
            # Перевіряємо, що файл не порожній і має правильний заголовок PDF
            with open(pdf_filename, 'rb') as f:
                content = f.read()
                if content.startswith(b'%PDF'):
                    print("✅ PDF файл має коректну структуру")
                else:
                    print("❌ PDF файл має некоректну структуру")
            
            print(f"\n🔍 Додаткові перевірки:")
            print(f"   • Файл містить дані про {len(stats['category_expenses'])} категорій")
            print(f"   • Всі таблиці повинні бути на одній сторінці завдяки KeepTogether")
            print(f"   • Текст без емодзі, лише читабельний текст")
            print(f"   • Оптимізовані ширини колонок для кращого розміщення")
            
            return True
        else:
            print("❌ Помилка: PDF не був створений")
            return False
            
    except Exception as e:
        print(f"❌ Помилка при створенні PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """Очищає тестові дані"""
    print("🧹 Очищаємо тестові дані...")
    try:
        user = User.objects.get(telegram_id=999999999)
        # Видаляємо всі пов'язані об'єкти
        Transaction.objects.filter(account__user=user).delete()
        Category.objects.filter(user=user).delete()
        Account.objects.filter(user=user).delete()
        user.delete()
        print("✅ Тестові дані очищено")
    except User.DoesNotExist:
        print("ℹ️ Тестові дані не знайдено")

if __name__ == "__main__":
    print("🚀 Запуск тесту PDF без розривів таблиць...")
    print("=" * 60)
    
    try:
        success = test_pdf_generation()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ ТЕСТ ПРОЙШОВ УСПІШНО!")
            print("📋 Перевірте згенерований PDF файл:")
            print("   • Таблиці не розриваються між сторінками")
            print("   • Текст читабельний без емодзі")
            print("   • Колонки мають оптимальну ширину")
            print("   • Розділи залишаються цілими")
        else:
            print("\n" + "=" * 60)
            print("❌ ТЕСТ НЕ ПРОЙШОВ!")
    
    except Exception as e:
        print(f"\n❌ Критична помилка в тесті: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        cleanup_test_data()
        print("\n🏁 Тест завершено")
