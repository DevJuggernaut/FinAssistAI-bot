#!/usr/bin/env python3
"""
Демо покращеного парсера чеків Таврія В
"""

import sys
import os
sys.path.append('/Users/abobina/telegram_bot/FinAssistAI-bot')

from services.tavria_receipt_parser import TavriaReceiptParser

def test_specific_receipt():
    """Тестує конкретний чек з покращеним логуванням"""
    
    parser = TavriaReceiptParser()
    receipt_path = '/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/receipts/photo_2025-06-24 21.09.07.jpeg'
    
    print("="*60)
    print("ТЕСТ ПОКРАЩЕНОГО ПАРСЕРА ЧЕКІВ ТАВРІЯ В")
    print("="*60)
    
    result = parser.parse_receipt(receipt_path)
    
    if result:
        print(f"\n✅ ЧЕК УСПІШНО РОЗПІЗНАНО!")
        print(f"Магазин: {result['store_name']}")
        print(f"Дата: {result.get('date', 'Не знайдено')}")
        print(f"Номер чека: {result.get('receipt_number', 'Не знайдено')}")
        print(f"Загальна сума: {result['total_amount']:.2f} грн")
        print(f"Знайдено товарів: {len(result['items'])}")
        
        print(f"\n📦 ТОВАРИ:")
        for i, item in enumerate(result['items'], 1):
            print(f"  {i}. {item['name']}: {item['price']:.2f} грн ({item['category']})")
        
        print(f"\n📊 ПО КАТЕГОРІЯХ:")
        for category, info in result['categorized_items'].items():
            print(f"  {category}: {info['item_count']} товарів, {info['total_amount']:.2f} грн")
        
        # Показуємо частину сирого тексту
        print(f"\n📄 ФРАГМЕНТ РОЗПІЗНАНОГО ТЕКСТУ:")
        print(result['raw_text'][:300] + "...")
        
    else:
        print("❌ Не вдалося розпізнати чек")

if __name__ == "__main__":
    test_specific_receipt()
