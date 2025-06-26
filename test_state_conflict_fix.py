#!/usr/bin/env python3
"""
Тест виправлення конфлікту станів при обробці повідомлень
"""

import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock
import logging

# Додаємо кореневу директорію до шляху
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers.message_handler import handle_text_message
from database.models import User

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_state_conflict_scenarios():
    """Тестуємо різні сценарії конфлікту станів"""
    
    print("🧪 Тестування виправлення конфлікту станів")
    print("=" * 50)
    
    test_scenarios = [
        {
            "name": "Сценарій 1: Користувач завершив налаштування, створює рахунок",
            "user_setup_completed": True,
            "context_data": {
                "setup_step": "balance",  # Конфлікт! 
                "awaiting_account_balance": True,
                "account_creation": {
                    "name": "Тестовий рахунок",
                    "icon": "💳"
                }
            },
            "input_text": "1500",
            "expected_handler": "accounts_handler",
            "description": "Користувач налаштований, але якимось чином має setup_step='balance'"
        },
        {
            "name": "Сценарій 2: Новий користувач, початкове налаштування",
            "user_setup_completed": False,
            "context_data": {
                "setup_step": "balance"
            },
            "input_text": "5000",
            "expected_handler": "setup_callbacks",
            "description": "Новий користувач проходить початкове налаштування"
        },
        {
            "name": "Сценарій 3: Користувач завершений, тільки account_balance",
            "user_setup_completed": True,
            "context_data": {
                "awaiting_account_balance": True,
                "account_creation": {
                    "name": "Новий рахунок",
                    "icon": "🏦"
                }
            },
            "input_text": "2500",
            "expected_handler": "accounts_handler",
            "description": "Чистий сценарій створення рахунку без конфліктів"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 {scenario['name']}")
        print(f"   Опис: {scenario['description']}")
        print(f"   Користувач налаштований: {scenario['user_setup_completed']}")
        print(f"   Контекст: {scenario['context_data']}")
        print(f"   Ввід: '{scenario['input_text']}'")
        
        try:
            # Створюємо мок об'єкти
            update = Mock()
            update.effective_user.id = 12345
            update.message.text = scenario['input_text']
            update.message.reply_text = AsyncMock()
            
            context = Mock()
            context.user_data = scenario['context_data'].copy()
            
            # Створюємо мок користувача
            mock_user = Mock()
            mock_user.id = 1
            mock_user.telegram_id = 12345
            mock_user.is_setup_completed = scenario['user_setup_completed']
            mock_user.setup_step = 'completed' if scenario['user_setup_completed'] else 'start'
            mock_user.currency = 'UAH'
            
            # Мокаємо get_user
            import handlers.message_handler
            original_get_user = handlers.message_handler.get_user
            handlers.message_handler.get_user = Mock(return_value=mock_user)
            
            # Мокаємо обробники
            process_initial_balance_called = False
            handle_account_text_input_called = False
            
            async def mock_process_initial_balance(update, context):
                nonlocal process_initial_balance_called
                process_initial_balance_called = True
                logger.info("process_initial_balance викликано")
            
            async def mock_handle_account_text_input(message, context):
                nonlocal handle_account_text_input_called
                handle_account_text_input_called = True
                logger.info("handle_account_text_input викликано")
                return True
            
            # Патчимо функції
            import handlers.setup_callbacks
            import handlers.accounts_handler
            
            original_process_initial_balance = handlers.setup_callbacks.process_initial_balance
            original_handle_account_text_input = handlers.accounts_handler.handle_account_text_input
            
            handlers.setup_callbacks.process_initial_balance = mock_process_initial_balance
            handlers.accounts_handler.handle_account_text_input = mock_handle_account_text_input
            
            # Викликаємо обробник
            await handle_text_message(update, context)
            
            # Перевіряємо результати
            print(f"   Стан після обробки:")
            print(f"     - setup_step у контексті: {context.user_data.get('setup_step', 'Відсутній')}")
            print(f"     - awaiting_account_balance: {context.user_data.get('awaiting_account_balance', False)}")
            print(f"     - process_initial_balance викликано: {process_initial_balance_called}")
            print(f"     - handle_account_text_input викликано: {handle_account_text_input_called}")
            
            # Перевіряємо очікувані результати
            if scenario['expected_handler'] == 'setup_callbacks':
                if process_initial_balance_called:
                    print("   ✅ ПРОЙШОВ: Правильно перенаправлено до setup_callbacks")
                else:
                    print("   ❌ ПРОВАЛЕНО: Очікувався setup_callbacks")
            elif scenario['expected_handler'] == 'accounts_handler':
                if handle_account_text_input_called:
                    print("   ✅ ПРОЙШОВ: Правильно перенаправлено до accounts_handler")
                else:
                    print("   ❌ ПРОВАЛЕНО: Очікувався accounts_handler")
            
            # Перевіряємо, чи очищено конфлікт
            if (scenario['user_setup_completed'] and 
                'setup_step' in scenario['context_data'] and
                scenario['context_data']['setup_step'] == 'balance'):
                if 'setup_step' not in context.user_data:
                    print("   ✅ ВИПРАВЛЕНО: Конфліктний setup_step очищено")
                else:
                    print("   ❌ ПОМИЛКА: Конфліктний setup_step не очищено")
            
            # Відновлюємо оригінальні функції
            handlers.message_handler.get_user = original_get_user
            handlers.setup_callbacks.process_initial_balance = original_process_initial_balance
            handlers.accounts_handler.handle_account_text_input = original_handle_account_text_input
            
        except Exception as e:
            print(f"   ❌ ПОМИЛКА: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎯 Тестування завершено")

async def main():
    await test_state_conflict_scenarios()

if __name__ == "__main__":
    asyncio.run(main())
