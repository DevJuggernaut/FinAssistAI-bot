#!/usr/bin/env python3
"""
Детальне дебагування парсингу PDF Monobank
"""

import sys
import os
sys.path.append('/Users/abobina/telegram_bot/FinAssistAI-bot')

import pdfplumber

def debug_pdf_structure():
    """Детальний аналіз структури PDF файлу"""
    pdf_file = "/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/statements/report_20-06-2025_16-12-03.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ PDF файл не знайдено: {pdf_file}")
        return
    
    print(f"🔍 Аналізуємо PDF: {pdf_file}")
    
    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages):
            print(f"\n📄 Сторінка {page_num + 1}:")
            tables = page.extract_tables()
            
            for table_num, table in enumerate(tables):
                print(f"\n  📊 Таблиця {table_num + 1}:")
                
                if table and len(table) > 0:
                    # Заголовки
                    headers = table[0]
                    print(f"    📝 Заголовки ({len(headers)} колонок):")
                    for i, header in enumerate(headers):
                        print(f"      {i}: '{header}'")
                    
                    # Перші кілька рядків даних
                    print(f"    📋 Дані ({len(table)-1} рядків):")
                    for row_num, row in enumerate(table[1:6]):  # Перші 5 рядків даних
                        print(f"      Рядок {row_num + 1}:")
                        for col_num, cell in enumerate(row):
                            print(f"        Колонка {col_num}: '{cell}'")
                        print()  # Порожній рядок між рядками

if __name__ == "__main__":
    debug_pdf_structure()
