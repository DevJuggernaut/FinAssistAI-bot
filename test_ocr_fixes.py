#!/usr/bin/env python3
"""
Тест після виправлення OCR помилок
"""

import sys
import os
import re
from datetime import datetime

# Додаємо поточну директорію до шляху
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.receipt_processor_enhanced import EnhancedReceiptProcessor

def test_after_ocr_fixes():
    """Тест після виправлення OCR помилок"""
    
    processor = EnhancedReceiptProcessor()
    
    print("=== ТЕСТ ПІСЛЯ ВИПРАВЛЕННЯ OCR ПОМИЛОК ===")
    
    # Сирий текст
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

    # Очищуємо текст
    cleaned_text = processor._clean_ocr_text(raw_text)
    
    print("=== ОЧИЩЕНИЙ ТЕКСТ ===")
    print(cleaned_text)
    print("=" * 50)
    
    # Аналізуємо очищений текст
    lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]
    
    print("\n=== АНАЛІЗ ОЧИЩЕНОГО ТЕКСТУ ===")
    
    # 1. Дата
    print("1. ДАТА:")
    date_result = processor._extract_date(cleaned_text)
    print(f"   Знайдена дата: {date_result}")
    
    # 2. Загальна сума
    print("\n2. ЗАГАЛЬНА СУМА:")
    total_amount = 0.0
    for line in lines:
        if processor._is_total_line(line):
            amount = processor._extract_amount_from_line(line)
            print(f"   Рядок із сумою: '{line}' -> {amount}")
            if amount > total_amount:
                total_amount = amount
    print(f"   Фінальна сума: {total_amount}")
    
    # 3. Товари
    print("\n3. ТОВАРИ:")
    items, detected_total = processor._extract_items_and_total(lines)
    print(f"   Знайдено товарів: {len(items)}")
    for i, item in enumerate(items, 1):
        print(f"   {i}. {item.get('description', 'Невідомо')}")
        print(f"      Ціна: {item.get('amount', 0)}")
        print(f"      Кількість: {item.get('quantity', 1)}")
        print()
    
    print(f"   Загальна сума з товарів: {detected_total}")
    
    # 4. Повний результат
    print("\n4. ПОВНИЙ РЕЗУЛЬТАТ:")
    result = processor._parse_receipt_text(cleaned_text)
    
    print(f"   Дата: {result.get('date')}")
    print(f"   Магазин: {result.get('store_name')}")
    print(f"   Загальна сума: {result.get('total_amount')}")
    print(f"   Кількість товарів: {result.get('items_count')}")

if __name__ == "__main__":
    test_after_ocr_fixes()
