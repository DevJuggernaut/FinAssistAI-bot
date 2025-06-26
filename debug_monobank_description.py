#!/usr/bin/env python3
"""
Скрипт для діагностики проблем з описами у PDF виписках Монобанку
"""

import pdfplumber
import logging
import sys
import os

# Налаштовуємо логування
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_pdf_structure(pdf_path):
    """Аналізує структуру PDF файлу"""
    
    if not os.path.exists(pdf_path):
        print(f"❌ Файл {pdf_path} не знайдено")
        return
    
    print(f"📄 Аналіз PDF файлу: {pdf_path}")
    print("=" * 50)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"📊 Кількість сторінок: {len(pdf.pages)}")
            
            for page_num, page in enumerate(pdf.pages):
                print(f"\n📄 Сторінка {page_num + 1}:")
                print("-" * 30)
                
                # Аналізуємо таблиці
                tables = page.extract_tables()
                
                if not tables:
                    print("❌ Таблиці не знайдені")
                    text = page.extract_text()
                    if text:
                        print("📝 Знайдено текст:")
                        print(text[:500] + "..." if len(text) > 500 else text)
                    continue
                
                print(f"📊 Знайдено таблиць: {len(tables)}")
                
                for table_num, table in enumerate(tables):
                    print(f"\n📋 Таблиця {table_num + 1}:")
                    print(f"   Рядків: {len(table)}")
                    
                    if len(table) == 0:
                        print("   ❌ Таблиця порожня")
                        continue
                    
                    # Аналізуємо заголовки
                    headers = table[0] if table else []
                    print(f"   Колонок: {len(headers)}")
                    print(f"   Заголовки: {headers}")
                    
                    # Аналізуємо перші кілька рядків даних
                    data_rows = table[1:6] if len(table) > 1 else []
                    for i, row in enumerate(data_rows):
                        print(f"   Рядок {i+1}: {row}")
                    
                    if len(table) > 6:
                        print(f"   ... та ще {len(table) - 6} рядків")
                    
                    # Аналізуємо можливі колонки з описом
                    print("\n🔍 Аналіз колонок:")
                    for i, header in enumerate(headers):
                        header_str = str(header or '').lower().strip()
                        print(f"   Колонка {i}: '{header}' -> '{header_str}'")
                        
                        # Перевіряємо, чи це може бути колонка з описом
                        description_keywords = [
                            'деталі', 'опис', 'details', 'операці', 'призначення', 'purpose', 
                            'comment', 'коментар', 'description', 'merchant', 'торговець',
                            'контрагент', 'назва', 'name', 'transaction', 'операція'
                        ]
                        
                        if any(keyword in header_str for keyword in description_keywords):
                            print(f"      ✅ Можлива колонка з описом!")
                        
                        # Аналізуємо дані в цій колонці
                        if len(table) > 1:
                            sample_values = []
                            for row_idx in range(1, min(4, len(table))):
                                if i < len(table[row_idx]):
                                    sample_values.append(str(table[row_idx][i] or ''))
                            
                            print(f"      Приклади даних: {sample_values}")
                    
                    print("\n" + "="*50)
    
    except Exception as e:
        logger.error(f"Помилка при аналізі PDF: {e}", exc_info=True)

def main():
    # Шукаємо PDF файли у поточній папці
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    
    if not pdf_files:
        print("❌ PDF файли не знайдені у поточній папці")
        print("📁 Покладіть PDF файл Монобанку у папку з цим скриптом")
        return
    
    print(f"📂 Знайдено PDF файлів: {len(pdf_files)}")
    
    for pdf_file in pdf_files:
        analyze_pdf_structure(pdf_file)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
