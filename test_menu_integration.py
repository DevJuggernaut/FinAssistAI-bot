#!/usr/bin/env python3
"""
Швидкий тест нового AI-помічника меню
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from handlers.main_menu import create_main_menu_keyboard

def test_main_menu():
    """Тестує нове головне меню"""
    print("🏠 Тестування нового головного меню...")
    
    keyboard = create_main_menu_keyboard()
    
    print("✅ Кнопки головного меню:")
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"  - {button.text} (callback: {button.callback_data})")
    
    print("\n🤖 Перевіряємо, чи є кнопка AI-помічника...")
    ai_button_found = False
    for row in keyboard.inline_keyboard:
        for button in row:
            if "AI-помічник" in button.text:
                ai_button_found = True
                print(f"✅ Знайдено: {button.text} → {button.callback_data}")
    
    if not ai_button_found:
        print("❌ Кнопка AI-помічника не знайдена!")
    else:
        print("🎉 Успішно! Нова кнопка AI-помічника додана в головне меню")

if __name__ == "__main__":
    test_main_menu()
