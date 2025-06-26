#!/usr/bin/env python3
"""
Тестування імпорту транзакцій для виявлення проблем
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.session import init_db, Session
from database.models import User, Transaction, Category, Account
from database.db_operations import get_or_create_user, get_user_accounts, get_user_categories
from services.statement_parser import StatementParser
import logging

# Налаштування логування
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_import_flow():
    """Тестуємо повний процес імпорту як у боті"""
    try:
        init_db()
        
        # Створюємо тестового користувача (використовуємо реальний ID з бази)
        test_user_id = 123456789  # Замініть на ваш реальний telegram_id
        user = get_or_create_user(test_user_id)
        print(f"User: {user.id}, telegram_id: {user.telegram_id}")
        
        # Перевіряємо рахунки користувача
        accounts = get_user_accounts(user.id)
        print(f"User accounts: {[acc.name for acc in accounts]}")
        
        # Перевіряємо категорії користувача
        categories = get_user_categories(user.id)
        print(f"User categories: {[(cat.name, cat.type) for cat in categories]}")
        
        # Тестуємо парсер з реальним PDF файлом
        pdf_path = "report_20-06-2025_16-12-03.pdf"
        
        if not os.path.exists(pdf_path):
            print("❌ Моноbank PDF файл не знайдено для тестування")
            return
        
        print(f"📄 Тестуємо з файлом: {pdf_path}")
        
        # Парсимо PDF
        parser = StatementParser()
        transactions = parser.parse_bank_statement(pdf_path, "monobank")
        
        print(f"📊 Знайдено {len(transactions)} транзакцій:")
        for i, trans in enumerate(transactions[:3], 1):  # Показуємо перші 3
            print(f"  {i}. Amount: {trans.get('amount')}, Description: {trans.get('description', '')[:50]}, Type: {trans.get('type')}")
        
        if not transactions:
            print("❌ Жодної транзакції не знайдено")
            return
        
        # Симулюємо імпорт як у боті
        session = Session()
        imported_count = 0
        
        print("\n🔄 Починаємо імпорт...")
        
        for trans in transactions[:2]:  # Імпортуємо тільки перші 2 для тесту
            try:
                from database.models import TransactionType
                from datetime import datetime
                
                # Отримуємо дані транзакції
                amount = abs(float(trans.get('amount', 0)))
                description = trans.get('description', '').strip() or "Тестова транзакція"
                trans_type = trans.get('type', 'expense')
                
                if amount == 0:
                    print(f"⚠️ Пропускаємо транзакцію з нульовою сумою: {description[:30]}")
                    continue
                
                # Визначаємо тип транзакції
                if isinstance(trans_type, str):
                    transaction_type = TransactionType.EXPENSE if trans_type == 'expense' else TransactionType.INCOME
                else:
                    transaction_type = trans_type
                
                print(f"  💰 Додаємо: {amount} UAH, {description[:30]}, тип: {transaction_type}")
                
                # Визначаємо дату
                date = trans.get('date')
                if isinstance(date, str):
                    try:
                        from datetime import datetime
                        date = datetime.strptime(date, '%Y-%m-%d').date()
                    except:
                        date = datetime.now().date()
                elif not date:
                    date = datetime.now().date()
                
                # Знаходимо категорію
                category_id = None
                if categories:
                    # Використовуємо першу доступну категорію відповідного типу
                    matching_categories = [cat for cat in categories if cat.type == transaction_type.value]
                    if matching_categories:
                        category_id = matching_categories[0].id
                        print(f"    📂 Категорія: {matching_categories[0].name}")
                
                # Знаходимо рахунок
                account_id = None
                if accounts:
                    account_id = accounts[0].id
                    print(f"    🏦 Рахунок: {accounts[0].name}")
                
                # Створюємо транзакцію
                transaction = Transaction(
                    user_id=user.id,
                    amount=amount,
                    type=transaction_type,
                    description=description,
                    transaction_date=date,
                    category_id=category_id,
                    account_id=account_id,
                    created_at=datetime.now(),
                    source='import'
                )
                
                session.add(transaction)
                imported_count += 1
                print(f"    ✅ Транзакція додана до сесії")
                
            except Exception as e:
                print(f"    ❌ Помилка транзакції: {e}")
                logger.exception("Transaction import error")
                continue
        
        # Коммітимо зміни
        print(f"\n💾 Коммітимо {imported_count} транзакцій...")
        session.commit()
        print("✅ Комміт виконано успішно")
        
        # Перевіряємо, чи з'явилися транзакції в базі
        from database.db_operations import get_transactions
        all_transactions = get_transactions(user.id)
        print(f"📊 Всього транзакцій користувача в базі: {len(all_transactions)}")
        
        # Показуємо останні транзакції
        recent_transactions = all_transactions[-5:] if all_transactions else []
        print("\n🕐 Останні транзакції:")
        for trans in recent_transactions:
            print(f"  - {trans.amount} UAH, {trans.description[:30]}, {trans.transaction_date}")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Загальна помилка: {e}")
        logger.exception("General error")

if __name__ == "__main__":
    test_import_flow()
