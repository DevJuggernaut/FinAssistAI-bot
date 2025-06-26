#!/usr/bin/env python3
"""
Перевірка користувачів у базі даних
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_operations import Session
from database.models import User, Category, Transaction

def check_database():
    """Перевіряє стан бази даних"""
    print("=== Перевірка бази даних ===\n")
    
    session = Session()
    
    # Перевіряємо користувачів
    users = session.query(User).all()
    print(f"👥 Користувачів у базі: {len(users)}")
    
    if users:
        for user in users[:5]:  # показуємо перших 5
            print(f"  - ID: {user.id}, Telegram ID: {user.telegram_id}, Username: {user.username}")
    
    # Перевіряємо категорії
    categories = session.query(Category).all()
    print(f"\n📂 Категорій у базі: {len(categories)}")
    
    if categories:
        for cat in categories[:10]:  # показуємо перших 10
            print(f"  - ID: {cat.id}, User ID: {cat.user_id}, Name: {cat.name}, Type: {cat.type}")
    
    # Перевіряємо транзакції
    transactions = session.query(Transaction).all()
    print(f"\n💸 Транзакцій у базі: {len(transactions)}")
    
    if transactions:
        for trans in transactions[:5]:  # показуємо перших 5
            print(f"  - ID: {trans.id}, User ID: {trans.user_id}, Amount: {trans.amount}, Type: {trans.type}")
    
    session.close()
    print("\n=== Перевірка завершена ===")

if __name__ == "__main__":
    check_database()
