#!/usr/bin/env python3
"""
Тест правильності днів тижня для останніх 7 днів
"""

from datetime import datetime, timedelta

def test_correct_weekdays():
    """Тестуємо правильність днів тижня"""
    print("📅 Перевірка правильності днів тижня для останніх 7 днів")
    print(f"Сьогодні: {datetime.now().strftime('%A, %d.%m.%Y')}")
    print("=" * 60)
    
    now = datetime.now()
    weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
    
    print("Останні 7 днів з правильними днями тижня:")
    
    for i in range(6, -1, -1):  # від 6 днів тому до сьогодні
        date = now - timedelta(days=i)
        weekday_name = weekdays[date.weekday()]
        key = f"{weekday_name} ({date.strftime('%d.%m')})"
        
        # Перевіряємо правильність
        real_weekday = date.strftime('%A')
        weekday_mapping = {
            'Monday': 'Пн',
            'Tuesday': 'Вт', 
            'Wednesday': 'Ср',
            'Thursday': 'Чт',
            'Friday': 'Пт',
            'Saturday': 'Сб',
            'Sunday': 'Нд'
        }
        
        expected_weekday = weekday_mapping[real_weekday]
        is_correct = weekday_name == expected_weekday
        
        status = "✅" if is_correct else "❌"
        
        print(f"  {7-i}. {key} | Реальний: {real_weekday} | {status}")
        
        if not is_correct:
            print(f"     ⚠️ ПОМИЛКА: очікували {expected_weekday}, отримали {weekday_name}")

def test_transaction_key_generation():
    """Тестуємо створення ключів для транзакцій"""
    print("\n🔄 Тестуємо створення ключів для транзакцій...")
    
    now = datetime.now()
    weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
    
    # Симулюємо транзакції на останні 7 днів
    test_dates = []
    for i in range(7):
        test_dates.append(now - timedelta(days=i))
    
    print("Ключі для транзакцій:")
    for date in test_dates:
        weekday_name = weekdays[date.weekday()]
        key = f"{weekday_name} ({date.strftime('%d.%m')})"
        
        real_weekday = date.strftime('%A')
        print(f"  {date.strftime('%Y-%m-%d %A')} -> {key}")

def main():
    """Головна функція тестування"""
    print("🚀 Тестування правильності днів тижня")
    
    # Тестуємо правильність днів тижня
    test_correct_weekdays()
    
    # Тестуємо генерацію ключів для транзакцій
    test_transaction_key_generation()
    
    print("\n✅ Тестування завершено!")
    print("\n📋 Очікувані результати:")
    print("  ✅ Всі дні тижня повинні відповідати реальним")
    print("  ✅ Сьогодні вівторок (24.06) повинен бути позначений як 'Вт (24.06)'")
    print("  ✅ Вчора понеділок (23.06) повинен бути позначений як 'Пн (23.06)'")

if __name__ == "__main__":
    main()
