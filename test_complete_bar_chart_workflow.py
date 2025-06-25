#!/usr/bin/env python3

"""
Комплексний тест всіх змін для стовпчастих графіків
"""

import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_workflow():
    """Комплексний тест повного workflow для стовпчастих графіків"""
    try:
        print("🧪 === КОМПЛЕКСНИЙ ТЕСТ СТОВПЧАСТИХ ГРАФІКІВ ===")
        
        from handlers.callback_handler import handle_callback
        from handlers.analytics_handler import show_chart_period_selection
        
        print("\n1️⃣ Тест: chart_type_bar → прямий перехід до вибору періоду")
        
        # Мокаємо всі необхідні компоненти
        with patch('handlers.callback_handler.get_user') as mock_get_user, \
             patch('handlers.callback_handler.show_chart_period_selection') as mock_show_period:
            
            # Налаштовуємо мок користувача
            mock_user = Mock()
            mock_user.id = 12345
            mock_get_user.return_value = mock_user
            
            # Налаштовуємо мок функції
            mock_show_period.return_value = None
            
            # Створюємо мок update та context для chart_type_bar
            update = Mock()
            update.effective_user = Mock()
            update.effective_user.id = 12345
            
            query = Mock()
            query.data = "chart_type_bar"
            query.answer = AsyncMock()
            update.callback_query = query
            
            context = Mock()
            context.user_data = {}
            
            # Викликаємо обробник
            await handle_callback(update, context)
            
            # Перевіряємо виклик show_chart_period_selection
            mock_show_period.assert_called_once_with(query, context, "bar", "comparison")
            print("✅ chart_type_bar викликає show_chart_period_selection з правильними параметрами")
        
        print("\n2️⃣ Тест: Структура кнопок у меню вибору періоду для стовпчастих графіків")
        
        # Тестуємо саму функцію show_chart_period_selection
        query_test = Mock()
        query_test.edit_message_text = AsyncMock()
        context_test = Mock()
        context_test.user_data = {}
        
        await show_chart_period_selection(query_test, context_test, "bar", "comparison")
        
        # Аналізуємо виклик
        call_args = query_test.edit_message_text.call_args
        reply_markup = call_args.kwargs.get('reply_markup')
        keyboard = reply_markup.inline_keyboard
        
        # Перевіряємо структуру
        assert len(keyboard) == 2, f"Очікувалося 2 рядки, отримано {len(keyboard)}"
        
        # Перший рядок: Місяць, Тиждень
        first_row = keyboard[0]
        assert len(first_row) == 2, "Перший рядок повинен містити 2 кнопки"
        assert "Місяць" in first_row[0].text
        assert "Тиждень" in first_row[1].text
        assert first_row[0].callback_data == "generate_chart_bar_comparison_month"
        assert first_row[1].callback_data == "generate_chart_bar_comparison_week"
        
        # Другий рядок: До графіків (не до типу даних!)
        second_row = keyboard[1]
        assert len(second_row) == 1, "Другий рядок повинен містити 1 кнопку"
        assert "графіків" in second_row[0].text.lower()
        assert second_row[0].callback_data == "analytics_charts"
        
        print("✅ Структура кнопок правильна: [Місяць, Тиждень] + [До графіків]")
        
        print("\n3️⃣ Тест: Кругові діаграми залишилися без змін")
        
        # Перевіряємо, що кругові діаграми все ще працюють по-старому
        with patch('handlers.callback_handler.get_user') as mock_get_user, \
             patch('handlers.callback_handler.show_chart_data_type_selection') as mock_show_data_type:
            
            mock_user = Mock()
            mock_user.id = 12345
            mock_get_user.return_value = mock_user
            mock_show_data_type.return_value = None
            
            update = Mock()
            update.effective_user = Mock()
            update.effective_user.id = 12345
            
            query = Mock()
            query.data = "chart_type_pie"
            query.answer = AsyncMock()
            update.callback_query = query
            
            context = Mock()
            context.user_data = {}
            
            await handle_callback(update, context)
            
            # Перевіряємо, що для кругових діаграм викликається show_chart_data_type_selection
            mock_show_data_type.assert_called_once_with(query, context, "pie")
            print("✅ Кругові діаграми все ще показують вибір типу даних")
        
        print("\n4️⃣ Тест: Навігація кнопки 'Назад' для кругових діаграм")
        
        # Тестуємо кругові діаграми
        query_pie = Mock()
        query_pie.edit_message_text = AsyncMock()
        context_pie = Mock()
        context_pie.user_data = {}
        
        await show_chart_period_selection(query_pie, context_pie, "pie", "expenses")
        
        call_args = query_pie.edit_message_text.call_args
        reply_markup = call_args.kwargs.get('reply_markup')
        keyboard = reply_markup.inline_keyboard
        
        # Для кругових діаграм кнопка "Назад" повинна вести до типу даних
        back_button = keyboard[1][0]
        assert "типу даних" in back_button.text.lower()
        assert back_button.callback_data == "chart_type_pie"
        
        print("✅ Кругові діаграми: кнопка 'Назад' веде до вибору типу даних")
        
        print("\n🎉 === ВСІ ТЕСТИ ПРОЙШЛИ УСПІШНО! ===")
        print("\n📊 Підсумок змін:")
        print("• Стовпчасті графіки: прямий перехід до вибору періоду")
        print("• Автоматичний тип даних 'comparison' для стовпчастих графіків")
        print("• Правильна навігація кнопки 'Назад'")
        print("• Кругові діаграми залишилися без змін")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка в комплексному тесті: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Запуск комплексного тесту"""
    print("🧪 Запуск комплексного тесту стовпчастих графіків...")
    
    result = await test_complete_workflow()
    
    if result:
        print("\n🎉 КОМПЛЕКСНИЙ ТЕСТ УСПІШНИЙ!")
        print("🚀 Зміни готові до використання!")
    else:
        print("\n❌ КОМПЛЕКСНИЙ ТЕСТ НЕ ПРОЙШОВ!")

if __name__ == "__main__":
    asyncio.run(main())
