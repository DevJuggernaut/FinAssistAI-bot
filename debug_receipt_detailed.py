#!/usr/bin/env python3
"""
Детальний дебаг розпізнавання чека
"""

import sys
import os
import re
from datetime import datetime

# Додаємо поточну директорію до шляху
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.receipt_processor_enhanced import EnhancedReceiptProcessor

def debug_receipt_processing():
    """Детальний аналіз кожного кроку обробки"""
    
    processor = EnhancedReceiptProcessor()
    
    print("=== ДЕБАГ РОЗПІЗНАВАННЯ ЧЕКА ===")
    
    # Текст з нашого OCR
    raw_text = """OOM AHTIKOB BITANIM BANEPTMOBHY
Mara3nu
Mukonaispcbka o6nacTb, M. Mukonais, 3aBoncbKui paox, Byn
Jla3sypHa, 6yq16p
Tf] 2903314199
Kacosuh uex
MPPO OH 4000962466 BH 1
YEK OH _5eAP3VrxXi8 BH 288 onnaitn
HOMep ANA 3aMOBHEHHHA:

(66) 086 22 81
098714014460
Nignuc ne notTpi6er

APT... 271558 17871/w1/B/Bona conog Sprite 3/6 0.33n

1.000 x 24.30 = 24.30
APT. Me 271559 3838/«r/B/UykatTn aHaHac Kinbue Bar /MM/
@.186 x 409.50 = 76.17
CYMA 0 CNIATH: 100.47
BE3FOTIBKOBA. BE3TOTIBKOBMM: 100.47
Bes NDB

Aaxyemo!

Mu Binkpunuce!!!
THTepket—mara3svn "MIDA"
mid

a.mk.ua

---Onnata Ef3--------—-
Exsalip: Mpusatbank
Toproseub: S

1NFQ7HN

Tepmixan: SINFQ7HN

Nnatixda cuctema: MasterCar
d

EM3: XXXXXXXXXXXX2210

Koy aptopm3auii: 717989
RRN:

18-06-2025 13:47:15
OICKANbHUM YEK
ockKO EKN
lepxasHa nopatkosa cnyx6a YKpainn"""

    print("=== 1. АНАЛІЗ ДАТИ ===")
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    # Шукаємо дати
    date_patterns = [
        r'(\d{2}[./]\d{2}[./]\d{4})',  
        r'(\d{4}[.-]\d{2}[.-]\d{2})',  
        r'(\d{2}[.-]\d{2}[.-]\d{2})',  
        r'(\d{2}\.\d{2}\.\d{2})',      
        r'(\d{2}-\d{2}-\d{4})',        
        r'(\d{1,2}-\d{1,2}-\d{4})',    
    ]
    
    print(f"Шукаємо дати в тексті...")
    for pattern in date_patterns:
        matches = re.findall(pattern, raw_text)
        if matches:
            print(f"  Паттерн {pattern}: {matches}")
    
    # Шукаємо дати з часом
    datetime_pattern = r'(\d{1,2}-\d{1,2}-\d{4})\s+\d{1,2}:\d{2}:\d{2}'
    datetime_matches = re.findall(datetime_pattern, raw_text)
    print(f"  Дата з часом: {datetime_matches}")
    
    print("\n=== 2. АНАЛІЗ ЗАГАЛЬНОЇ СУМИ ===")
    
    # Шукаємо рядки з сумою
    total_keywords = ['сума', 'всього', 'до сплати', 'сплати', 'безготівков']
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in total_keywords):
            print(f"  Знайдено рядок із сумою: '{line}'")
            
            # Шукаємо числа в цьому рядку
            amounts = re.findall(r'\d+[.,]\d{2}', line)
            print(f"    Числа в рядку: {amounts}")
            
            # Перевіряємо спеціальні паттерни
            special_patterns = [
                r'сума.*(\d+[.,]\d{2})',
                r'всього.*(\d+[.,]\d{2})', 
                r'сплати.*(\d+[.,]\d{2})',
                r'безготівков.*(\d+[.,]\d{2})',
            ]
            
            for pattern in special_patterns:
                match = re.search(pattern, line_lower)
                if match:
                    print(f"    Спец.паттерн {pattern}: {match.group(1)}")
    
    print("\n=== 3. АНАЛІЗ ТОВАРІВ ===")
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Перевіряємо, чи це може бути товар
        has_amount = (re.search(r'\d+[.,]\d{2}', line) or 
                     re.search(r'\d{1,4}\s+\d{2}', line))
        
        has_multiplication = re.search(r'[xх*×]\s*\d+[.,]\d{2}', line.lower())
        
        # Перевіряємо на назви продуктів
        product_hints = [
            'спрайт', 'sprite', 'вода', 'water', 'ананас', 'ananac', 
            'цукати', 'yxara', 'bona', 'conog', 'кільце', 'bar', 
            'uykattn', 'kinbue'
        ]
        has_product_hint = any(hint in line_lower for hint in product_hints)
        
        if has_amount or has_multiplication or has_product_hint:
            print(f"  Рядок {i}: '{line}'")
            print(f"    Має суму: {has_amount}")
            print(f"    Має множення: {has_multiplication}")
            print(f"    Має натяк на товар: {has_product_hint}")
            
            if has_amount:
                amounts = re.findall(r'\d+[.,]\d{2}', line)
                print(f"    Суми: {amounts}")
            
            if has_multiplication:
                mult_match = re.search(r'(\d+(?:[.,]\d+)?)\s*[xх*×]\s*(\d+[.,]\d{2})', line)
                if mult_match:
                    print(f"    Множення: {mult_match.group(1)} x {mult_match.group(2)}")

if __name__ == "__main__":
    debug_receipt_processing()
