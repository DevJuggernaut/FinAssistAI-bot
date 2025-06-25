#!/usr/bin/env python3

"""
Простий тест для перевірки прямого переходу до вибору періоду для стовпчастих графіків
"""

import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bar_chart_direct_period():
    """Тест прямого переходу до вибору періоду для стовпчастих графіків"""
    try:
        print("=== Тест прямого переходу до вибору періоду для стовпчастих графіків ===")
        
        from handlers.callback_handler import handle_callback
        
        # Мокаємо всі необхідні компоненти
        with patch('handlers.callback_handler.get_user') as mock_get_user, \
             patch('handlers.callback_handler.show_chart_period_selection') as mock_show_period:
            
            # Налаштовуємо мок користувача
            mock_user = Mock()
            mock_user.id = 12345
            mock_get_user.return_value = mock_user
            
            # Налаштовуємо мок функції
            mock_show_period.return_value = None
            
            # Створюємо мок update та context
            update = Mock()
            update.effective_user = Mock()
            update.effective_user.id = 12345
            
            # Мок callback query
            query = Mock()
            query.data = "chart_type_bar"
            query.answer = AsyncMock()
            update.callback_query = query
            
            context = Mock()
            context.user_data = {}
            
            # Викликаємо обробник
            await handle_callback(update, context)
            
            # Перевіряємо, що функція show_chart_period_selection була викликана
            mock_show_period.assert_called_once()
            call_args = mock_show_period.call_args
            
            # Перевіряємо аргументи виклику
            assert call_args[0][0] == query  # query
            assert call_args[0][1] == context  # context
            assert call_args[0][2] == "bar"  # chart_type
            assert call_args[0][3] == "comparison"  # data_type
            
            print("✅ Тест пройшов успішно!")
            print("✅ При виборі стовпчастого графіку одразу показується вибір періоду")
            print("✅ Тип даних автоматично встановлюється як 'comparison'")
            
            return True
            
    except Exception as e:
        print(f"❌ Помилка в тесті: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_pie_chart_unchanged():
    """Тест що кругові діаграми поводяться по-старому"""
    try:
        print("\n=== Тест незмінної поведінки для кругових діаграм ===")
        
        from handlers.callback_handler import handle_callback
        
        # Мокаємо всі необхідні компоненти
        with patch('handlers.callback_handler.get_user') as mock_get_user, \
             patch('handlers.callback_handler.show_chart_data_type_selection') as mock_show_data_type:
            
            # Налаштовуємо мок користувача
            mock_user = Mock()
            mock_user.id = 12345
            mock_get_user.return_value = mock_user
            
            # Налаштовуємо мок функції
            mock_show_data_type.return_value = None
            
            # Створюємо мок update та context
            update = Mock()
            update.effective_user = Mock()
            update.effective_user.id = 12345
            
            # Мок callback query
            query = Mock()
            query.data = "chart_type_pie"
            query.answer = AsyncMock()
            update.callback_query = query
            
            context = Mock()
            context.user_data = {}
            
            # Викликаємо обробник
            await handle_callback(update, context)
            
            # Перевіряємо, що функція show_chart_data_type_selection була викликана
            mock_show_data_type.assert_called_once()
            call_args = mock_show_data_type.call_args
            
            # Перевіряємо аргументи виклику
            assert call_args[0][0] == query  # query
            assert call_args[0][1] == context  # context
            assert call_args[0][2] == "pie"  # chart_type
            
            print("✅ Тест пройшов успішно!")
            print("✅ Кругові діаграми все ще показують вибір типу даних")
            
            return True
            
    except Exception as e:
        print(f"❌ Помилка в тесті: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Запуск всіх тестів"""
    print("🧪 Запуск тестів прямого переходу до періоду для стовпчастих графіків...")
    
    test1_result = await test_bar_chart_direct_period()
    test2_result = await test_pie_chart_unchanged()
    
    if test1_result and test2_result:
        print("\n🎉 Всі тести пройшли успішно!")
        print("📊 Стовпчасті графіки: прямий перехід до вибору періоду")
        print("🍩 Кругові діаграми: поведінка незмінна")
        
        print("\n📋 Короткий підсумок змін:")
        print("• chart_type_bar → show_chart_period_selection(query, context, 'bar', 'comparison')")
        print("• chart_type_pie → show_chart_data_type_selection(query, context, 'pie') (без змін)")
        
    else:
        print("\n❌ Деякі тести не пройшли!")

if __name__ == "__main__":
    asyncio.run(main())
