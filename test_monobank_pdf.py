#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки парсингу PDF виписки Монобанку
"""

import sys
import os
import importlib
sys.path.append('/Users/abobina/telegram_bot/FinAssistAI-bot')

# Переімпортуємо модуль для оновлення
if 'services.statement_parser' in sys.modules:
    importlib.reload(sys.modules['services.statement_parser'])

from services.statement_parser import StatementParser
import pdfplumber

def test_monobank_pdf(file_path):
    """
    Тестує парсинг PDF файлу Монобанку
    """
    print(f"🔍 Тестуємо PDF файл: {file_path}")
    
    # Спочатку подивимося на структуру PDF файлу
    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"📖 Кількість сторінок: {len(pdf.pages)}")
            
            # Перевіряємо перші кілька сторінок
            for i, page in enumerate(pdf.pages[:3]):
                print(f"\n📄 Сторінка {i+1}:")
                text = page.extract_text() or ""
                print(f"   Символів тексту: {len(text)}")
                
                # Перші кілька рядків тексту
                lines = text.split('\n')[:5]
                print("   Перші рядки тексту:")
                for j, line in enumerate(lines):
                    if line.strip():
                        print(f"     {j+1}: {line.strip()[:80]}")
                
                # Перевіряємо наявність таблиць
                tables = page.extract_tables()
                print(f"   Таблиць знайдено: {len(tables)}")
                
                if tables:
                    for k, table in enumerate(tables[:2]):  # Перші 2 таблиці
                        print(f"     Таблиця {k+1}: {len(table)} рядків, {len(table[0]) if table else 0} стовпців")
                        if table and len(table) > 0:
                            print(f"       Перший рядок: {table[0]}")
        
    except Exception as e:
        print(f"❌ Помилка читання PDF файлу: {e}")
        return
    
    print("\n" + "="*80)
    
    # Тестуємо парсер
    try:
        parser = StatementParser()
        # Спочатку спробуємо загальний метод
        transactions = parser.parse_bank_statement(file_path, bank_type='monobank')
        
        print(f"✅ Парсинг успішний!")
        print(f"📈 Знайдено транзакцій: {len(transactions)}")
        
        if transactions:
            print("\n📋 Перші 5 транзакцій:")
            for i, transaction in enumerate(transactions[:5]):
                print(f"  {i+1}. Дата: {transaction.get('date')}")
                print(f"     Сума: {transaction.get('amount')} грн")
                print(f"     Тип: {transaction.get('type')}")
                print(f"     Опис: {transaction.get('description', 'N/A')[:50]}")
                print(f"     Джерело: {transaction.get('source')}")
                print()
            
            # Статистика
            income_count = len([t for t in transactions if t.get('type') == 'income'])
            expense_count = len([t for t in transactions if t.get('type') == 'expense'])
            total_income = sum([t.get('amount', 0) for t in transactions if t.get('type') == 'income'])
            total_expense = sum([t.get('amount', 0) for t in transactions if t.get('type') == 'expense'])
            
            print("📊 Статистика:")
            print(f"   Доходів: {income_count} (сума: {total_income:.2f} грн)")
            print(f"   Витрат: {expense_count} (сума: {total_expense:.2f} грн)")
        else:
            print("⚠️ Транзакції не знайдені.")
            
    except Exception as e:
        print(f"❌ Помилка парсингу: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Шукаємо PDF файл
    pdf_file = "/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/statements/report_20-06-2025_16-12-03.pdf"
    
    if os.path.exists(pdf_file):
        test_monobank_pdf(pdf_file)
    else:
        print(f"❌ PDF файл не знайдено: {pdf_file}")
        
        # Пошук всіх PDF файлів у директорії
        uploads_dir = "/Users/abobina/telegram_bot/FinAssistAI-bot/uploads"
        if os.path.exists(uploads_dir):
            for root, dirs, files in os.walk(uploads_dir):
                for file in files:
                    if file.endswith('.pdf'):
                        full_path = os.path.join(root, file)
                        print(f"Знайдено PDF файл: {full_path}")
