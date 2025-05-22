import unittest
import os
import sys
import logging
from datetime import datetime

# Додаємо базову директорію проекту в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Імпортуємо модулі для тестування
from database.db_operations import get_or_create_user, add_transaction, get_user_categories, create_or_update_budget
from database.models import init_db, User, Category, Transaction, Base, engine, BudgetPlan, CategoryBudget
from services.category_classifier import classify_transaction, get_category_suggestions
from services.financial_advisor import get_financial_advice
from services.document_parser import BankStatementParser, ReceiptParser
from services.report_generator import FinancialReport, generate_user_report
from services.budget_manager import BudgetManager

# Імпортуємо окремі тести
from tests.test_budget_manager import TestBudgetManager

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestBotFunctions(unittest.TestCase):
    """Тести для основних функцій бота"""
    
    @classmethod
    def setUpClass(cls):
        """Виконується один раз перед усіма тестами"""
        # Створюємо тестову базу даних
        cls.test_user_id = 12345  # тестовий Telegram ID
        
        # Ініціалізуємо базу даних
        logger.info("Підготовка тестової бази даних...")
        Base.metadata.create_all(engine)
        
        # Створюємо тестового користувача
        cls.db_user = get_or_create_user(
            telegram_id=cls.test_user_id,
            username="test_user",
            first_name="Test",
            last_name="User"
        )
        
        # Додаємо тестові транзакції
        cls._add_test_transactions(cls.db_user.id)
    
    @classmethod
    def _add_test_transactions(cls, user_id):
        """Додавання тестових транзакцій для користувача"""
        # Отримуємо категорії користувача
        expense_categories = get_user_categories(user_id, 'expense')
        income_categories = get_user_categories(user_id, 'income')
        
        if not expense_categories or not income_categories:
            logger.warning("No categories found for test user")
            return
        
        # Додаємо тестові витрати
        expense_transactions = [
            {"description": "Покупка продуктів у супермаркеті", "amount": 450.50, "category": "Продукти"},
            {"description": "Обід у кафе", "amount": 250.00, "category": "Кафе і ресторани"},
            {"description": "Таксі до роботи", "amount": 120.00, "category": "Транспорт"},
            {"description": "Ліки в аптеці", "amount": 320.75, "category": "Здоров'я"},
            {"description": "Нова футболка", "amount": 500.00, "category": "Покупки"},
            {"description": "Рахунок за газ", "amount": 800.00, "category": "Комунальні послуги"},
            {"description": "Квитки у кіно", "amount": 200.00, "category": "Розваги"}
        ]
        
        # Додаємо тестові доходи
        income_transactions = [
            {"description": "Зарплата за квітень", "amount": 15000.00, "category": "Зарплата"},
            {"description": "Фріланс проект", "amount": 5000.00, "category": "Фріланс"},
            {"description": "Повернення від друга", "amount": 1000.00, "category": "Інше"}
        ]
        
        # Додаємо витрати
        for tx in expense_transactions:
            # Знаходимо ID відповідної категорії
            category_id = None
            for cat in expense_categories:
                if cat.name == tx["category"]:
                    category_id = cat.id
                    break
            
            if not category_id:
                continue
                
            # Додаємо транзакцію
            add_transaction(
                user_id=user_id,
                amount=tx["amount"],
                description=tx["description"],
                category_id=category_id,
                transaction_type="expense",
                transaction_date=datetime.now()
            )
        
        # Додаємо доходи
        for tx in income_transactions:
            # Знаходимо ID відповідної категорії
            category_id = None
            for cat in income_categories:
                if cat.name == tx["category"]:
                    category_id = cat.id
                    break
            
            if not category_id:
                continue
                
            # Додаємо транзакцію
            add_transaction(
                user_id=user_id,
                amount=tx["amount"],
                description=tx["description"],
                category_id=category_id,
                transaction_type="income",
                transaction_date=datetime.now()
            )
    
    def test_user_creation(self):
        """Тест створення користувача"""
        self.assertIsNotNone(self.db_user)
        self.assertEqual(self.db_user.telegram_id, self.test_user_id)
    
    def test_category_classifier(self):
        """Тест класифікатора транзакцій"""
        # Тестуємо класифікацію витрат
        expense_text = "Продукти у Сільпо"
        category = classify_transaction(expense_text, 'expense')
        self.assertIsNotNone(category)
        logger.info(f"Класифікація '{expense_text}': {category}")
        
        # Тестуємо класифікацію доходів
        income_text = "Зарплата за травень"
        category = classify_transaction(income_text, 'income')
        self.assertIsNotNone(category)
        logger.info(f"Класифікація '{income_text}': {category}")
    
    def test_financial_advice(self):
        """Тест генерації фінансових порад"""
        # Пропускаємо тест, якщо немає ключа API
        import os
        if not os.environ.get('OPENAI_API_KEY'):
            logger.warning("OPENAI_API_KEY не встановлений, пропускаємо тест")
            return
        
        advice = get_financial_advice(self.db_user.id, "general")
        self.assertIsNotNone(advice)
        logger.info(f"Згенерована порада: {advice[:100]}...")
    
    def test_report_generation(self):
        """Тест генерації звіту"""
        report_data = generate_user_report(self.db_user.id)
        self.assertIsNotNone(report_data)
        
        # Перевіряємо, що звіт містить необхідні компоненти
        self.assertIn('html_path', report_data)
        self.assertIn('charts', report_data)
        
        # Перевіряємо, що файл звіту існує
        self.assertTrue(os.path.exists(report_data['html_path']))
        logger.info(f"Звіт згенеровано: {report_data['html_path']}")

if __name__ == '__main__':
    unittest.main()
