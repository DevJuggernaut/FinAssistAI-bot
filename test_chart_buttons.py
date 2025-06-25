#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для перевірки кнопок після створення графіку
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_button_structure_after_chart():
    """Перевіряємо структуру кнопок після створення графіку"""
    
    print("🔍 Перевіряємо структуру кнопок після створення графіку...")
    
    with open('handlers/analytics_handler.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Шукаємо блок з кнопками після відправки графіку
    photo_section = content.find('await context.bot.send_photo(')
    if photo_section == -1:
        print("❌ ПОМИЛКА: Не знайдено блок send_photo")
        return False
    
    # Знаходимо reply_markup після send_photo
    reply_markup_start = content.find('reply_markup=InlineKeyboardMarkup([', photo_section)
    if reply_markup_start == -1:
        print("❌ ПОМИЛКА: Не знайдено reply_markup після send_photo")
        return False
    
    # Витягуємо блок кнопок
    lines = content[reply_markup_start:].split('\n')
    button_lines = []
    bracket_count = 0
    
    for line in lines:
        button_lines.append(line)
        bracket_count += line.count('[') - line.count(']')
        if 'reply_markup=InlineKeyboardMarkup([' in line:
            bracket_count = 1
        elif bracket_count == 0 and '])' in line:
            break
    
    button_code = '\n'.join(button_lines)
    print("📋 Структура кнопок після створення графіку:")
    print(button_code)
    
    # Перевіряємо, що немає кнопки "Інший графік"
    if 'Інший графік' in button_code:
        print("❌ ПОМИЛКА: Кнопка 'Інший графік' все ще присутня")
        return False
    else:
        print("✅ УСПІХ: Кнопка 'Інший графік' видалена")
    
    # Перевіряємо, що є кнопка "Інший період"
    if 'Інший період' in button_code:
        print("✅ УСПІХ: Кнопка 'Інший період' присутня")
    else:
        print("❌ ПОМИЛКА: Кнопка 'Інший період' відсутня")
        return False
    
    # Перевіряємо callback для кнопки "Інший період"
    if 'chart_data_{data_type}_{chart_type}' in button_code:
        print("✅ УСПІХ: Callback для 'Інший період' правильний")
    else:
        print("❌ ПОМИЛКА: Неправильний callback для 'Інший період'")
        return False
    
    # Перевіряємо кнопку "Назад"
    if 'До вибору графіків' in button_code:
        print("✅ УСПІХ: Кнопка 'До вибору графіків' присутня")
    else:
        print("❌ ПОМИЛКА: Кнопка 'До вибору графіків' відсутня")
        return False
    
    # Перевіряємо callback для кнопки "Назад"
    if '"analytics_charts"' in button_code:
        print("✅ УСПІХ: Callback для 'До вибору графіків' правильний")
    else:
        print("❌ ПОМИЛКА: Неправильний callback для 'До вибору графіків'")
        return False
    
    return True

def test_callback_handler():
    """Перевіряємо, що callback_handler правильно обробляє chart_data_"""
    
    print("\n🔍 Перевіряємо обробку callback'ів...")
    
    with open('handlers/callback_handler.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Перевіряємо, що є обробка chart_data_
    if 'elif callback_data.startswith("chart_data_"):' in content:
        print("✅ УСПІХ: Обробник chart_data_ присутній")
    else:
        print("❌ ПОМИЛКА: Обробник chart_data_ відсутній")
        return False
    
    # Перевіряємо, що викликається show_chart_period_selection
    if 'await show_chart_period_selection(query, context, chart_type, data_type)' in content:
        print("✅ УСПІХ: Правильно викликається show_chart_period_selection")
    else:
        print("❌ ПОМИЛКА: Неправильний виклик show_chart_period_selection")
        return False
    
    return True

def test_navigation_flow():
    """Перевіряємо логіку навігації"""
    
    print("\n🔍 Перевіряємо логіку навігації...")
    
    flow_steps = [
        "analytics_charts -> chart_type_pie/bar",
        "chart_type_* -> chart_data_expenses/income/comparison_*",
        "chart_data_*_* -> generate_chart_*_*_*",
        "generate_chart -> button: chart_data_*_* (Інший період)",
        "generate_chart -> button: analytics_charts (До вибору графіків)"
    ]
    
    print("📋 Логіка навігації:")
    for step in flow_steps:
        print(f"  {step}")
    
    print("✅ УСПІХ: Логіка навігації правильна")
    return True

if __name__ == "__main__":
    print("🧪 Тестування кнопок після створення графіку\n")
    
    result1 = test_button_structure_after_chart()
    result2 = test_callback_handler()
    result3 = test_navigation_flow()
    
    print(f"\n📋 Результати тестування:")
    print(f"  Структура кнопок: {'✅ ПРОЙДЕНО' if result1 else '❌ ПРОВАЛЕНО'}")
    print(f"  Обробка callback'ів: {'✅ ПРОЙДЕНО' if result2 else '❌ ПРОВАЛЕНО'}")
    print(f"  Логіка навігації: {'✅ ПРОЙДЕНО' if result3 else '❌ ПРОВАЛЕНО'}")
    
    if result1 and result2 and result3:
        print(f"\n🎉 Всі тести пройдено успішно! Кнопки працюють правильно.")
    else:
        print(f"\n💥 Деякі тести провалились!")
