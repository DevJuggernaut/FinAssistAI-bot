import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from services.budget_manager import BudgetManager

class TestBudgetManager(unittest.TestCase):
    
    @patch('services.budget_manager.Session')
    def test_get_active_budget_no_budget(self, mock_session):
        # Налаштовуємо мок для випадку відсутності активного бюджету
        mock_session_instance = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order_by = MagicMock()
        
        mock_session.return_value = mock_session_instance
        mock_session_instance.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order_by
        mock_order_by.first.return_value = None  # Немає активного бюджету
        
        # Створюємо екземпляр BudgetManager
        manager = BudgetManager(1)  # Користувач з ID 1
        
        # Викликаємо метод, який ми тестуємо
        result = manager.get_active_budget()
        
        # Перевіряємо результат
        self.assertIsNone(result)
        
        # Перевіряємо виклики моків
        mock_session_instance.query.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_filter.order_by.assert_called_once()
        
    @patch('services.budget_manager.Session')
    def test_budget_status_no_active_budget(self, mock_session):
        # Створюємо менеджер бюджету з моком
        manager = BudgetManager(1)
        manager.get_active_budget = MagicMock(return_value=None)
        
        # Отримуємо статус бюджету
        status = manager.get_budget_status()
        
        # Перевіряємо результат
        self.assertEqual(status['status'], 'no_active_budget')
        self.assertIn('message', status)

if __name__ == '__main__':
    unittest.main()
