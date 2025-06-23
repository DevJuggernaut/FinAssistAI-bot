#!/usr/bin/env python3
"""
Міграція бази даних для додавання підтримки рахунків.
Додає:
1. Таблицю accounts
2. Поле account_id до таблиці transactions
3. Створює головний рахунок для існуючих користувачів
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Base, engine, Session, User, Account, Transaction, TransactionType, AccountType
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Виконує міграцію бази даних"""
    
    logger.info("🔄 Початок міграції бази даних...")
    
    try:
        # 1. Створюємо нові таблиці
        logger.info("📋 Створення нових таблиць...")
        Base.metadata.create_all(engine)
        logger.info("✅ Таблиці створено успішно")
        
        # 2. Створюємо головні рахунки для існуючих користувачів
        logger.info("👥 Створення головних рахунків для існуючих користувачів...")
        session = Session()
        
        try:
            users = session.query(User).filter(User.is_setup_completed == True).all()
            created_accounts = 0
            
            for user in users:
                # Перевіряємо, чи вже є рахунок у користувача
                existing_account = session.query(Account).filter(Account.user_id == user.id).first()
                
                if not existing_account:
                    # Створюємо головний рахунок з початковим балансом
                    account = Account(
                        user_id=user.id,
                        name="Головний рахунок",
                        account_type=AccountType.CASH,
                        balance=user.initial_balance or 0.0,
                        currency=user.currency or 'UAH',
                        is_main=True,
                        icon='💰',
                        description="Автоматично створений під час міграції",
                        created_at=user.created_at or datetime.utcnow()
                    )
                    session.add(account)
                    created_accounts += 1
                    
                    logger.info(f"✅ Створено рахунок для користувача {user.telegram_id}")
            
            session.commit()
            logger.info(f"✅ Створено {created_accounts} головних рахунків")
            
            # 3. Оновлюємо існуючі транзакції, прив'язуючи їх до головних рахунків
            logger.info("🔗 Прив'язка існуючих транзакцій до рахунків...")
            updated_transactions = 0
            
            for user in users:
                main_account = session.query(Account).filter(
                    Account.user_id == user.id,
                    Account.is_main == True
                ).first()
                
                if main_account:
                    # Оновлюємо транзакції без account_id
                    transactions = session.query(Transaction).filter(
                        Transaction.user_id == user.id,
                        Transaction.account_id == None
                    ).all()
                    
                    for transaction in transactions:
                        transaction.account_id = main_account.id
                        updated_transactions += 1
            
            session.commit()
            logger.info(f"✅ Оновлено {updated_transactions} транзакцій")
            
        finally:
            session.close()
        
        logger.info("🎉 Міграція завершена успішно!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Помилка під час міграції: {str(e)}")
        return False

def verify_migration():
    """Перевіряє, чи міграція виконана коректно"""
    logger.info("🔍 Перевірка міграції...")
    
    session = Session()
    try:
        # Перевіряємо кількість користувачів та рахунків
        users_count = session.query(User).filter(User.is_setup_completed == True).count()
        accounts_count = session.query(Account).count()
        main_accounts_count = session.query(Account).filter(Account.is_main == True).count()
        
        logger.info(f"📊 Користувачів з налаштуванням: {users_count}")
        logger.info(f"📊 Всього рахунків: {accounts_count}")
        logger.info(f"📊 Головних рахунків: {main_accounts_count}")
        
        # Перевіряємо транзакції з рахунками
        transactions_with_accounts = session.query(Transaction).filter(Transaction.account_id != None).count()
        total_transactions = session.query(Transaction).count()
        
        logger.info(f"📊 Транзакцій з рахунками: {transactions_with_accounts}")
        logger.info(f"📊 Всього транзакцій: {total_transactions}")
        
        if users_count == main_accounts_count:
            logger.info("✅ Міграція пройшла успішно!")
            return True
        else:
            logger.warning("⚠️ Можливі проблеми з міграцією")
            return False
            
    finally:
        session.close()

if __name__ == "__main__":
    print("🏦 Міграція FinAssist: Додавання підтримки рахунків")
    print("=" * 50)
    
    success = run_migration()
    if success:
        verify_migration()
        print("\n🎉 Міграція завершена! Бот готовий до роботи з рахунками.")
    else:
        print("\n❌ Міграція не вдалася. Перевірте логи.")
        sys.exit(1)
