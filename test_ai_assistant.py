#!/usr/bin/env python3
"""
Тестування нового AI-помічника
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Додаємо кореневий каталог проекту до шляху
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_operations import get_user, get_user_transactions
from database.models import TransactionType
from handlers.ai_assistant_handler import (
    generate_personal_advice, 
    generate_financial_forecast, 
    answer_custom_question
)
from services.openai_service import OpenAIService
from database.config import OPENAI_API_KEY

async def test_ai_assistant():
    """Тестує AI-помічника"""
    print("🤖 Тестування AI-помічника...")
    
    # Перевіряємо, чи є OpenAI API ключ
    if not OPENAI_API_KEY:
        print("❌ OpenAI API ключ не знайдено в змінних середовища")
        print("💡 Додайте OPENAI_API_KEY в .env файл")
        return
    
    print(f"✅ OpenAI API ключ знайдено: {OPENAI_API_KEY[:10]}...")
    
    # Створюємо тестового користувача
    class TestUser:
        def __init__(self):
            self.id = 123456
            self.monthly_budget = 15000
            self.currency = "UAH"
    
    # Створюємо тестові транзакції
    test_transactions = [
        {
            'amount': 500.0,
            'category': 'Їжа',
            'type': 'expense',
            'date': (datetime.now() - timedelta(days=5)).isoformat(),
            'description': 'Супермаркет'
        },
        {
            'amount': 200.0,
            'category': 'Транспорт',
            'type': 'expense',
            'date': (datetime.now() - timedelta(days=3)).isoformat(),
            'description': 'Метро'
        },
        {
            'amount': 1200.0,
            'category': 'Комунальні послуги',
            'type': 'expense',
            'date': (datetime.now() - timedelta(days=10)).isoformat(),
            'description': 'Електроенергія'
        },
        {
            'amount': 25000.0,
            'category': 'Зарплата',
            'type': 'income',
            'date': (datetime.now() - timedelta(days=1)).isoformat(),
            'description': 'Місячна зарплата'
        }
    ]
    
    user = TestUser()
    
    print("\n💡 Тестування персональної поради...")
    try:
        advice = await generate_personal_advice(user, test_transactions)
        print("✅ Порада отримана:")
        print(advice)
    except Exception as e:
        print(f"❌ Помилка при отриманні поради: {e}")
    
    print("\n🔮 Тестування фінансового прогнозу...")
    try:
        forecast = await generate_financial_forecast(user, test_transactions)
        print("✅ Прогноз отриманий:")
        print(forecast)
    except Exception as e:
        print(f"❌ Помилка при створенні прогнозу: {e}")
    
    print("\n❓ Тестування кастомного питання...")
    try:
        question = "Скільки я витрачаю на їжу щомісяця?"
        answer = await answer_custom_question(question, user, test_transactions)
        print("✅ Відповідь отримана:")
        print(answer)
    except Exception as e:
        print(f"❌ Помилка при відповіді на питання: {e}")
    
    print("\n🎉 Тестування завершено!")

if __name__ == "__main__":
    asyncio.run(test_ai_assistant())
