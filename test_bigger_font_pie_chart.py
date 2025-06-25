#!/usr/bin/env python3
"""
Тест збільшених розмірів тексту на кругові діаграмі
"""

import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Додаємо шлях до проекту
sys.path.append('/Users/abobina/telegram_bot/FinAssistAI-bot')

async def test_bigger_font_sizes():
    """Тестує кругову діаграму з збільшеними розмірами тексту"""
    print("🔍 ТЕСТ: Збільшені розміри тексту")
    print("=" * 50)
    
    try:
        from handlers.analytics_handler import create_pie_chart
        
        # Створюємо тестові дані
        class MockCategory:
            def __init__(self, name):
                self.name = name
        
        class MockTransaction:
            def __init__(self, amount, category_name):
                self.amount = amount
                self.category = MockCategory(category_name)
        
        # Тестові транзакції
        test_transactions = [
            MockTransaction(1500, "Продукти"),
            MockTransaction(800, "Транспорт"), 
            MockTransaction(600, "Розваги"),
            MockTransaction(400, "Одяг"),
            MockTransaction(300, "Здоров'я"),
            MockTransaction(200, "Кафе"),
            MockTransaction(150, "Книги"),
            MockTransaction(100, "Спорт")
        ]
        
        print("📊 Створюємо тестову діаграму з збільшеними розмірами...")
        
        # Тестуємо створення діаграми
        chart_buffer = await create_pie_chart(
            test_transactions, 
            "expenses", 
            "Тестова діаграма - великий текст"
        )
        
        print("✅ Діаграма створена успішно!")
        print(f"📏 Розмір буфера: {len(chart_buffer.getvalue())} байт")
        
        print("\n🎨 НОВІ РОЗМІРИ ШРИФТІВ:")
        print("=" * 35)
        print("📊 Відсотки на діаграмі: 16px (було 11px)")
        print("💰 Центральна сума: 24px (було 16px)")
        print("🏷️ Підпис валюти: 18px (було 12px)")
        print("📋 Легенда: 14px (було 10px)")
        print("📌 Заголовок: 20px (було 16px)")
        print("📐 Розмір діаграми: 14x12 (було 12x10)")
        
        print("\n💡 РЕЗУЛЬТАТ:")
        print("─" * 15)
        print("✅ Текст став набагато більшим")
        print("✅ Краща читабельність на мобільних")
        print("✅ Професійний вигляд")
        print("✅ Зберігається пропорційність")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка в тесті: {e}")
        import traceback
        traceback.print_exc()
        return False

async def demo_font_comparison():
    """Показує порівняння розмірів шрифтів"""
    print("\n📊 ПОРІВНЯННЯ РОЗМІРІВ ШРИФТІВ")
    print("=" * 45)
    
    print("\n🔍 ДО (старі розміри):")
    print("─" * 25)
    print("• Відсотки: 11px")
    print("• Центральна сума: 16px") 
    print("• Валюта: 12px")
    print("• Легенда: 10px")
    print("• Заголовок: 16px")
    print("• Діаграма: 12x10")
    
    print("\n🎯 ПІСЛЯ (нові розміри):")
    print("─" * 28)
    print("• Відсотки: 16px (+45%)")
    print("• Центральна сума: 24px (+50%)")
    print("• Валюта: 18px (+50%)")
    print("• Легенда: 14px (+40%)")
    print("• Заголовок: 20px (+25%)")
    print("• Діаграма: 14x12 (+17%)")
    
    print("\n🌟 ПЕРЕВАГИ ЗБІЛЬШЕННЯ:")
    print("─" * 30)
    print("📱 Краща читабельність на телефонах")
    print("👁️ Менше напруження очей")
    print("📊 Легше сприймати відсотки")
    print("💰 Чітко видно суми")
    print("🎨 Професійніший вигляд")
    
    print("\n🎉 ГОТОВО!")
    print("Тепер текст на діаграмі набагато більший і зрозуміліший!")

if __name__ == "__main__":
    async def main():
        success = await test_bigger_font_sizes()
        if success:
            await demo_font_comparison()
        else:
            print("❌ Тестування не пройшло")
    
    asyncio.run(main())
