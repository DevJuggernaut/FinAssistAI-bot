#!/usr/bin/env python3
"""
Тестування безкоштовного розпізнавання чеків MIDA
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.mida_receipt_parser import mida_receipt_parser
from services.free_receipt_parser import free_receipt_parser
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_receipt_parsing(image_path: str):
    """Тестує розпізнавання чеку"""
    print(f"🔍 Тестуємо розпізнавання чеку: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"❌ Файл не знайдено: {image_path}")
        return
    
    print("\n1️⃣ Тестуємо MIDA парсер...")
    mida_result = mida_receipt_parser.parse_receipt(image_path)
    
    if mida_result:
        print("✅ MIDA парсер успішно розпізнав чек!")
        print(f"🏪 Магазин: {mida_result.get('store_name')}")
        print(f"💰 Сума: {mida_result.get('total_amount', 0):.2f} грн")
        print(f"📅 Дата: {mida_result.get('date')}")
        print(f"🛒 Товарів: {len(mida_result.get('items', []))}")
        
        if 'categorized_items' in mida_result:
            print("📂 Категорії:")
            for category, data in mida_result['categorized_items'].items():
                if isinstance(data, dict) and 'items' in data:
                    print(f"  - {category}: {data['item_count']} товарів, {data['total_amount']:.2f} грн")
        
        print(f"\n📄 Розпізнаний текст:\n{mida_result.get('raw_text', '')[:200]}...")
    else:
        print("❌ MIDA парсер не зміг розпізнати чек")
    
    print("\n2️⃣ Тестуємо загальний безкоштовний парсер...")
    free_result = free_receipt_parser.parse_receipt(image_path)
    
    if free_result:
        print("✅ Загальний парсер успішно розпізнав чек!")
        print(f"🏪 Магазин: {free_result.get('store_name')}")
        print(f"💰 Сума: {free_result.get('total_amount', 0):.2f} грн")
        print(f"📅 Дата: {free_result.get('date')}")
        print(f"🛒 Товарів: {len(free_result.get('items', []))}")
        
        items = free_result.get('items', [])
        if items:
            print("🛍️ Товари:")
            for item in items[:5]:  # Показуємо перші 5 товарів
                print(f"  - {item['name']}: {item['price']:.2f} грн")
            if len(items) > 5:
                print(f"  ... та ще {len(items) - 5} товарів")
        
        print(f"\n📄 Розпізнаний текст:\n{free_result.get('raw_text', '')[:200]}...")
    else:
        print("❌ Загальний парсер не зміг розпізнати чек")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Використання: python test_mida_receipt.py <шлях_до_фото_чеку>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    test_receipt_parsing(image_path)
