#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простий тест для перевірки, що кнопка "День" прибрана з коду
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_day_button_removed_from_code():
    """Перевіряємо, що кнопка 'День' прибрана з коду"""
    
    print("🔍 Перевіряємо analytics_handler.py на наявність кнопок 'День'...")
    
    with open('handlers/analytics_handler.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Шукаємо згадки про кнопку "День" у callback_data
    day_button_patterns = [
        'InlineKeyboardButton("🗓 День"',
        '"generate_chart_pie_expenses_day"',
        '"generate_chart_pie_income_day"', 
        '"generate_chart_bar_expenses_day"',
        '"generate_chart_bar_income_day"',
        'callback_data=f"generate_chart_{chart_type}_{data_type}_day"'
    ]
    
    found_issues = []
    for pattern in day_button_patterns:
        if pattern in content:
            found_issues.append(pattern)
    
    if found_issues:
        print("❌ ПОМИЛКА: Знайдено згадки про кнопку 'День':")
        for issue in found_issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ УСПІХ: Кнопка 'День' прибрана з коду")
    
    # Перевіряємо, що в тексті меню не згадується "День" для графіків
    day_text_patterns = [
        '🗓 **День** — сьогодні',
        '🗓 **День** — сьогоднішні витрати'
    ]
    
    found_text_issues = []
    for pattern in day_text_patterns:
        if pattern in content:
            found_text_issues.append(pattern)
    
    if found_text_issues:
        print("❌ ПОМИЛКА: Знайдено згадки про 'День' у тексті:")
        for issue in found_text_issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ УСПІХ: Згадки про 'День' прибрані з тексту меню")
    
    # Перевіряємо, що обробка періоду "day" видалена
    day_logic_patterns = [
        'if period == "day":',
        'period == "day"'
    ]
    
    day_logic_count = 0
    for pattern in day_logic_patterns:
        day_logic_count += content.count(pattern)
    
    if day_logic_count > 0:
        print(f"⚠️  УВАГА: Знайдено {day_logic_count} згадок обробки періоду 'day'")
        print("   Це може бути нормально, якщо вони в інших контекстах")
    else:
        print("✅ УСПІХ: Обробка періоду 'day' видалена")
    
    return len(found_issues) == 0 and len(found_text_issues) == 0


def test_keyboard_structure():
    """Перевіряємо структуру клавіатури в коді"""
    
    print("\n🔍 Перевіряємо структуру клавіатури...")
    
    with open('handlers/analytics_handler.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Знаходимо блок з клавіатурою для вибору періоду
    search_text = 'InlineKeyboardButton("📅 Місяць"'
    keyboard_start = content.find(search_text)
    if keyboard_start == -1:
        print("❌ ПОМИЛКА: Не знайдено блок клавіатури для вибору періоду")
        return False
    
    # Знаходимо початок блоку keyboard = [
    lines_before = content[:keyboard_start].split('\n')
    keyboard_line_start = -1
    for i in range(len(lines_before) - 1, -1, -1):
        if 'keyboard = [' in lines_before[i]:
            keyboard_line_start = i
            break
    
    if keyboard_line_start == -1:
        print("❌ ПОМИЛКА: Не знайдено початок блоку клавіатури")
        return False
    
    # Знаходимо кінець блоку клавіатури
    all_lines = content.split('\n')
    keyboard_lines = []
    bracket_count = 0
    
    for i in range(keyboard_line_start, len(all_lines)):
        line = all_lines[i]
        keyboard_lines.append(line)
        bracket_count += line.count('[') - line.count(']')
        if 'keyboard = [' in line:
            bracket_count = 1  # початковий рахунок
        elif bracket_count == 0 and line.strip().endswith(']'):
            break
    
    keyboard_code = '\n'.join(keyboard_lines)
    print("📋 Структура клавіатури для вибору періоду:")
    print(keyboard_code)
    
    # Перевіряємо, що є кнопки Місяць і Тиждень
    if 'InlineKeyboardButton("📅 Місяць"' in keyboard_code and 'InlineKeyboardButton("📆 Тиждень"' in keyboard_code:
        print("✅ УСПІХ: Кнопки 'Місяць' і 'Тиждень' присутні")
    else:
        print("❌ ПОМИЛКА: Не всі потрібні кнопки присутні")
        return False
    
    if 'InlineKeyboardButton("🗓 День"' not in keyboard_code:
        print("✅ УСПІХ: Кнопка 'День' відсутня")
    else:
        print("❌ ПОМИЛКА: Кнопка 'День' все ще присутня")
        return False
    
    # Перевіряємо, що клавіатура має правильну структуру (2 рядки)
    keyboard_rows = keyboard_code.count('],[')
    if keyboard_rows == 1:  # 2 рядки = 1 роздільник
        print("✅ УСПІХ: Клавіатура має правильну структуру (2 рядки)")
    else:
        print(f"⚠️  УВАГА: Клавіатура має {keyboard_rows + 1} рядків (очікувалось 2)")
    
    return True


if __name__ == "__main__":
    print("🧪 Тестування видалення кнопки 'День' з коду\n")
    
    result1 = test_day_button_removed_from_code()
    result2 = test_keyboard_structure()
    
    print(f"\n📋 Результати тестування:")
    print(f"  Видалення з коду: {'✅ ПРОЙДЕНО' if result1 else '❌ ПРОВАЛЕНО'}")
    print(f"  Структура клавіатури: {'✅ ПРОЙДЕНО' if result2 else '❌ ПРОВАЛЕНО'}")
    
    if result1 and result2:
        print(f"\n🎉 Всі тести пройдено успішно! Кнопка 'День' успішно прибрана.")
    else:
        print(f"\n💥 Деякі тести провалились!")
