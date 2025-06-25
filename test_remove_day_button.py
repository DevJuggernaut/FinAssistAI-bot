#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для перевірки, що кнопка "День" прибрана з меню вибору періоду графіків
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from handlers.analytics_handler import show_chart_period_selection
from unittest.mock import AsyncMock, MagicMock


async def test_day_button_removed():
    """Тестуємо, що кнопка 'День' прибрана з меню вибору періоду"""
    
    # Створюємо мок об'єкти
    query = AsyncMock()
    context = MagicMock()
    
    # Мокаємо edit_message_text для перехоплення клавіатури
    def capture_keyboard(text, reply_markup, parse_mode=None):
        # Зберігаємо клавіатуру для аналізу
        capture_keyboard.last_keyboard = reply_markup.inline_keyboard
        return AsyncMock()
    
    query.edit_message_text = capture_keyboard
    query.data = "chart_period_pie_expenses"
    
    # Мокаємо користувача
    query.from_user.id = 12345
    
    try:
        # Викликаємо функцію
        await show_chart_period_selection(query, context, "pie", "expenses")
        
        # Перевіряємо клавіатуру
        keyboard = capture_keyboard.last_keyboard
        
        # Знаходимо всі тексти кнопок
        button_texts = []
        for row in keyboard:
            for button in row:
                button_texts.append(button.text)
        
        print("🔍 Знайдені кнопки в меню:")
        for text in button_texts:
            print(f"  - {text}")
        
        # Перевіряємо, що кнопки "День" немає
        day_buttons = [text for text in button_texts if "День" in text]
        
        if day_buttons:
            print(f"❌ ПОМИЛКА: Знайдено кнопки з 'День': {day_buttons}")
            return False
        else:
            print("✅ УСПІХ: Кнопка 'День' успішно прибрана")
        
        # Перевіряємо, що залишились тільки "Місяць" і "Тиждень"
        period_buttons = [text for text in button_texts if any(period in text for period in ["Місяць", "Тиждень"])]
        
        if len(period_buttons) == 2:
            print(f"✅ УСПІХ: Залишилось 2 кнопки періоду: {period_buttons}")
        else:
            print(f"❌ ПОМИЛКА: Неправильна кількість кнопок періоду: {period_buttons}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ ПОМИЛКА: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_both_chart_types():
    """Тестуємо обидва типи графіків (pie і bar)"""
    
    print("📊 Тестування меню для кругових діаграм...")
    result_pie = await test_day_button_removed()
    
    print("\n📊 Тестування меню для стовпчастих діаграм...")
    
    # Тестуємо стовпчасті діаграми
    query = AsyncMock()
    context = MagicMock()
    
    def capture_keyboard(text, reply_markup, parse_mode=None):
        capture_keyboard.last_keyboard = reply_markup.inline_keyboard
        capture_keyboard.last_text = text
        return AsyncMock()
    
    query.edit_message_text = capture_keyboard
    query.data = "chart_period_bar_expenses"
    query.from_user.id = 12345
    
    try:
        await show_chart_period_selection(query, context, "bar", "expenses")
        
        # Перевіряємо текст (чи не згадується "День")
        text = capture_keyboard.last_text
        if "День" in text:
            print("❌ ПОМИЛКА: Текст все ще містить згадку про 'День'")
            print(f"Проблемний текст: {text}")
            return False
        else:
            print("✅ УСПІХ: Текст не містить згадок про 'День'")
        
        # Перевіряємо клавіатуру
        keyboard = capture_keyboard.last_keyboard
        button_texts = []
        for row in keyboard:
            for button in row:
                button_texts.append(button.text)
        
        day_buttons = [text for text in button_texts if "День" in text]
        if day_buttons:
            print(f"❌ ПОМИЛКА: Знайдено кнопки з 'День' у стовпчастих діаграмах: {day_buttons}")
            return False
        else:
            print("✅ УСПІХ: Кнопка 'День' прибрана зі стовпчастих діаграм")
            
        return True
        
    except Exception as e:
        print(f"❌ ПОМИЛКА: {str(e)}")
        return False


if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("🧪 Тестування видалення кнопки 'День' з меню графіків\n")
        
        result1 = await test_day_button_removed()
        result2 = await test_both_chart_types()
        
        print(f"\n📋 Результати тестування:")
        print(f"  Кругові діаграми: {'✅ ПРОЙДЕНО' if result1 else '❌ ПРОВАЛЕНО'}")
        print(f"  Стовпчасті діаграми: {'✅ ПРОЙДЕНО' if result2 else '❌ ПРОВАЛЕНО'}")
        
        if result1 and result2:
            print(f"\n🎉 Всі тести пройдено успішно! Кнопка 'День' успішно прибрана.")
        else:
            print(f"\n💥 Деякі тести провалились!")

    asyncio.run(main())
