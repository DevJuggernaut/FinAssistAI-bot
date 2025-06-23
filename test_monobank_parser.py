#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки парсингу CSV виписки Монобанку
"""

import sys
import os
import importlib
sys.path.append('/Users/abobina/telegram_bot/FinAssistAI-bot')

# Переімпортуємо модуль для оновлення
if 'services.statement_parser' in sys.modules:
    importlib.reload(sys.modules['services.statement_parser'])

from services.statement_parser import StatementParser
import pandas as pd

def test_monobank_csv(file_path):
    """
    Тестує парсинг CSV файлу Монобанку
    """
    print(f"🔍 Тестуємо файл: {file_path}")
    
    # Спочатку подивимось на структуру файлу
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        print(f"📊 Структура файлу:")
        print(f"   Рядків: {df.shape[0]}")
        print(f"   Колонок: {df.shape[1]}")
        print(f"   Назви колонок: {df.columns.tolist()}")
        print()
        
        # Перші кілька рядків
        print("📝 Перші 3 рядки:")
        print(df.head(3).to_string())
        print()
        
    except Exception as e:
        print(f"❌ Помилка читання файлу: {e}")
        return
    
    # Тестуємо парсер
    try:
        parser = StatementParser()
        transactions = parser._parse_monobank_csv(file_path)
        
        print(f"✅ Парсинг успішний!")
        print(f"📈 Знайдено транзакцій: {len(transactions)}")
        
        if transactions:
            print("\n📋 Перші 5 транзакцій:")
            for i, transaction in enumerate(transactions[:5], 1):
                print(f"  {i}. {transaction['date']} {transaction['time']} - "
                      f"{transaction['type']} {transaction['amount']} UAH - "
                      f"{transaction['description']}")
            
            # Статистика
            income_count = sum(1 for t in transactions if t['type'] == 'income')
            expense_count = sum(1 for t in transactions if t['type'] == 'expense')
            
            total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
            total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
            
            print(f"\n📊 Статистика:")
            print(f"   Доходів: {income_count} ({total_income:.2f} UAH)")
            print(f"   Витрат: {expense_count} ({total_expense:.2f} UAH)")
            print(f"   Баланс: {total_income - total_expense:.2f} UAH")
            
    except Exception as e:
        print(f"❌ Помилка парсингу: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Тестуємо з завантаженим файлом
    csv_file = "/Users/abobina/Downloads/report_20-06-2025_16-12-17.csv"
    
    if os.path.exists(csv_file):
        test_monobank_csv(csv_file)
    else:
        print(f"❌ Файл не знайдено: {csv_file}")
