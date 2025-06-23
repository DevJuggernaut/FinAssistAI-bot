#!/usr/bin/env python3
"""
Тест для перевірки виправлених імпортів
"""

def test_imports():
    """Тестуємо, що всі імпорти працюють правильно"""
    print("🔄 Тестуємо імпорти...")
    
    try:
        # Тестуємо імпорт callback_handler
        from handlers.callback_handler import handle_callback
        print("✅ callback_handler імпортується без помилок")
        
        # Тестуємо імпорт analytics_handler
        from handlers.analytics_handler import (
            show_analytics_main_menu, generate_pdf_report, 
            show_chart_data_type_selection, generate_simple_chart
        )
        print("✅ analytics_handler імпортується без помилок")
        
        # Тестуємо основний bot.py
        import bot
        print("✅ bot.py імпортується без помилок")
        
        print("\n🎉 Всі імпорти працюють коректно!")
        return True
        
    except ImportError as e:
        print(f"❌ Помилка імпорту: {e}")
        return False
    except Exception as e:
        print(f"❌ Неочікувана помилка: {e}")
        return False

def test_callback_functions():
    """Тестуємо, що функції існують та доступні"""
    print("\n🔄 Тестуємо доступність функцій...")
    
    try:
        from handlers.analytics_handler import (
            show_analytics_main_menu, 
            generate_pdf_report,
            show_chart_data_type_selection,
            show_chart_period_selection,
            generate_simple_chart
        )
        
        # Перевіряємо, що функції callable
        functions_to_check = [
            show_analytics_main_menu,
            generate_pdf_report,
            show_chart_data_type_selection,
            show_chart_period_selection,
            generate_simple_chart
        ]
        
        for func in functions_to_check:
            if callable(func):
                print(f"✅ {func.__name__} доступна")
            else:
                print(f"❌ {func.__name__} не є функцією")
                return False
        
        print("🎉 Всі функції доступні!")
        return True
        
    except Exception as e:
        print(f"❌ Помилка: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестування виправлених імпортів...\n")
    
    success1 = test_imports()
    success2 = test_callback_functions()
    
    if success1 and success2:
        print("\n✅ Всі тести пройшли успішно!")
        print("✅ Імпорти виправлені, бот готовий до роботи!")
    else:
        print("\n❌ Деякі тести не пройшли")
        exit(1)
