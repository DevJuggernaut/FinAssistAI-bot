#!/usr/bin/env python3
"""
Тест оновленої кругової діаграми з вкладки "Огляд фінансів"
Перевіряємо функцію generate_expense_pie_chart з services/report_generator.py
"""

import os
import sys
import matplotlib
matplotlib.use('Agg')  # Встановлюємо backend перед імпортом pyplot

# Додаємо шлях до кореневої директорії
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.report_generator import FinancialReport
from database.models import Session, Transaction, Category, User, TransactionType
from datetime import datetime
import random

def create_test_data():
    """Створюємо тестові дані для діаграми"""
    session = Session()
    
    try:
        # Створюємо тестового користувача
        test_user = User(
            telegram_id=999999999,
            username="test_budget_user",
            first_name="Test",
            last_name="User"
        )
        
        # Перевіряємо, чи користувач уже існує
        existing_user = session.query(User).filter(User.telegram_id == 999999999).first()
        if existing_user:
            user = existing_user
        else:
            session.add(test_user)
            session.flush()
            user = test_user
        
        print(f"✅ Користувач створений/знайдений: ID={user.id}")
        
        # Створюємо тестові категорії витрат
        expense_categories = [
            ("Продукти", "🛒"),
            ("Транспорт", "🚗"),
            ("Комунальні послуги", "🏠"),
            ("Розваги", "🎬"),
            ("Одяг", "👕"),
            ("Ресторани", "🍽️"),
            ("Здоров'я", "🏥"),
            ("Освіта", "📚")
        ]
        
        categories = []
        for name, icon in expense_categories:
            existing_cat = session.query(Category).filter(
                Category.name == name,
                Category.user_id == user.id
            ).first()
            
            if not existing_cat:
                category = Category(
                    name=name,
                    icon=icon,
                    type='expense',  # Додаємо тип категорії
                    user_id=user.id
                )
                session.add(category)
                session.flush()
                categories.append(category)
            else:
                categories.append(existing_cat)
        
        print(f"✅ Створено/знайдено {len(categories)} категорій")
        
        # Очищуємо старі тестові транзакції
        session.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.description.like('ТЕСТ:%')
        ).delete()
        
        # Створюємо тестові витрати з різними сумами
        expense_amounts = [1500, 800, 2200, 450, 300, 680, 1200, 200]
        
        for i, category in enumerate(categories):
            amount = expense_amounts[i] if i < len(expense_amounts) else random.randint(200, 1000)
            
            transaction = Transaction(
                user_id=user.id,
                category_id=category.id,
                amount=amount,
                description=f"ТЕСТ: {category.name}",
                type=TransactionType.EXPENSE,
                transaction_date=datetime.now()
            )
            session.add(transaction)
        
        session.commit()
        print(f"✅ Створено {len(categories)} тестових транзакцій")
        
        return user.id
        
    except Exception as e:
        session.rollback()
        print(f"❌ Помилка створення тестових даних: {e}")
        return None
    finally:
        session.close()

def test_budget_overview_pie_chart():
    """Тестуємо оновлену діаграму з вкладки огляду фінансів"""
    print("🔧 Тестування оновленої діаграми витрат з огляду фінансів...")
    
    # Створюємо тестові дані
    user_id = create_test_data()
    if not user_id:
        print("❌ Не вдалося створити тестові дані")
        return
    
    try:
        # Створюємо FinancialReport і генеруємо діаграму
        financial_report = FinancialReport(user_id)
        
        print("📊 Генеруємо кругову діаграму витрат (функція з services/report_generator.py)...")
        
        # Генеруємо діаграму (як у show_expense_pie_chart)
        chart_buffer, error = financial_report.generate_expense_pie_chart()
        
        if error:
            print(f"❌ Помилка генерації діаграми: {error}")
            return
        
        if not chart_buffer:
            print("❌ Діаграма не була згенерована")
            return
        
        # Зберігаємо діаграму
        output_path = "test_budget_overview_modern_pie_chart.png"
        with open(output_path, 'wb') as f:
            f.write(chart_buffer.getvalue())
        
        print(f"✅ Діаграма успішно збережена: {output_path}")
        print("🎯 Перевірте файл - діаграма повинна мати:")
        print("   • Пончикову форму (з отвором в центрі)")
        print("   • Великий текст загальної суми в центрі")
        print("   • Сучасні кольори та великі шрифти")
        print("   • Легенду збоку з відсотками та сумами")
        print("   • Відсутність підписів прямо на діаграмі")
        print("   • Високу роздільну здатність (300 DPI)")
        
        # Перевіряємо розмір файлу
        file_size = os.path.getsize(output_path)
        print(f"📏 Розмір файлу: {file_size} байт")
        
        if file_size > 50000:  # Більше 50KB означає високу якість
            print("✅ Діаграма має високу якість (великий розмір файлу)")
        else:
            print("⚠️ Діаграма може мати низьку якість (малий розмір файлу)")
            
    except Exception as e:
        print(f"❌ Помилка тестування: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_budget_overview_pie_chart()
