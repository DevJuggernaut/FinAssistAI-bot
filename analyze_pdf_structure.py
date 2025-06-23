#!/usr/bin/env python3
"""
Прямий тест PDF парсингу для Монобанку
"""

import sys
import os
sys.path.insert(0, '/Users/abobina/telegram_bot/FinAssistAI-bot')

import pdfplumber

def analyze_pdf_structure(file_path):
    """Аналізує структуру PDF файлу"""
    print(f"🔍 Аналізуємо PDF файл: {file_path}")
    
    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"📖 Кількість сторінок: {len(pdf.pages)}")
            
            for i, page in enumerate(pdf.pages):
                print(f"\n📄 Сторінка {i+1}:")
                
                # Витягуємо текст
                text = page.extract_text() or ""
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                print(f"   Рядків тексту: {len(lines)}")
                
                # Перевіряємо, чи це Монобанк
                is_monobank = any('моно' in line.lower() or 'mono' in line.lower() or 'універсал' in line.lower() for line in lines)
                print(f"   Визначення Монобанку: {'✅' if is_monobank else '❌'}")
                
                # Витягуємо таблиці
                tables = page.extract_tables()
                print(f"   Таблиць знайдено: {len(tables)}")
                
                if tables:
                    for j, table in enumerate(tables):
                        print(f"\n   📊 Таблиця {j+1}:")
                        print(f"      Розмір: {len(table)} рядків x {len(table[0]) if table else 0} стовпців")
                        
                        if table and len(table) > 0:
                            # Заголовки
                            headers = table[0]
                            print("      Заголовки:")
                            for k, header in enumerate(headers):
                                print(f"        {k}: {header}")
                            
                            # Шукаємо ключові стовпці
                            date_col = None
                            amount_col = None
                            desc_col = None
                            
                            for k, header in enumerate(headers):
                                header_lower = str(header or '').lower()
                                if 'дата' in header_lower or 'date' in header_lower:
                                    date_col = k
                                elif 'сума' in header_lower and 'картки' in header_lower:
                                    amount_col = k
                                elif 'деталі' in header_lower or 'опис' in header_lower:
                                    desc_col = k
                            
                            print(f"      Знайдені колонки: дата={date_col}, сума={amount_col}, опис={desc_col}")
                            
                            # Показуємо кілька рядків даних
                            print("      Дані (перші 3 рядки):")
                            for row_idx in range(1, min(4, len(table))):
                                if row_idx < len(table):
                                    row = table[row_idx]
                                    print(f"        Рядок {row_idx}: {row}")
                                    
                                    # Пробуємо розпізнати транзакцію
                                    if date_col is not None and amount_col is not None and len(row) > max(date_col, amount_col):
                                        date_val = row[date_col] if date_col < len(row) else None
                                        amount_val = row[amount_col] if amount_col < len(row) else None
                                        desc_val = row[desc_col] if desc_col is not None and desc_col < len(row) else None
                                        
                                        print(f"          Дата: {date_val}")
                                        print(f"          Сума: {amount_val}")
                                        print(f"          Опис: {desc_val}")
                                        
                                        # Спробуємо парсити суму
                                        if amount_val:
                                            import re
                                            amount_clean = re.sub(r'[^\d\-\+\.\,]', '', str(amount_val))
                                            amount_clean = amount_clean.replace(',', '.')
                                            try:
                                                amount_parsed = float(amount_clean)
                                                print(f"          Сума (parsed): {amount_parsed}")
                                            except ValueError:
                                                print(f"          Сума (error): не вдалося розпізнати '{amount_clean}'")
                
    except Exception as e:
        print(f"❌ Помилка аналізу PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    pdf_file = "/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/statements/report_20-06-2025_16-12-03.pdf"
    
    if os.path.exists(pdf_file):
        analyze_pdf_structure(pdf_file)
    else:
        print(f"❌ PDF файл не знайдено: {pdf_file}")
