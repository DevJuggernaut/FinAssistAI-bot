#!/usr/bin/env python3
"""
Тест для перевірки покращеного PDF звіту з підтримкою кирилиці через локальні шрифти DejaVu Sans
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Додаємо батьківську папку до sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import init_database
from models import User, Transaction, TransactionType, Category
from handlers.analytics_handler import create_pdf_report

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cyrillic_pdf_support():
    """Тестує підтримку кирилиці в PDF через локальні шрифти"""
    print("🧪 Тестування PDF з підтримкою кирилиці...")
    
    # Ініціалізуємо базу
    init_database()
    
    # Створюємо тестового користувача
    test_user = User(
        telegram_id=999999999,
        username="test_cyrillic_user",
        language_code="uk"
    )
    
    # Створюємо тестові транзакції з українським текстом
    now = datetime.now()
    test_transactions = [
        Transaction(
            user_id=test_user.id,
            amount=1500.50,
            type=TransactionType.EXPENSE,
            category="🛒 Продукти харчування",
            description="Покупки в АТБ: хліб, молоко, м'ясо",
            date=now - timedelta(days=1)
        ),
        Transaction(
            user_id=test_user.id,
            amount=850.75,
            type=TransactionType.EXPENSE,
            category="🚗 Транспорт",
            description="Проїзд в маршрутці та метро",
            date=now - timedelta(days=2)
        ),
        Transaction(
            user_id=test_user.id,
            amount=2300.00,
            type=TransactionType.EXPENSE,
            category="🏠 Комунальні послуги",
            description="Сплата за електроенергію та воду",
            date=now - timedelta(days=3)
        ),
        Transaction(
            user_id=test_user.id,
            amount=25000.00,
            type=TransactionType.INCOME,
            category="💼 Зарплата",
            description="Заробітна плата за січень",
            date=now - timedelta(days=5)
        ),
        Transaction(
            user_id=test_user.id,
            amount=420.30,
            type=TransactionType.EXPENSE,
            category="🎬 Розваги",
            description="Кінотеатр: білети та попкорн",
            date=now - timedelta(days=7)
        )
    ]
    
    # Створюємо статистику
    total_income = sum(t.amount for t in test_transactions if t.type == TransactionType.INCOME)
    total_expenses = sum(t.amount for t in test_transactions if t.type == TransactionType.EXPENSE)
    
    category_expenses = {}
    for t in test_transactions:
        if t.type == TransactionType.EXPENSE:
            category_expenses[t.category] = category_expenses.get(t.category, 0) + t.amount
    
    stats = {
        'period': "30 днів",
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': total_income - total_expenses,
        'category_expenses': category_expenses,
        'transaction_count': len(test_transactions)
    }
    
    print(f"📊 Статистика для тесту:")
    print(f"   💰 Доходи: {total_income:,.2f} грн")
    print(f"   💸 Витрати: {total_expenses:,.2f} грн")
    print(f"   📈 Баланс: {stats['balance']:+,.2f} грн")
    print(f"   📦 Транзакцій: {len(test_transactions)}")
    print(f"   🏷️ Категорій: {len(category_expenses)}")
    
    # Тестуємо створення PDF
    try:
        print("\n🔧 Створення PDF з кирилицею...")
        pdf_buffer = create_pdf_report(test_user, test_transactions, stats)
        
        if pdf_buffer:
            # Зберігаємо PDF файл для перевірки
            test_filename = f"test_cyrillic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            with open(test_filename, 'wb') as f:
                f.write(pdf_buffer.getvalue())
            
            print(f"✅ PDF успішно створено: {test_filename}")
            print(f"📄 Розмір файлу: {len(pdf_buffer.getvalue())} байт")
            
            # Перевірка: чи містить PDF правильні метадані
            pdf_content = pdf_buffer.getvalue()
            
            # Базова перевірка вмісту
            checks = {
                "DejaVu font registration": b"DejaVu" in pdf_content,
                "Ukrainian currency symbol": "грн".encode('utf-8') in pdf_content,
                "Ukrainian text": "Персональний".encode('utf-8') in pdf_content,
                "Categories in Ukrainian": "Продукти".encode('utf-8') in pdf_content,
                "PDF header": pdf_content.startswith(b'%PDF-'),
                "PDF size > 10KB": len(pdf_content) > 10240
            }
            
            print(f"\n🔍 Перевірки PDF:")
            all_passed = True
            for check_name, result in checks.items():
                status = "✅" if result else "❌"
                print(f"   {status} {check_name}: {result}")
                if not result:
                    all_passed = False
            
            if all_passed:
                print(f"\n🎉 Всі перевірки пройшли успішно!")
                print(f"📱 Кирилиця має коректно відображатися в PDF!")
                print(f"🔤 Використовується шрифт DejaVu Sans з локальної папки fonts/")
                return True
            else:
                print(f"\n⚠️ Деякі перевірки не пройшли. Перевірте PDF вручну.")
                return False
                
        else:
            print("❌ Помилка: PDF не було створено")
            return False
            
    except Exception as e:
        print(f"❌ Помилка при створенні PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_font_files():
    """Перевіряє наявність файлів шрифтів"""
    print("🔤 Перевірка файлів шрифтів...")
    
    font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')
    
    required_fonts = [
        'DejaVuSans.ttf',
        'DejaVuSans-Bold.ttf'
    ]
    
    all_found = True
    for font_file in required_fonts:
        font_path = os.path.join(font_dir, font_file)
        if os.path.exists(font_path):
            size = os.path.getsize(font_path)
            print(f"   ✅ {font_file}: {size:,} байт")
        else:
            print(f"   ❌ {font_file}: НЕ ЗНАЙДЕНО")
            all_found = False
    
    if all_found:
        print("✅ Всі необхідні шрифти знайдено!")
    else:
        print("❌ Деякі шрифти відсутні. Завантажте їх командою:")
        print("   curl -L -o fonts/DejaVuSans.ttf 'https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf'")
        print("   curl -L -o fonts/DejaVuSans-Bold.ttf 'https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf'")
    
    return all_found

if __name__ == "__main__":
    print("🚀 Запуск тестування PDF з підтримкою кирилиці\n")
    
    # Спочатку перевіряємо шрифти
    fonts_ok = check_font_files()
    
    if fonts_ok:
        # Якщо шрифти є, тестуємо PDF
        success = test_cyrillic_pdf_support()
        
        if success:
            print("\n🎯 РЕЗУЛЬТАТ: Тест пройшов успішно!")
            print("💡 Рекомендація: Відкрийте згенерований PDF і перевірте відображення української мови")
        else:
            print("\n🚨 РЕЗУЛЬТАТ: Тест не пройшов!")
    else:
        print("\n🚨 РЕЗУЛЬТАТ: Спочатку завантажте необхідні шрифти!")
