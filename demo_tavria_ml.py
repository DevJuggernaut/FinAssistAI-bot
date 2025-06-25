#!/usr/bin/env python3
"""
Демонстрація роботи ML категоризатора з товарами Таврія В
"""

import os
import sys

# Додаємо шлях до проекту
sys.path.append(os.path.dirname(__file__))

from services.tavria_receipt_parser import TavriaReceiptParser

def demo_ml_categorization():
    """Демо ML категоризації товарів"""
    parser = TavriaReceiptParser()
    
    # Тестові товари з чеків Таврія В
    test_products = [
        "коньяк таврія премізм 0.5л",
        "українська зірка гречана 900г", 
        "каша обсяночка 450г асорті",
        "пиво мекленбургер 0.5л",
        "корона екстра 0.33л скл",
        "вода моршинська спорт 0.7л б/газ",
        "чипси м'ясна пательня 3гри",
        "біфідойогурт активіа 2.2% манго-персик",
        "морозиво три ведмеді monaco ескімо",
        "сметана славія 15% 350г",
        "коржі для торта merci 500г"
    ]
    
    print("🧠 ДЕМОНСТРАЦІЯ ML КАТЕГОРИЗАЦІЇ ТОВАРІВ ТАВРІЯ В\n")
    print(f"{'Товар':<50} {'Категорія':<20}")
    print("="*70)
    
    for product in test_products:
        category = parser._guess_category(product)
        emoji_map = {
            'напої': '🥤',
            'алкоголь': '🍺', 
            'молочні продукти': '🥛',
            'крупи та каші': '🌾',
            'кондитерські вироби': '🍰',
            'снеки': '🍿',
            'хліб та випічка': '🍞',
            'продукти харчування': '🍽️',
            'інше': '📦'
        }
        emoji = emoji_map.get(category, '📦')
        print(f"{product:<50} {emoji} {category}")
    
    print("\n" + "="*70)
    print("\n📊 СТАТИСТИКА КАТЕГОРІЙ:")
    
    # Підраховуємо статистику
    category_counts = {}
    for product in test_products:
        category = parser._guess_category(product)
        category_counts[category] = category_counts.get(category, 0) + 1
    
    for category, count in sorted(category_counts.items()):
        emoji = emoji_map.get(category, '📦')
        print(f"  {emoji} {category}: {count} товарів")
    
    print(f"\n✅ Загалом категоризовано: {len(test_products)} товарів")
    print(f"📂 Унікальних категорій: {len(category_counts)}")

def demo_receipt_processing():
    """Демо обробки реального чека"""
    parser = TavriaReceiptParser()
    
    print("\n\n🧾 ДЕМОНСТРАЦІЯ ОБРОБКИ РЕАЛЬНОГО ЧЕКА\n")
    
    # Беремо перший чек для демо
    receipts_dir = "/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/receipts"
    receipt_files = [f for f in os.listdir(receipts_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    if not receipt_files:
        print("❌ Чеки не знайдено")
        return
    
    # Беремо найбільш повний чек (другий)
    receipt_path = os.path.join(receipts_dir, receipt_files[1])
    print(f"📄 Обробляємо чек: {receipt_files[1]}")
    
    result = parser.parse_receipt(receipt_path)
    
    if not result:
        print("❌ Не вдалося розпізнати чек")
        return
    
    print(f"\n🏪 Магазин: {result['store_name']}")
    print(f"💰 Загальна сума: {result['total_amount']:.2f} грн")
    print(f"📦 Товарів: {len(result['items'])}")
    print(f"📂 Категорій: {len(result['categorized_items'])}")
    
    print(f"\n📊 РОЗПОДІЛ ПО КАТЕГОРІЯХ:")
    
    emoji_map = {
        'напої': '🥤',
        'алкоголь': '🍺', 
        'молочні продукти': '🥛',
        'крупи та каші': '🌾',
        'кондитерські вироби': '🍰',
        'снеки': '🍿',
        'хліб та випічка': '🍞',
        'продукти харчування': '🍽️',
        'інше': '📦'
    }
    
    for category, data in result['categorized_items'].items():
        emoji = emoji_map.get(category, '📦')
        percentage = (data['total_amount'] / result['total_amount']) * 100
        print(f"  {emoji} {category.title()}: {data['total_amount']:.2f} грн ({percentage:.1f}%)")
        
        # Показуємо топ товари в категорії
        for item in data['items'][:2]:  # Перші 2 товари
            print(f"    • {item['name']}: {item['price']:.2f} грн")
    
    print(f"\n💡 ВИСНОВКИ:")
    print(f"  • Найбільша категорія: {max(result['categorized_items'].items(), key=lambda x: x[1]['total_amount'])[0]}")
    print(f"  • Середня ціна товару: {result['total_amount']/len(result['items']):.2f} грн")
    print(f"  • Розпізнавання: успішне ✅")

if __name__ == "__main__":
    demo_ml_categorization()
    demo_receipt_processing()
