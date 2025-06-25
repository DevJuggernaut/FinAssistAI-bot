#!/usr/bin/env python3
"""
Скрипт для перевірки стану бази даних
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_database_status():
    """Перевіряє стан бази даних"""
    
    print("🔍 Перевірка стану бази даних\n")
    
    try:
        from database.db_operations import engine
        from database.models import User, Category, Transaction
        from sqlalchemy import text
        
        # Перевіряємо підключення до бази
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Підключення до бази даних працює")
        
        # Перевіряємо кількість користувачів
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            users_count = session.query(User).count()
            categories_count = session.query(Category).count()
            transactions_count = session.query(Transaction).count()
            
            print(f"👥 Користувачів у базі: {users_count}")
            print(f"📂 Категорій у базі: {categories_count}")
            print(f"💰 Транзакцій у базі: {transactions_count}")
            
            if users_count > 0:
                print(f"\n📋 Перші 5 користувачів:")
                users = session.query(User).limit(5).all()
                for user in users:
                    print(f"  • ID: {user.id}, Ім'я: {user.first_name or 'Без імені'}, Username: @{user.username or 'немає'}")
            
            if categories_count > 0:
                print(f"\n📂 Перші 10 категорій:")
                categories = session.query(Category).limit(10).all()
                for cat in categories:
                    print(f"  • ID: {cat.id}, Назва: {cat.name}, Тип: {cat.type.value}, Користувач: {cat.user_id}")
            
        finally:
            session.close()
        
        print(f"\n✅ Перевірка бази даних завершена")
        
    except Exception as e:
        print(f"❌ Помилка під час перевірки бази даних: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_status()
