#!/usr/bin/env python3
"""
Тест функції редагування дати транзакції
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta

def test_date_editing_functionality():
    """Тестує нову функціональність редагування дати"""
    print("=== Тест функціональності редагування дати ===\n")
    
    # Тестуємо різні варіанти дат
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    day_before_yesterday = today - timedelta(days=2)
    
    print("📅 Доступні швидкі варіанти дат:")
    print(f"• Сьогодні: {today.strftime('%d.%m.%Y')}")
    print(f"• Вчора: {yesterday.strftime('%d.%m.%Y')}")
    print(f"• Позавчора: {day_before_yesterday.strftime('%d.%m.%Y')}")
    print()
    
    # Тестуємо парсинг дати з введення користувача
    test_dates = [
        "25.06.2025",
        "01.01.2025", 
        "15.12.2024",
        "invalid_date",
        "32.13.2025",  # неіснуюча дата
        "25.06.2026"   # майбутня дата
    ]
    
    print("🧪 Тестування парсингу дат:")
    for date_str in test_dates:
        try:
            date_parts = date_str.strip().split('.')
            if len(date_parts) != 3:
                raise ValueError("Неправильний формат")
            
            day, month, year = map(int, date_parts)
            new_date = datetime(year, month, day)
            
            if new_date.date() > datetime.now().date():
                print(f"❌ {date_str} - дата в майбутньому")
            else:
                print(f"✅ {date_str} - коректна дата: {new_date.strftime('%d.%m.%Y')}")
                
        except (ValueError, TypeError):
            print(f"❌ {date_str} - неправильний формат")
    
    print(f"\n📋 Callback'и, які тепер підтримуються:")
    print(f"• edit_date_{{transaction_id}} - відкриває меню редагування дати")
    print(f"• set_date_today_{{transaction_id}} - встановлює сьогоднішню дату")
    print(f"• set_date_yesterday_{{transaction_id}} - встановлює вчорашню дату")
    print(f"• set_date_day_before_yesterday_{{transaction_id}} - встановлює позавчорашню дату")
    print(f"• set_date_manual_{{transaction_id}} - відкриває ручне введення дати")
    
    print(f"\n=== Тест завершено ===")

if __name__ == "__main__":
    test_date_editing_functionality()
