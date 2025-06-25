#!/usr/bin/env python3
"""
Діагностика типів категорій
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_category_types():
    """Перевіряє типи категорій в базі даних"""
    
    print("🔍 Діагностика типів категорій\n")
    
    try:
        from database.models import Session, Category, TransactionType
        
        session = Session()
        
        try:
            # Отримуємо всі категорії
            all_categories = session.query(Category).all()
            
            print(f"📊 Всього категорій в базі: {len(all_categories)}")
            
            if not all_categories:
                print("❌ Немає категорій в базі даних")
                return
            
            # Групуємо за типами
            type_counts = {}
            categories_by_type = {}
            
            for cat in all_categories:
                cat_type = cat.type
                type_str = str(cat_type)
                
                if type_str not in type_counts:
                    type_counts[type_str] = 0
                    categories_by_type[type_str] = []
                
                type_counts[type_str] += 1
                categories_by_type[type_str].append(cat)
            
            print("\n📋 Розподіл за типами:")
            for type_str, count in type_counts.items():
                print(f"  • {type_str}: {count}")
            
            print(f"\n🔍 Очікувані типи:")
            print(f"  • {TransactionType.EXPENSE}: витрати")
            print(f"  • {TransactionType.INCOME}: доходи")
            
            # Показуємо деталі категорій
            for type_str, categories in categories_by_type.items():
                print(f"\n📂 Категорії типу '{type_str}':")
                for cat in categories[:10]:  # Показуємо перші 10
                    icon = cat.icon or "❓"
                    print(f"  • {icon} {cat.name} (ID: {cat.id}, User: {cat.user_id})")
                if len(categories) > 10:
                    print(f"  ... та ще {len(categories) - 10}")
            
            # Перевіряємо користувача 1
            user_categories = session.query(Category).filter(Category.user_id == 1).all()
            print(f"\n👤 Категорій користувача ID=1: {len(user_categories)}")
            
            if user_categories:
                user_type_counts = {}
                for cat in user_categories:
                    type_str = str(cat.type)
                    user_type_counts[type_str] = user_type_counts.get(type_str, 0) + 1
                
                print("📊 Розподіл категорій користувача за типами:")
                for type_str, count in user_type_counts.items():
                    print(f"  • {type_str}: {count}")
            
            print(f"\n✅ Діагностика завершена")
            
        finally:
            session.close()
        
    except Exception as e:
        print(f"❌ Помилка під час діагностики: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_category_types()
