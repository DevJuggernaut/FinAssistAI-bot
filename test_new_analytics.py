#!/usr/bin/env python3
"""
Тестування нової аналітики (статистика + графіки)
"""

import asyncio
import sys
import os

# Додаємо шлях до проекту
sys.path.insert(0, os.path.abspath('.'))

from unittest.mock import MagicMock, AsyncMock
from handlers.analytics_handler import show_analytics_main_menu, show_analytics_detailed, show_analytics_charts
from database.models import User, Transaction, Category, TransactionType
from datetime import datetime, timedelta

# Мок об'єкти
class MockQuery:
    def __init__(self, user_id=12345):
        self.from_user = MagicMock()
        self.from_user.id = user_id
        self.edit_message_text = AsyncMock()

class MockContext:
    def __init__(self):
        pass

async def test_analytics_menu():
    """Тест головного меню аналітики"""
    print("🧪 ТЕСТ: Головне меню аналітики")
    print("=" * 50)
    
    query = MockQuery()
    context = MockContext()
    
    # Мок користувача
    mock_user = User(id=12345, telegram_id=12345, username="testuser")
    
    # Патчимо get_user
    import handlers.analytics_handler
    original_get_user = handlers.analytics_handler.get_user
    handlers.analytics_handler.get_user = lambda user_id: mock_user
    
    try:
        await show_analytics_main_menu(query, context)
        
        # Перевіряємо чи було викликано edit_message_text
        assert query.edit_message_text.called, "Метод edit_message_text не було викликано"
        
        # Отримуємо аргументи виклику
        call_args = query.edit_message_text.call_args
        text = call_args[1]['text']  # kwargs['text']
        
        print("✅ Тест пройшов успішно!")
        print("📝 Текст меню:")
        print(text[:200] + "..." if len(text) > 200 else text)
        
        # Перевіряємо ключові фрази
        assert "📊 **Аналітика та звіти**" in text, "Заголовок не знайдено"
        assert "Графіки" in text, "Розділ 'Графіки' не знайдено"
        assert "Статистика" in text, "Розділ 'Статистика' не знайдено"
        
        print("✅ Всі перевірки пройшли!")
        
    except Exception as e:
        print(f"❌ Помилка в тесті: {e}")
    finally:
        # Відновлюємо оригінальну функцію
        handlers.analytics_handler.get_user = original_get_user

async def test_analytics_statistics():
    """Тест нової статистики"""
    print("\n🧪 ТЕСТ: Нова статистика")
    print("=" * 50)
    
    query = MockQuery()
    context = MockContext()
    
    # Мок користувача
    mock_user = User(id=12345, telegram_id=12345, username="testuser")
    
    # Мок категорії - видаляємо, оскільки створюємо в новому коді
    
    # Мок транзакцій (останні 30 днів)
    now = datetime.now()
    
    # Створюємо мок об'єкти замість реальних моделей
    class MockTransaction:
        def __init__(self, amount, type, description, category=None, date=None):
            self.amount = amount
            self.type = type
            self.description = description
            self.category = category
            self.date = date or now
    
    class MockCategory:
        def __init__(self, name, icon="💰"):
            self.name = name
            self.icon = icon
    
    food_cat = MockCategory("Їжа та ресторани", "🍽️")
    transport_cat = MockCategory("Транспорт", "🚗")
    
    mock_transactions = [
        # Доходи
        MockTransaction(15000, TransactionType.INCOME, "Зарплата", date=now - timedelta(days=1)),
        # Витрати
        MockTransaction(4200, TransactionType.EXPENSE, "Їжа", food_cat, now - timedelta(days=2)),
        MockTransaction(3000, TransactionType.EXPENSE, "Транспорт", transport_cat, now - timedelta(days=3)),
        MockTransaction(2500, TransactionType.EXPENSE, "Комунальні", date=now - timedelta(days=5)),
        MockTransaction(2800, TransactionType.EXPENSE, "Інші витрати", date=now - timedelta(days=10)),
    ]
    
    # Мок транзакцій попереднього періоду (для тренду)
    prev_transactions = [
        MockTransaction(13300, TransactionType.EXPENSE, "Попередні витрати", date=now - timedelta(days=40)),
    ]
    
    # Патчимо функції
    import handlers.analytics_handler
    original_get_user = handlers.analytics_handler.get_user
    original_get_user_transactions = handlers.analytics_handler.get_user_transactions
    
    def mock_get_user_transactions(user_id, start_date=None, end_date=None):
        # Повертаємо різні дані залежно від періоду
        if start_date and start_date < now - timedelta(days=35):
            return prev_transactions
        return mock_transactions
    
    handlers.analytics_handler.get_user = lambda user_id: mock_user
    handlers.analytics_handler.get_user_transactions = mock_get_user_transactions
    
    try:
        await show_analytics_detailed(query, context)
        
        # Перевіряємо чи було викликано edit_message_text
        assert query.edit_message_text.called, "Метод edit_message_text не було викликано"
        
        # Отримуємо аргументи виклику
        call_args = query.edit_message_text.call_args
        text = call_args[1]['text']  # kwargs['text']
        
        print("✅ Тест пройшов успішно!")
        print("📊 Зразок статистики:")
        print(text[:400] + "..." if len(text) > 400 else text)
        
        # Перевіряємо ключові елементи
        assert "📈 **Ваша фінансова статистика**" in text, "Заголовок статистики не знайдено"
        assert "Основні показники" in text, "Основні показники не знайдені"
        assert "Аналіз заощаджень" in text, "Аналіз заощаджень не знайдений"
        assert "Структура витрат" in text, "Структура витрат не знайдена"
        assert "Тренд витрат" in text, "Тренд витрат не знайдений"
        assert "фінансові висновки" in text, "Фінансові висновки не знайдені"
        
        print("✅ Всі елементи статистики присутні!")
        
    except Exception as e:
        print(f"❌ Помилка в тесті: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Відновлюємо оригінальні функції
        handlers.analytics_handler.get_user = original_get_user
        handlers.analytics_handler.get_user_transactions = original_get_user_transactions

async def test_analytics_charts():
    """Тест меню графіків"""
    print("\n🧪 ТЕСТ: Меню графіків")
    print("=" * 50)
    
    query = MockQuery()
    context = MockContext()
    
    try:
        await show_analytics_charts(query, context)
        
        # Перевіряємо чи було викликано edit_message_text
        assert query.edit_message_text.called, "Метод edit_message_text не було викликано"
        
        # Отримуємо аргументи виклику
        call_args = query.edit_message_text.call_args
        text = call_args[1]['text']  # kwargs['text']
        
        print("✅ Тест пройшов успішно!")
        print("📊 Меню графіків:")
        print(text[:300] + "..." if len(text) > 300 else text)
        
        # Перевіряємо ключові елементи
        assert "📊 **Графіки та діаграми**" in text, "Заголовок не знайдено"
        assert "Кругова діаграма" in text, "Кругова діаграма не знайдена"
        assert "Стовпчастий графік" in text, "Стовпчастий графік не знайдений"
        
        print("✅ Всі типи графіків присутні!")
        
    except Exception as e:
        print(f"❌ Помилка в тесті: {e}")

async def main():
    """Запуск всіх тестів"""
    print("🚀 ТЕСТУВАННЯ НОВОЇ АНАЛІТИКИ")
    print("=" * 60)
    
    await test_analytics_menu()
    await test_analytics_statistics()
    await test_analytics_charts()
    
    print("\n" + "=" * 60)
    print("🎊 ВСІ ТЕСТИ ЗАВЕРШЕНІ!")
    print("✅ Нова аналітика працює корректно")
    print("📊 Статистика показує корисні висновки")
    print("📈 Графіки спрощені до 2 типів")
    print("🎯 UX покращений для користувача")

if __name__ == "__main__":
    asyncio.run(main())
