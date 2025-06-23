#!/usr/bin/env python3
"""
Новий тест PDF парсингу з правильним імпортом
"""

import sys
import os

# Додаємо шлях до проекту
project_path = '/Users/abobina/telegram_bot/FinAssistAI-bot'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Очищуємо кеш модулів
modules_to_clear = [k for k in sys.modules.keys() if k.startswith('services')]
for module in modules_to_clear:
    if module in sys.modules:
        del sys.modules[module]

def test_pdf_parsing_direct():
    """Прямий тест PDF парсингу"""
    print("🔄 Імпортуємо модулі...")
    
    try:
        from services.statement_parser import StatementParser
        print("✅ StatementParser імпортовано успішно")
        
        # Перевіряємо наявність методу
        parser = StatementParser()
        has_method = hasattr(parser, '_parse_monobank_pdf')
        print(f"🔍 Метод _parse_monobank_pdf існує: {'✅' if has_method else '❌'}")
        
        if not has_method:
            # Показуємо доступні методи
            methods = [method for method in dir(parser) if method.startswith('_parse')]
            print(f"📋 Доступні методи парсингу: {methods}")
            return
        
        # Тестуємо парсинг
        pdf_file = "/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/statements/report_20-06-2025_16-12-03.pdf"
        if not os.path.exists(pdf_file):
            print(f"❌ PDF файл не знайдено: {pdf_file}")
            return
        
        print(f"🔍 Тестуємо PDF парсинг: {pdf_file}")
        
        # Прямий виклик методу
        transactions = parser._parse_monobank_pdf(pdf_file)
        
        print(f"✅ Парсинг успішний!")
        print(f"📈 Знайдено транзакцій: {len(transactions)}")
        
        if transactions:
            print("\n📋 Перші 3 транзакції:")
            for i, transaction in enumerate(transactions[:3]):
                print(f"  {i+1}. {transaction.get('date')} {transaction.get('time')}")
                print(f"     Сума: {transaction.get('amount')} грн ({transaction.get('type')})")
                print(f"     Опис: {transaction.get('description')}")
                print()
        else:
            print("⚠️ Транзакції не знайдені")
            
    except Exception as e:
        print(f"❌ Помилка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_parsing_direct()
