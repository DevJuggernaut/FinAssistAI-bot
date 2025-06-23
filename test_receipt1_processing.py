#!/usr/bin/env python3
"""
Тест розпізнавання чека test_receipt1.png
"""

import sys
import os
import logging
import json

# Додаємо поточну директорію до шляху
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.receipt_processor_enhanced import EnhancedReceiptProcessor

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_receipt1_processing():
    """Тестування з test_receipt1.png"""
    
    processor = EnhancedReceiptProcessor()
    
    print("=== ТЕСТ РОЗПІЗНАВАННЯ ЧЕКА test_receipt1.png ===")
    
    # Шлях до тестового чека
    receipt_image_path = "/Users/abobina/telegram_bot/FinAssistAI-bot/test_receipt1.png"
    
    if not os.path.exists(receipt_image_path):
        print(f"❌ Файл не знайдено: {receipt_image_path}")
        return
    
    print(f"📄 Обробляємо файл: {receipt_image_path}")
    
    try:
        # Обробляємо чек
        result = processor.process_receipt_image(receipt_image_path)
        
        print("\n=== РЕЗУЛЬТАТИ РОЗПІЗНАВАННЯ ===")
        print(f"📅 Дата: {result.get('date', 'Не знайдено')}")
        print(f"💰 Загальна сума: {result.get('total_amount', 'Не знайдено')}")
        print(f"🏪 Назва магазину: {result.get('store_name', 'Не знайдено')}")
        
        items = result.get('items', [])
        print(f"\n🛒 Знайдено товарів: {len(items)}")
        
        if items:
            print("\n--- СПИСОК ТОВАРІВ ---")
            for i, item in enumerate(items, 1):
                name = item.get('name', 'Невідома назва')
                price = item.get('price', 'Невідома ціна')
                quantity = item.get('quantity', 1)
                print(f"{i}. {name}")
                print(f"   Ціна: {price}")
                print(f"   Кількість: {quantity}")
                print()
        else:
            print("❌ Товари не знайдено")
        
        # Виводимо сирий текст для аналізу
        raw_text = result.get('raw_text', '')
        if raw_text:
            print("\n=== СИРИЙ ТЕКСТ З OCR ===")
            print(raw_text)
            print("=" * 50)
        
        # Зберігаємо результат у файл для аналізу
        output_file = "/Users/abobina/telegram_bot/FinAssistAI-bot/test_receipt1_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Результати збережено у: {output_file}")
        
        # Аналіз якості розпізнавання
        print("\n=== АНАЛІЗ ЯКОСТІ ===")
        if result.get('date'):
            print("✅ Дата розпізнана")
        else:
            print("❌ Дата не розпізнана")
            
        if result.get('total_amount'):
            print("✅ Загальна сума розпізнана")
        else:
            print("❌ Загальна сума не розпізнана")
            
        if items:
            print(f"✅ Товари розпізнані ({len(items)} шт.)")
        else:
            print("❌ Товари не розпізнані")
            
        if result.get('store_name'):
            print("✅ Назва магазину розпізнана")
        else:
            print("❌ Назва магазину не розпізнана")
            
    except Exception as e:
        print(f"❌ Помилка при обробці чека: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_receipt1_processing()
