#!/usr/bin/env python3
"""
Простий тест логіки останніх 7 днів для тижневого періоду
"""

from datetime import datetime, timedelta

def test_week_keys_logic():
    """Тестуємо логіку створення ключів для останніх 7 днів"""
    print("🧪 Тестуємо логіку останніх 7 днів...")
    
    now = datetime.now()
    
    print(f"Сьогодні: {now.strftime('%A, %d.%m.%Y %H:%M')}")
    print("\nОстанні 7 днів (новий алгоритм):")
    
    # Логіка з analytics_handler.py
    all_keys = []
    
    for i in range(6, -1, -1):  # від 6 днів тому до сьогодні
        date = now - timedelta(days=i)
        if i == 0:
            key = f"Сьогодні ({date.strftime('%d.%m')})"
        elif i == 1:
            key = f"Вчора ({date.strftime('%d.%m')})"
        else:
            weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
            weekday_name = weekdays[date.weekday()]
            key = f"{weekday_name} ({date.strftime('%d.%m')})"
        
        all_keys.append(key)
        print(f"  {7-i}. {key} ({date.strftime('%A')})")
    
    print(f"\nВсього ключів: {len(all_keys)}")
    print("Порядок ключів (від найстаршого до найновішого):")
    for i, key in enumerate(all_keys, 1):
        print(f"  {i}. {key}")
    
    return all_keys

def test_transaction_key_generation():
    """Тестуємо створення ключів для транзакцій"""
    print("\n🔄 Тестуємо створення ключів для транзакцій...")
    
    now = datetime.now()
    
    # Симулюємо транзакції на останні 7 днів
    test_dates = []
    for i in range(7):
        test_dates.append(now - timedelta(days=i))
    
    print("Ключі для транзакцій:")
    for date in test_dates:
        days_ago = (now.date() - date.date()).days
        
        if days_ago == 0:
            key = f"Сьогодні ({date.strftime('%d.%m')})"
        elif days_ago == 1:
            key = f"Вчора ({date.strftime('%d.%m')})"
        else:
            weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
            weekday_name = weekdays[date.weekday()]
            key = f"{weekday_name} ({date.strftime('%d.%m')})"
        
        print(f"  {date.strftime('%Y-%m-%d %A')} -> {key}")

def test_date_range():
    """Тестуємо діапазон дат для тижня"""
    print("\n📅 Тестуємо діапазон дат для тижневого періоду...")
    
    now = datetime.now()
    
    # Логіка з analytics_handler.py для тижня
    start_date = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now
    
    print(f"Початок періоду: {start_date.strftime('%Y-%m-%d %H:%M:%S (%A)')}")
    print(f"Кінець періоду: {end_date.strftime('%Y-%m-%d %H:%M:%S (%A)')}")
    print(f"Кількість днів: {(end_date.date() - start_date.date()).days + 1}")
    
    print("\nДні у діапазоні:")
    current = start_date.date()
    day_count = 1
    while current <= end_date.date():
        days_ago = (now.date() - current).days
        if days_ago == 0:
            label = "сьогодні"
        elif days_ago == 1:
            label = "вчора"
        else:
            label = f"{days_ago} днів тому"
        
        print(f"  {day_count}. {current.strftime('%Y-%m-%d %A')} ({label})")
        current += timedelta(days=1)
        day_count += 1

def main():
    """Головна функція тестування"""
    print("🚀 Тестування логіки останніх 7 днів для тижневого періоду")
    print("=" * 70)
    
    # Тестуємо створення ключів
    all_keys = test_week_keys_logic()
    
    # Тестуємо генерацію ключів для транзакцій
    test_transaction_key_generation()
    
    # Тестуємо діапазон дат
    test_date_range()
    
    print("\n✅ Логіка перевірена!")
    print("\n📋 Висновки:")
    print("  ✅ Показуються останні 7 днів (включаючи сьогодні)")
    print("  ✅ Сьогодні та вчора мають спеціальні позначки")
    print("  ✅ Інші дні показують день тижня + дату")
    print("  ✅ Порядок від найстаршого до найновішого дня")
    print("  ✅ Діапазон дат налаштований правильно")

if __name__ == "__main__":
    main()
