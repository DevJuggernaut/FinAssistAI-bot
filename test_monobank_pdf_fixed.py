#!/usr/bin/env python3

"""
Test Monobank PDF import after fixing suggest_category_for_bank_statement method
"""

import sys
import os

# Add the project root to Python path
sys.path.append('/Users/abobina/telegram_bot/FinAssistAI-bot')

from services.statement_parser import StatementParser

def test_monobank_pdf_import():
    """Test Monobank PDF import functionality"""
    
    pdf_file_path = '/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/statements/report_20-06-2025_16-12-03.pdf'
    
    if not os.path.exists(pdf_file_path):
        print(f"❌ PDF файл не знайдено: {pdf_file_path}")
        return
    
    print(f"🧪 Тестування імпорту Monobank PDF: {pdf_file_path}")
    print("-" * 70)
    
    try:
        # Спробуємо парсити файл
        parser = StatementParser()
        transactions = parser.parse_bank_statement(pdf_file_path, 'monobank')
        
        if not transactions:
            print("❌ Не вдалося розпізнати транзакції")
            return
        
        print(f"✅ Успішно розпізнано {len(transactions)} транзакцій")
        print()
        
        # Виведемо перші 5 транзакцій для перевірки
        for i, trans in enumerate(transactions[:5], 1):
            print(f"Транзакція {i}:")
            print(f"  Дата: {trans.get('date')}")
            print(f"  Час: {trans.get('time', 'N/A')}")
            print(f"  Сума: {trans.get('amount')}")
            print(f"  Опис: {trans.get('description')}")
            print(f"  Тип: {trans.get('type')}")
            print(f"  Категорія: {trans.get('category')}")
            print()
        
        if len(transactions) > 5:
            print(f"... і ще {len(transactions) - 5} транзакцій")
        
        # Перевіримо категоризацію
        categorized = [t for t in transactions if t.get('category') and t.get('category') != 'Інше']
        print(f"📊 Категоризовано: {len(categorized)} з {len(transactions)} транзакцій")
        
        # Перевіримо типи
        expenses = [t for t in transactions if t.get('type') == 'expense']
        incomes = [t for t in transactions if t.get('type') == 'income']
        print(f"💰 Доходи: {len(incomes)}, Витрати: {len(expenses)}")
        
    except Exception as e:
        print(f"❌ Помилка при імпорті: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_monobank_pdf_import()
