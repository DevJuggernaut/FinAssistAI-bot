#!/usr/bin/env python3
"""
Тест оновленої кругової діаграми доходів з вкладки "Огляд фінансів"
Перевіряємо функцію generate_income_pie_chart з services/report_generator.py
"""

import os
import sys
import matplotlib
matplotlib.use('Agg')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.report_generator import FinancialReport
from database.models import Session, Transaction, Category, User, TransactionType
from datetime import datetime
import random

def create_income_test_data():
    """Створюємо тестові дані для діаграми доходів"""
    session = Session()
    
    try:
        # Знаходимо або створюємо тестового користувача
        user = session.query(User).filter(User.telegram_id == 999999998).first()
        if not user:
            user = User(
                telegram_id=999999998,
                username="test_income_user",
                first_name="Income",
                last_name="Test"
            )
            session.add(user)
            session.flush()
        
        print(f"✅ Користувач створений/знайдений: ID={user.id}")
        
        # Створюємо тестові категорії доходів
        income_categories = [
            ("Зарплата", "💰"),
            ("Фріланс", "💻"),
            ("Інвестиції", "📈"),
            ("Подарунки", "🎁"),
            ("Інше", "💵")
        ]
        
        categories = []
        for name, icon in income_categories:
            existing_cat = session.query(Category).filter(
                Category.name == name,
                Category.user_id == user.id,
                Category.type == 'income'
            ).first()
            
            if not existing_cat:
                category = Category(
                    name=name,
                    icon=icon,
                    type='income',
                    user_id=user.id
                )
                session.add(category)
                session.flush()
                categories.append(category)
            else:
                categories.append(existing_cat)
        
        print(f"✅ Створено/знайдено {len(categories)} категорій доходів")
        
        # Очищуємо старі тестові транзакції
        session.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.description.like('ТЕСТ ДОХІД:%')
        ).delete()
        
        # Створюємо тестові доходи з різними сумами
        income_amounts = [25000, 5000, 2000, 1000, 500]
        
        for i, category in enumerate(categories):
            amount = income_amounts[i] if i < len(income_amounts) else random.randint(500, 3000)
            
            transaction = Transaction(
                user_id=user.id,
                category_id=category.id,
                amount=amount,
                description=f"ТЕСТ ДОХІД: {category.name}",
                type=TransactionType.INCOME,
                transaction_date=datetime.now()
            )
            session.add(transaction)
        
        session.commit()
        print(f"✅ Створено {len(categories)} тестових транзакцій доходів")
        
        return user.id
        
    except Exception as e:
        session.rollback()
        print(f"❌ Помилка створення тестових даних: {e}")
        return None
    finally:
        session.close()

def test_income_pie_chart():
    """Тестуємо оновлену діаграму доходів"""
    print("🔧 Тестування оновленої діаграми доходів з огляду фінансів...")
    
    # Створюємо тестові дані
    user_id = create_income_test_data()
    if not user_id:
        print("❌ Не вдалося створити тестові дані")
        return
    
    try:
        # Створюємо FinancialReport і генеруємо діаграму
        financial_report = FinancialReport(user_id)
        
        print("💰 Генеруємо кругову діаграму доходів (функція з services/report_generator.py)...")
        
        # Генеруємо діаграму (як у show_income_pie_chart)
        chart_buffer, error = financial_report.generate_income_pie_chart()
        
        if error:
            print(f"❌ Помилка генерації діаграми: {error}")
            return
        
        if not chart_buffer:
            print("❌ Діаграма не була згенерована")
            return
        
        # Зберігаємо діаграму
        output_path = "test_budget_overview_income_pie_chart.png"
        with open(output_path, 'wb') as f:
            f.write(chart_buffer.getvalue())
        
        print(f"✅ Діаграма доходів успішно збережена: {output_path}")
        print("🎯 Перевірте файл - діаграма повинна мати:")
        print("   • Пончикову форму (з отвором в центрі)")
        print("   • Великий текст загальної суми в центрі")
        print("   • Зелену кольорову палітру для доходів")
        print("   • Великі шрифти для всіх елементів")
        print("   • Легенду збоку з відсотками та сумами")
        print("   • Високу роздільну здатність (300 DPI)")
        
        # Перевіряємо розмір файлу
        file_size = os.path.getsize(output_path)
        print(f"📏 Розмір файлу: {file_size} байт")
        
        if file_size > 50000:
            print("✅ Діаграма має високу якість (великий розмір файлу)")
        else:
            print("⚠️ Діаграма може мати низьку якість (малий розмір файлу)")
            
    except Exception as e:
        print(f"❌ Помилка тестування: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_income_pie_chart()
