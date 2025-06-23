#!/usr/bin/env python3
"""
Простий тест для перевірки фінального результату
"""

import sys
import os
import logging

# Додаємо поточну директорію до шляху
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.receipt_processor_enhanced import EnhancedReceiptProcessor

def simple_test():
    """Простий тест з прямим викликом методу"""
    
    processor = EnhancedReceiptProcessor()
    
    print("=== ПРОСТИЙ ТЕСТ ПАРСИНГУ ===")
    
    # Очищений текст після всіх OCR виправлень
    cleaned_text = """ФОП ЛІОТІКОВ ВІТАЛІЙ ВАЛЕРІЇОВИЧ
Магазин
Миколаївська область, M. Миколаїв, Заводський район, Byn
Лазурна, буд16в
Tf] 2903314199
Касовий чек
ПРРО OH 4000962466 ВН 1
ЧЕК OH _5eAP3VrxXi8 ВН 288 onnaitn
номер ДЛЯ замовлення:
(66) 086 22 81
098714014460
Підпис ne не потрібен
APT... 271558 17871/w1/В/Вода солод Sprite 3/6 0.33n
1.000 x 24.30 = 24.30
APT. Me 271559 3838/«r/В/Цукати ананас кільце Bar /MM/
@.186 x 409.50 = 76.17
СУМА ДО СПЛАТИ: 100.47
БЕЗГОТІВКОВА. БЕЗГОТІВКОВИЙ: 100.47
Bes NDB
Дякуємо!
Mu відкрились!!!
Інтернет—магазин "MIDA"
mid
a.mk.ua
---Onnata Ef3--------—-
Еквайр: Приватбанк
Торговець: S
1NFQ7HN
Термінал: SINFQ7HN
Платіжна система: MasterCar
d
EM3: XXXXXXXXXXXX2210
Koy авторизації: 717989
RRN:
18-06-2025 13:47:15
ФІСКАЛЬНИЙ ЧЕК
ФІСКО ЧЕК
Державна nopatkosa служба YKpainn"""

    # Прямий виклик парсера
    result = processor._parse_receipt_text(cleaned_text)
    
    print("=== ФІНАЛЬНИЙ РЕЗУЛЬТАТ ===")
    print(f"📅 Дата: {result.get('date')}")
    print(f"🏪 Магазин: {result.get('store_name')}")
    print(f"💰 Загальна сума: {result.get('total_amount')}")
    print(f"🛒 Кількість товарів: {result.get('items_count')}")
    
    items = result.get('items', [])
    if items:
        print("\n--- ТОВАРИ ---")
        for i, item in enumerate(items, 1):
            print(f"{i}. {item.get('name', 'Невідомо')}")
            print(f"   Ціна: {item.get('price', 0)}")
            print(f"   Кількість: {item.get('quantity', 1)}")
            print(f"   Категорія: {item.get('category', 'Невідомо')}")
            print()

if __name__ == "__main__":
    simple_test()
