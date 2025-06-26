#!/usr/bin/env python3
"""
Тестовий скрипт для діагностики парсингу PDF Монобанку
"""

import sys
import os
import logging

# Додаємо поточну папку до шляху для імпорту
sys.path.append('/Users/abobina/telegram_bot/FinAssistAI-bot')

from services.statement_parser import StatementParser

# Налаштовуємо детальне логування
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pdf_debug.log')
    ]
)

logger = logging.getLogger(__name__)

def test_pdf_parsing():
    """Тестуємо парсинг PDF з детальним логуванням"""
    
    # Шукаємо PDF файли у поточній папці
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    
    if not pdf_files:
        print("❌ PDF файли не знайдені у поточній папці")
        print("📁 Покладіть PDF файл Монобанку у папку з проектом")
        return
    
    print(f"📂 Знайдено PDF файлів: {len(pdf_files)}")
    
    for pdf_file in pdf_files:
        print(f"\n🔍 Тестуємо файл: {pdf_file}")
        print("=" * 50)
        
        try:
            parser = StatementParser()
            
            # Спробуємо спеціальний парсер Монобанку
            print("📊 Використовуємо спеціальний парсер Монобанку...")
            transactions = parser._parse_monobank_pdf(pdf_file)
            
            print(f"✅ Знайдено транзакцій: {len(transactions)}")
            
            if transactions:
                print("\n📋 Перші 5 транзакцій:")
                for i, trans in enumerate(transactions[:5], 1):
                    print(f"{i}. {trans.get('date')} - {trans.get('amount')} - '{trans.get('description')}'")
                    print(f"   Тип: {trans.get('type')}")
                    print(f"   Час: {trans.get('time')}")
                    print(f"   Сирі дані: date='{trans.get('raw_date')}', amount='{trans.get('raw_amount')}'")
                    print()
            else:
                print("❌ Транзакції не знайдені")
            
        except Exception as e:
            logger.error(f"Помилка при парсингу файлу {pdf_file}: {e}", exc_info=True)
            print(f"❌ Помилка: {e}")
        
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test_pdf_parsing()
