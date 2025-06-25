#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простий тест для перевірки кнопок у функції generate_simple_chart
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_chart_buttons_after_generation():
    """Перевіряємо кнопки після генерації графіку"""
    
    print("🔍 Перевіряємо кнопки після генерації графіку...")
    
    with open('handlers/analytics_handler.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Шукаємо функцію generate_simple_chart
    func_start = content.find('async def generate_simple_chart(')
    if func_start == -1:
        print("❌ ПОМИЛКА: Функція generate_simple_chart не знайдена")
        return False
    
    # Знаходимо context.bot.send_photo в цій функції
    func_content = content[func_start:]
    send_photo_start = func_content.find('await context.bot.send_photo(')
    if send_photo_start == -1:
        print("❌ ПОМИЛКА: send_photo не знайдено в generate_simple_chart")
        return False
    
    # Витягуємо блок кнопок
    photo_section = func_content[send_photo_start:]
    lines = photo_section.split('\n')
    
    button_lines = []
    in_reply_markup = False
    bracket_count = 0
    
    for line in lines:
        if 'reply_markup=InlineKeyboardMarkup([' in line:
            in_reply_markup = True
            bracket_count = 1
        
        if in_reply_markup:
            button_lines.append(line)
            bracket_count += line.count('[') - line.count(']')
            if bracket_count == 0 and '])' in line:
                break
    
    button_code = '\n'.join(button_lines)
    print("📋 Кнопки після генерації графіку:")
    print(button_code)
    
    # Перевірки
    checks = []
    
    # 1. Немає кнопки "Інший графік"
    if 'Інший графік' not in button_code:
        checks.append("✅ Кнопка 'Інший графік' відсутня")
    else:
        checks.append("❌ Кнопка 'Інший графік' все ще присутня")
    
    # 2. Є кнопка "Інший період"
    if 'Інший період' in button_code:
        checks.append("✅ Кнопка 'Інший період' присутня")
    else:
        checks.append("❌ Кнопка 'Інший період' відсутня")
    
    # 3. Правильний callback для "Інший період"
    if 'chart_data_{data_type}_{chart_type}' in button_code:
        checks.append("✅ Callback для 'Інший період' правильний")
    else:
        checks.append("❌ Неправильний callback для 'Інший період'")
    
    # 4. Є кнопка "До вибору графіків"
    if 'До вибору графіків' in button_code:
        checks.append("✅ Кнопка 'До вибору графіків' присутня")
    else:
        checks.append("❌ Кнопка 'До вибору графіків' відсутня")
    
    # 5. Правильний callback для "До вибору графіків"
    if '"analytics_charts"' in button_code:
        checks.append("✅ Callback для 'До вибору графіків' правильний")
    else:
        checks.append("❌ Неправильний callback для 'До вибору графіків'")
    
    # Виводимо результати
    print("\n📋 Результати перевірки:")
    all_good = True
    for check in checks:
        print(f"  {check}")
        if "❌" in check:
            all_good = False
    
    return all_good

if __name__ == "__main__":
    print("🧪 Тестування кнопок після генерації графіку\n")
    
    result = test_chart_buttons_after_generation()
    
    if result:
        print(f"\n🎉 Тест пройдено успішно!")
        print("✅ Кнопка 'Інший графік' видалена")
        print("✅ Кнопка 'Інший період' працює правильно")
        print("✅ Кнопка 'До вибору графіків' працює правильно")
    else:
        print(f"\n💥 Тест провалився!")
