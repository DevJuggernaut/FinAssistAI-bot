#!/usr/bin/env python3
"""
Демонстрація роботи нового AI-помічника
"""

import asyncio
import sys
import os
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.ai_assistant_handler import show_ai_assistant_menu

async def demo_ai_assistant():
    """Демонстрація AI-помічника"""
    
    print("🤖 === ДЕМОНСТРАЦІЯ AI-ПОМІЧНИКА ===\n")
    
    # Створюємо mock об'єкти для демонстрації
    class MockQuery:
        def __init__(self):
            self.from_user = MagicMock()
            self.from_user.id = 123456
            
        async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
            print("📱 ПОВІДОМЛЕННЯ В ТЕЛЕГРАМ:")
            print("=" * 50)
            print(text)
            print("=" * 50)
            
            if reply_markup:
                print("\n🔘 КНОПКИ:")
                for i, row in enumerate(reply_markup.inline_keyboard):
                    for j, button in enumerate(row):
                        print(f"  [{button.text}] → {button.callback_data}")
                print()
    
    mock_query = MockQuery()
    mock_context = MagicMock()
    
    print("1️⃣ Показуємо головне меню AI-помічника:")
    print("-" * 50)
    
    try:
        await show_ai_assistant_menu(mock_query, mock_context)
    except Exception as e:
        print(f"Демонстрація завершена. (Очікувана помилка: {e})")
    
    print("\n✨ ОСОБЛИВОСТІ AI-ПОМІЧНИКА:")
    print("📊 Аналізує ваші реальні транзакції")
    print("🇺🇦 Відповідає українською мовою") 
    print("🎯 Дає персоналізовані поради")
    print("🔮 Створює прогнози витрат")
    print("❓ Відповідає на кастомні питання")
    print("🛡️ Має fallback на статичні поради")
    
    print("\n🚀 ДЛЯ ПОВНОЦІННОЇ РОБОТИ:")
    print("1. Додайте OPENAI_API_KEY в .env файл")
    print("2. Запустіть бота: python bot.py")
    print("3. В Телеграмі: /start → 🤖 AI-помічник")

if __name__ == "__main__":
    asyncio.run(demo_ai_assistant())
