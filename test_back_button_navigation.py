#!/usr/bin/env python3

"""
Тест для перевірки правильної навігації кнопки "Назад" у меню вибору періоду
"""

import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_back_button_navigation():
    """Тест правильної навігації кнопки 'Назад' у меню вибору періоду"""
    try:
        print("=== Тест навігації кнопки 'Назад' у меню вибору періоду ===")
        
        from handlers.analytics_handler import show_chart_period_selection
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        
        # Тест для стовпчастих графіків
        print("\n📊 Тестуємо стовпчасті графіки...")
        
        # Мокаємо query
        query_bar = Mock()
        query_bar.edit_message_text = AsyncMock()
        context_bar = Mock()
        context_bar.user_data = {}  # Додаємо user_data як словник
        
        # Викликаємо функцію для стовпчастого графіку
        await show_chart_period_selection(query_bar, context_bar, "bar", "comparison")
        
        # Перевіряємо, що функція була викликана
        query_bar.edit_message_text.assert_called_once()
        call_args = query_bar.edit_message_text.call_args
        
        # Отримуємо reply_markup
        reply_markup = call_args.kwargs.get('reply_markup')
        if reply_markup:
            # Перевіряємо структуру кнопок
            keyboard = reply_markup.inline_keyboard
            
            # Повинно бути 2 рядки: [Місяць, Тиждень] та [До графіків]
            assert len(keyboard) == 2, f"Очікувалося 2 рядки кнопок, отримано {len(keyboard)}"
            
            # Перевіряємо перший рядок (Місяць, Тиждень)
            first_row = keyboard[0]
            assert len(first_row) == 2, "Перший рядок повинен містити 2 кнопки"
            
            month_button = first_row[0]
            week_button = first_row[1]
            assert "Місяць" in month_button.text, "Перша кнопка повинна бути 'Місяць'"
            assert "Тиждень" in week_button.text, "Друга кнопка повинна бути 'Тиждень'"
            
            # Перевіряємо другий рядок (Назад)
            second_row = keyboard[1]
            assert len(second_row) == 1, "Другий рядок повинен містити 1 кнопку"
            
            back_button = second_row[0]
            assert "графіків" in back_button.text.lower(), f"Кнопка 'Назад' для стовпчастих графіків повинна містити 'графіків', отримано: {back_button.text}"
            assert back_button.callback_data == "analytics_charts", f"Callback для стовпчастих графіків повинен бути 'analytics_charts', отримано: {back_button.callback_data}"
            
            print("✅ Стовпчасті графіки: кнопка 'Назад' веде до вибору графіків")
        
        # Тест для кругових діаграм
        print("\n🍩 Тестуємо кругові діаграми...")
        
        # Мокаємо query для кругової діаграми
        query_pie = Mock()
        query_pie.edit_message_text = AsyncMock()
        context_pie = Mock()
        context_pie.user_data = {}  # Додаємо user_data як словник
        
        # Викликаємо функцію для кругової діаграми
        await show_chart_period_selection(query_pie, context_pie, "pie", "expenses")
        
        # Перевіряємо, що функція була викликана
        query_pie.edit_message_text.assert_called_once()
        call_args = query_pie.edit_message_text.call_args
        
        # Отримуємо reply_markup
        reply_markup = call_args.kwargs.get('reply_markup')
        if reply_markup:
            # Перевіряємо структуру кнопок
            keyboard = reply_markup.inline_keyboard
            
            # Повинно бути 2 рядки: [Місяць, Тиждень] та [До типу даних]
            assert len(keyboard) == 2, f"Очікувалося 2 рядки кнопок, отримано {len(keyboard)}"
            
            # Перевіряємо другий рядок (Назад)
            second_row = keyboard[1]
            assert len(second_row) == 1, "Другий рядок повинен містити 1 кнопку"
            
            back_button = second_row[0]
            assert "типу даних" in back_button.text.lower(), f"Кнопка 'Назад' для кругових діаграм повинна містити 'типу даних', отримано: {back_button.text}"
            assert back_button.callback_data == "chart_type_pie", f"Callback для кругових діаграм повинен бути 'chart_type_pie', отримано: {back_button.callback_data}"
            
            print("✅ Кругові діаграми: кнопка 'Назад' веде до вибору типу даних")
        
        print("\n🎉 Тест навігації пройшов успішно!")
        print("📊 Стовпчасті графіки: Назад → До графіків")
        print("🍩 Кругові діаграми: Назад → До типу даних")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка в тесті: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Запуск тесту"""
    print("🧪 Запуск тесту навігації кнопки 'Назад'...")
    
    result = await test_back_button_navigation()
    
    if result:
        print("\n🎉 Тест пройшов успішно!")
        print("\n📋 Підсумок навігації:")
        print("• Стовпчасті графіки: chart_type_bar → period_selection → analytics_charts")
        print("• Кругові діаграми: chart_type_pie → data_type_selection → period_selection → chart_type_pie")
    else:
        print("\n❌ Тест не пройшов!")

if __name__ == "__main__":
    asyncio.run(main())
