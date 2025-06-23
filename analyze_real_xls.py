#!/usr/bin/env python3
"""
Аналіз структури реального XLS файлу Monobank
"""

import pandas as pd
import os
import sys

def analyze_monobank_xls(file_path):
    """
    Аналізує структуру XLS файлу Monobank
    """
    print(f"📊 Аналіз файлу: {file_path}")
    print("=" * 50)
    
    try:
        # Читаємо всі аркуші
        excel_file = pd.ExcelFile(file_path)
        print(f"📄 Знайдені аркуші: {excel_file.sheet_names}")
        
        for sheet_name in excel_file.sheet_names:
            print(f"\n🔍 Аналіз аркуша: '{sheet_name}'")
            print("-" * 30)
            
            # Читаємо без заголовків для аналізу структури
            df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            print(f"📐 Розмір: {df_raw.shape[0]} рядків x {df_raw.shape[1]} колонок")
            
            # Показуємо перші 20 рядків
            print(f"\n📋 Перші 20 рядків:")
            for i in range(min(20, len(df_raw))):
                row_data = []
                for j in range(len(df_raw.columns)):
                    val = df_raw.iloc[i, j]
                    if pd.isna(val):
                        row_data.append("NaN")
                    else:
                        row_data.append(str(val)[:30])  # Обрізаємо довгі значення
                
                print(f"Рядок {i:2d}: {' | '.join(row_data)}")
                
                # Перевіряємо, чи це може бути рядок заголовків
                row_text = ' '.join([str(val).lower() if not pd.isna(val) else '' for val in df_raw.iloc[i].values])
                keywords = ['дата', 'час', 'операції', 'сума', 'деталі', 'мсс', 'баланс']
                keyword_count = sum(1 for keyword in keywords if keyword in row_text)
                
                if keyword_count >= 2:
                    print(f"   ⭐ МОЖЛИВИЙ ЗАГОЛОВОК! Знайдено {keyword_count} ключових слів")
                    print(f"      Ключові слова: {[kw for kw in keywords if kw in row_text]}")
            
            # Показуємо статистику по колонках
            print(f"\n📊 Статистика по колонках:")
            for j in range(len(df_raw.columns)):
                col_data = df_raw.iloc[:, j]
                non_na_count = col_data.notna().sum()
                print(f"  Колонка {j}: {non_na_count}/{len(col_data)} заповнених значень")
                
                # Показуємо кілька прикладів значень
                examples = col_data.dropna().head(3).tolist()
                if examples:
                    print(f"    Приклади: {examples}")
                    
    except Exception as e:
        print(f"❌ Помилка при аналізі: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    file_path = "uploads/statements/report_20-06-2025_16-12-27.xls"
    
    if os.path.exists(file_path):
        analyze_monobank_xls(file_path)
    else:
        print(f"❌ Файл не знайдено: {file_path}")
        print("Доступні файли:")
        if os.path.exists("uploads/statements/"):
            for f in os.listdir("uploads/statements/"):
                print(f"  - {f}")
