#!/usr/bin/env python3

"""
Debug Monobank PDF import with detailed logging
"""

import sys
import os
import pdfplumber
import logging

# Add the project root to Python path
sys.path.append('/Users/abobina/telegram_bot/FinAssistAI-bot')

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_monobank_pdf():
    """Debug Monobank PDF structure"""
    
    pdf_file_path = '/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/statements/report_20-06-2025_16-12-03.pdf'
    
    if not os.path.exists(pdf_file_path):
        print(f"❌ PDF файл не знайдено: {pdf_file_path}")
        return
    
    print(f"🔍 Аналіз структури Monobank PDF: {pdf_file_path}")
    print("=" * 70)
    
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            print(f"📄 Кількість сторінок: {len(pdf.pages)}")
            print()
            
            for page_num, page in enumerate(pdf.pages[:2], 1):  # Тільки перші 2 сторінки
                print(f"🔍 Сторінка {page_num}:")
                print("-" * 50)
                
                # Спробуємо витягти таблиці
                tables = page.extract_tables()
                print(f"  Кількість таблиць: {len(tables)}")
                
                if tables:
                    for table_num, table in enumerate(tables[:2], 1):  # Тільки перші 2 таблиці
                        print(f"  \n  📊 Таблиця {table_num}:")
                        print(f"     Кількість рядків: {len(table)}")
                        
                        if table:
                            # Заголовки
                            headers = table[0] if table else []
                            print(f"     Заголовки: {headers}")
                            
                            # Перші кілька рядків даних
                            for row_idx, row in enumerate(table[1:6], 1):  # Перші 5 рядків даних
                                print(f"     Рядок {row_idx}: {row}")
                
                # Якщо таблиць немає, спробуємо витягти текст
                if not tables:
                    text = page.extract_text()
                    if text:
                        print(f"  📝 Текст сторінки ({len(text)} символів):")
                        lines = text.split('\n')[:10]  # Перші 10 рядків
                        for i, line in enumerate(lines, 1):
                            print(f"     Рядок {i}: {line.strip()}")
                
                print()
                
    except Exception as e:
        print(f"❌ Помилка при аналізі: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_monobank_pdf()
