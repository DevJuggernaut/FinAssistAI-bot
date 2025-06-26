#!/usr/bin/env python3
"""
Прямий тест спеціального методу _parse_monobank_pdf
"""

import sys
import os
sys.path.append('/Users/abobina/telegram_bot/FinAssistAI-bot')

from services.statement_parser import StatementParser

def test_direct_monobank_pdf():
    """Прямий тест методу _parse_monobank_pdf"""
    pdf_file = "/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/statements/report_20-06-2025_16-12-03.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ PDF файл не знайдено: {pdf_file}")
        return
    
    print(f"🔍 Тестуємо ПРЯМИЙ виклик _parse_monobank_pdf для: {pdf_file}")
    
    try:
        parser = StatementParser()
        # Прямий виклик спеціального методу для Monobank
        transactions = parser._parse_monobank_pdf(pdf_file)
        
        print(f"✅ Парсинг успішний!")
        print(f"📈 Знайдено транзакцій: {len(transactions)}")
        
        if transactions:
            print(f"\n📋 Перші 5 транзакцій:")
            for i, transaction in enumerate(transactions[:5]):
                print(f"  {i+1}. Дата: {transaction['date']}")
                print(f"     Сума: {transaction['amount']} грн")
                print(f"     Тип: {transaction['type']}")
                print(f"     Опис: '{transaction['description']}'")
                print(f"     Джерело: {transaction['source']}")
                print()
    
    except Exception as e:
        print(f"❌ Помилка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_monobank_pdf()
