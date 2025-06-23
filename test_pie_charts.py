#!/usr/bin/env python3
"""
Тестування нової функціональності кругових діаграм для огляду фінансів
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.report_generator import FinancialReport
from database.db_operations import get_or_create_user
from database.session import Session
from database.models import Transaction, Category, TransactionType
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pie_charts():
    """Тестуємо генерацію кругових діаграм"""
    
    # Тестовий користувач (ваш telegram_id)
    test_telegram_id = 580683833
    
    try:
        # Отримуємо користувача
        user = get_or_create_user(test_telegram_id)
        logger.info(f"Знайдено користувача: {user.id}")
        
        # Створюємо звіт
        financial_report = FinancialReport(user.id)
        
        # Тестуємо кругову діаграму витрат
        logger.info("Генеруємо кругову діаграму витрат...")
        expenses_chart, error = financial_report.generate_expense_pie_chart()
        
        if error:
            logger.error(f"Помилка генерації діаграми витрат: {error}")
        else:
            logger.info("✅ Діаграма витрат згенерована успішно!")
            
        # Тестуємо кругову діаграму доходів
        logger.info("Генеруємо кругову діаграму доходів...")
        income_chart, error = financial_report.generate_income_pie_chart()
        
        if error:
            logger.error(f"Помилка генерації діаграми доходів: {error}")
        else:
            logger.info("✅ Діаграма доходів згенерована успішно!")
            
        # Перевіряємо наявність транзакцій
        session = Session()
        expense_count = session.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.EXPENSE
        ).count()
        
        income_count = session.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.INCOME
        ).count()
        
        session.close()
        
        logger.info(f"📊 Статистика транзакцій:")
        logger.info(f"   Витрати: {expense_count} транзакцій")
        logger.info(f"   Доходи: {income_count} транзакцій")
        
        if expense_count == 0:
            logger.warning("⚠️ Немає витрат для тестування діаграми")
        if income_count == 0:
            logger.warning("⚠️ Немає доходів для тестування діаграми")
            
        logger.info("🎉 Тестування завершено успішно!")
        
    except Exception as e:
        logger.error(f"❌ Помилка під час тестування: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pie_charts()
