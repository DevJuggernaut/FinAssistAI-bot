#!/usr/bin/env python3
"""
Тестування парсера Таврія В
"""

import os
import sys

# Додаємо шлях до проекту
sys.path.append(os.path.dirname(__file__))

from services.tavria_receipt_parser import TavriaReceiptParser

def test_tavria_parser():
    """Тестує парсер на реальних чеках"""
    parser = TavriaReceiptParser()
    
    receipts_dir = "/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/receipts"
    receipt_files = [f for f in os.listdir(receipts_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    for receipt_file in sorted(receipt_files):
        receipt_path = os.path.join(receipts_dir, receipt_file)
        print(f"\n{'='*60}")
        print(f"Тестування парсера: {receipt_file}")
        print(f"{'='*60}")
        
        result = parser.parse_receipt(receipt_path)
        if result:
            print(f"✅ РЕЗУЛЬТАТ:")
            print(f"Магазин: {result['store_name']}")
            print(f"Дата: {result['date']}")
            print(f"Номер чека: {result['receipt_number']}")
            print(f"Загальна сума: {result['total_amount']:.2f} грн")
            print(f"Знайдено товарів: {len(result['items'])}")
            
            print(f"\n📦 ТОВАРИ:")
            for i, item in enumerate(result['items'], 1):
                print(f"  {i}. {item['name']}: {item['price']:.2f} грн ({item['category']})")
            
            print(f"\n📊 ПО КАТЕГОРІЯХ:")
            for category, data in result['categorized_items'].items():
                print(f"  {category}: {data['item_count']} товарів, {data['total_amount']:.2f} грн")
        else:
            print("❌ Не вдалося розпізнати чек")

if __name__ == "__main__":
    test_tavria_parser()
