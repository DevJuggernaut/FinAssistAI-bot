#!/usr/bin/env python3
"""
Діагностичний скрипт для перевірки категорій користувача
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_user_categories(telegram_id=None):
    """Діагностика категорій користувача"""
    
    print("🔍 Діагностика категорій користувача\n")
    
    # Якщо telegram_id не вказано, використовуємо тестовий
    if telegram_id is None:
        print("ℹ️ Використовуємо тестовий telegram_id. Для реального користувача передайте telegram_id як аргумент.")
        telegram_id = 123456789  # Тестовий telegram_id
    
    print(f"👤 Перевіряємо користувача Telegram ID: {telegram_id}")
    
    try:
        from database.db_operations import get_user, get_user_categories
        from database.models import TransactionType
        
        # Отримуємо користувача
        user = get_user(telegram_id)
        if not user:
            print(f"❌ Користувач з Telegram ID {telegram_id} не знайдений")
            print("💡 Користувач повинен спочатку запустити бота командою /start")
            return
        
        print(f"✅ Користувач знайдений: {user.first_name or 'Без імені'} (DB ID: {user.id})")
        
        # Отримуємо всі категорії користувача
        all_categories = get_user_categories(user.id)
        print(f"📊 Всього категорій: {len(all_categories)}")
        
        if not all_categories:
            print("❌ У користувача немає категорій!")
            print("💡 Рекомендація: Створіть категорії через меню налаштувань у боті")
            return
        
        # Розділяємо на витрати та доходи
        expense_categories = [c for c in all_categories if c.type == TransactionType.EXPENSE.value]
        income_categories = [c for c in all_categories if c.type == TransactionType.INCOME.value]
        
        print(f"💸 Витрати: {len(expense_categories)}")
        print(f"💰 Доходи: {len(income_categories)}")
        print()
        
        # Показуємо витрати
        if expense_categories:
            print("📋 КАТЕГОРІЇ ВИТРАТ:")
            for i, cat in enumerate(expense_categories, 1):
                icon = cat.icon or "💸"
                print(f"  {i}. {icon} {cat.name} (ID: {cat.id})")
        else:
            print("❌ Немає категорій витрат")
        
        print()
        
        # Показуємо доходи
        if income_categories:
            print("📋 КАТЕГОРІЇ ДОХОДІВ:")
            for i, cat in enumerate(income_categories, 1):
                icon = cat.icon or "💰"
                print(f"  {i}. {icon} {cat.name} (ID: {cat.id})")
        else:
            print("❌ Немає категорій доходів")
        
        print()
        
        # Тестуємо пагінацію
        print("🔄 ТЕСТ ПАГІНАЦІЇ:")
        per_page = 8
        total_categories = len(all_categories)
        total_pages = max(1, (total_categories + per_page - 1) // per_page)
        
        print(f"  • Категорій на сторінку: {per_page}")
        print(f"  • Всього сторінок: {total_pages}")
        
        # Створюємо загальний список для пагінації
        all_categories_for_pagination = expense_categories + income_categories
        
        for page in range(1, total_pages + 1):
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            page_categories = all_categories_for_pagination[start_idx:end_idx]
            
            print(f"\n  📄 СТОРІНКА {page}:")
            print(f"    Категорій на сторінці: {len(page_categories)}")
            
            # Розділяємо за типом на сторінці
            page_expense_categories = [c for c in page_categories if c.type == TransactionType.EXPENSE.value]
            page_income_categories = [c for c in page_categories if c.type == TransactionType.INCOME.value]
            
            if page_expense_categories:
                print(f"    💸 Витрати ({len(page_expense_categories)}):")
                for cat in page_expense_categories:
                    print(f"      • {cat.icon or '💸'} {cat.name}")
            
            if page_income_categories:
                print(f"    💰 Доходи ({len(page_income_categories)}):")
                for cat in page_income_categories:
                    print(f"      • {cat.icon or '💰'} {cat.name}")
            
            if not page_expense_categories and not page_income_categories:
                print("    ❌ ПУСТА СТОРІНКА!")
        
        print(f"\n✅ Діагностика завершена")
        
    except Exception as e:
        print(f"❌ Помилка під час діагностики: {e}")
        import traceback
        traceback.print_exc()

def check_database_basic():
    """Базова перевірка бази даних"""
    print("🔍 Базова перевірка бази даних\n")
    
    try:
        from database.models import Session, User, Category
        
        session = Session()
        
        try:
            users_count = session.query(User).count()
            categories_count = session.query(Category).count()
            
            print(f"👥 Користувачів у базі: {users_count}")
            print(f"📂 Категорій у базі: {categories_count}")
            
            if users_count > 0:
                print(f"\n📋 Перші 3 користувачі:")
                users = session.query(User).limit(3).all()
                for user in users:
                    print(f"  • Telegram ID: {user.telegram_id}, Ім'я: {user.first_name or 'Без імені'}")
            
            print(f"\n✅ Базова перевірка завершена")
            
        finally:
            session.close()
        
    except Exception as e:
        print(f"❌ Помилка під час перевірки: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Спочатку перевіряємо базу даних
    check_database_basic()
    print("-" * 50)
    
    # Потім діагностуємо категорії
    if len(sys.argv) > 1:
        try:
            telegram_id = int(sys.argv[1])
            debug_user_categories(telegram_id)
        except ValueError:
            print("❌ Невірний формат telegram_id. Має бути числом.")
    else:
        debug_user_categories()
