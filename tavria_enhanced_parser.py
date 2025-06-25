#!/usr/bin/env python3
"""
Розширена версія парсера для "Таврія В" з ручним розпізнаванням конкретних товарів
"""

import os
import sys
import re
import logging
from typing import Dict, List, Optional
from PIL import Image
import pytesseract

# Додаємо шлях до сервісів
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TavriaReceiptParserEnhanced:
    """
    Покращений парсер для чеків "Таврія В" з ручними правилами
    """
    
    def __init__(self):
        # Конкретні товари, які ми знайшли в чеках
        self.known_products = {
            'коньяк таврія премізм': {
                'category': 'алкоголь',
                'patterns': [r'коньяк.*таврія.*премізм', r'премізм.*0[.,]5']
            },
            'українська зірка гречана': {
                'category': 'крупи та каші',
                'patterns': [r'українська.*зірка.*гречана', r'зірка.*гречана', r'гречана.*зірка']
            },
            'українська зірка пропасений': {
                'category': 'крупи та каші', 
                'patterns': [r'українська.*зірка.*пропасений', r'зірка.*пропасений']
            },
            'каша обсяночка': {
                'category': 'крупи та каші',
                'patterns': [r'каша.*обсяночка', r'обсяночка.*450.*г']
            },
            'мекленбургер пиво': {
                'category': 'напої',
                'patterns': [r'mivomecki.*lenburger', r'мекленбургер', r'0[.,]5.*л.*пиво']
            },
            'корона екстра': {
                'category': 'напої', 
                'patterns': [r'корона.*екстра', r'corona.*extra', r'0[.,]33.*л.*скл']
            },
            'вода моршинська спорт': {
                'category': 'напої',
                'patterns': [r'вода.*моршинська.*спорт', r'моршинська.*0[.,]7', r'б/газ.*спорт']
            },
            'чипси пательня': {
                'category': 'снеки',
                'patterns': [r'чипси.*пательня', r'м\'ясна.*пательня']
            },
            'біфідойогурт активіа': {
                'category': 'молочні продукти',
                'patterns': [r'біфідо.*активіа', r'активіа.*2[.,]2%', r'манго.*пер']
            },
            'морозиво три ведмеді': {
                'category': 'кондитерські вироби',
                'patterns': [r'морозиво.*три.*ведмеді', r'три.*ведмеді.*monaco', r'ескімо.*манго']
            },
            'сметана славія': {
                'category': 'молочні продукти',
                'patterns': [r'сметана.*славія', r'славія.*15%.*350.*г']
            },
            'коржі для торта': {
                'category': 'кондитерські вироби',
                'patterns': [r'коржі.*д/торта', r'коржі.*merci', r'коржі.*500.*г']
            }
        }
        
        # Спеціальні шаблони для цін
        self.price_patterns = [
            r'(\d+[.,]\d{2})\s*[xх*×]\s*(\d+)',  # ціна x кількість
            r'(\d+[.,]\d{2})\s*грн',             # ціна грн
            r'(\d+[.,]\d{2})\s*-?\s*[АA]',       # ціна -А (розрахунок)
        ]
        
    def parse_receipt_manual(self, image_path: str) -> Dict:
        """Ручний парсинг з конкретними правилами"""
        try:
            # Розпізнаємо текст
            text = self._extract_text_enhanced(image_path)
            
            print(f"\n=== Повний текст з {os.path.basename(image_path)} ===")
            print(text)
            print("=" * 60)
            
            # Перевіряємо, чи це Таврія В
            if not self._is_tavria_receipt(text):
                return None
            
            # Шукаємо товари
            items = self._find_known_products(text)
            
            # Розраховуємо загальну суму
            total_amount = self._calculate_total_amount(text, items)
            
            # Витягуємо дату та номер чека
            date = self._extract_date_enhanced(text)
            receipt_number = self._extract_receipt_number_enhanced(text)
            
            result = {
                'store_name': 'Таврія В',
                'items': items,
                'total_amount': total_amount,
                'date': date,
                'receipt_number': receipt_number,
                'raw_text': text
            }
            
            # Категоризуємо
            result['categorized_items'] = self._categorize_items(result['items'])
            
            return result
            
        except Exception as e:
            logger.error(f"Помилка при парсингу: {str(e)}")
            return None
    
    def _extract_text_enhanced(self, image_path: str) -> str:
        """Покращене витягування тексту"""
        try:
            image = Image.open(image_path)
            
            # Декілька спроб з різними налаштуваннями
            configs = [
                '--oem 3 --psm 6',
                '--oem 3 --psm 4', 
                '--oem 3 --psm 3',
                '--oem 1 --psm 6'
            ]
            
            texts = []
            for config in configs:
                try:
                    text = pytesseract.image_to_string(image, lang='ukr+rus+eng', config=config)
                    texts.append(text)
                except:
                    continue
            
            # Вибираємо найдовший текст
            best_text = max(texts, key=len) if texts else ""
            return best_text
            
        except Exception as e:
            logger.error(f"Помилка OCR: {str(e)}")
            return ""
    
    def _is_tavria_receipt(self, text: str) -> bool:
        """Перевіряє чи це чек з Таврії В"""
        text_lower = text.lower()
        patterns = [
            r'таврія', r'ставрія', r'аврія',
            r'торговельний.*центр', r'центр.*кафе',
            r'лазурна', r'миколаїв'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _find_known_products(self, text: str) -> List[Dict]:
        """Шукає відомі товари"""
        items = []
        text_lower = text.lower()
        
        for product_name, product_info in self.known_products.items():
            for pattern in product_info['patterns']:
                if re.search(pattern, text_lower):
                    # Знайшли товар, тепер шукаємо ціну
                    price = self._find_price_for_product(text, pattern)
                    if price > 0:
                        items.append({
                            'name': product_name,
                            'price': price,
                            'quantity': 1,
                            'category': product_info['category']
                        })
                        logger.info(f"Знайдено товар: {product_name} - {price} грн")
                        break
        
        # Додатково шукаємо товари за загальними правилами
        additional_items = self._find_additional_products(text)
        items.extend(additional_items)
        
        return self._deduplicate_items(items)
    
    def _find_price_for_product(self, text: str, product_pattern: str) -> float:
        """Шукає ціну для конкретного товару"""
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if re.search(product_pattern, line.lower()):
                # Шукаємо ціну в цьому рядку та сусідніх
                for check_line in [line] + lines[max(0, i-1):i+2]:
                    price = self._extract_price_from_line_enhanced(check_line)
                    if price > 0:
                        return price
        
        return 0.0
    
    def _extract_price_from_line_enhanced(self, line: str) -> float:
        """Покращене витягування ціни"""
        # Шукаємо різні формати цін
        price_patterns = [
            r'(\d+[.,]\d{2})\s*[xх*×]\s*(\d+)',  # ціна x кількість  
            r'(\d+[.,]\d{2})\s*-?\s*[АA]',       # ціна -А
            r'(\d+[.,]\d{2})\s*грн',             # ціна грн
            r'(\d+[.,]\d{2})(?=\s|$)',           # просто ціна
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, line)
            if match:
                if len(match.groups()) == 2:  # з множенням
                    unit_price = float(match.group(1).replace(',', '.'))
                    quantity = int(match.group(2))
                    return unit_price * quantity
                else:
                    price = float(match.group(1).replace(',', '.'))
                    if 0.1 <= price <= 1000:  # Розумні межі
                        return price
        
        return 0.0
    
    def _find_additional_products(self, text: str) -> List[Dict]:
        """Шукає додаткові товари за загальними правилами"""
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if len(line) < 5:
                continue
            
            # Пропускаємо службові рядки
            if self._is_service_line(line):
                continue
            
            # Шукаємо рядки з цінами
            price = self._extract_price_from_line_enhanced(line)
            if price > 0:
                # Очищаємо назву товару
                product_name = self._clean_product_name(line)
                if len(product_name) >= 3:
                    category = self._guess_category(product_name)
                    items.append({
                        'name': product_name,
                        'price': price,
                        'quantity': 1,
                        'category': category
                    })
        
        return items
    
    def _is_service_line(self, line: str) -> bool:
        """Перевіряє службові рядки"""
        line_lower = line.lower()
        service_keywords = [
            'термінал', 'оплата', 'картка', 'касир', 'чек',
            'безготівкова', 'ідент', 'система', 'авт',
            'баланс', 'сплати', 'пдв', 'самообсл',
            'україна', 'заводський', 'вул.', 'код уктзед',
            'штрих-код', 'рн', 'платіжна', 'mastercard'
        ]
        
        for keyword in service_keywords:
            if keyword in line_lower:
                return True
        return False
    
    def _clean_product_name(self, line: str) -> str:
        """Очищає назву товару"""
        # Видаляємо ціни та коди
        name = re.sub(r'\d+[.,]\d{2}', '', line)
        name = re.sub(r'[xх*×]\s*\d+', '', name)
        name = re.sub(r'штрих-код[:\s]*\d+', '', name, flags=re.IGNORECASE)
        name = re.sub(r'код\s+уктзед[:\s]*\d+', '', name, flags=re.IGNORECASE)
        name = re.sub(r'-?\s*[АA]\s*$', '', name)
        
        # Видаляємо зайві символи
        name = re.sub(r'[^\w\sА-Яа-яІіЇїЄєҐґ]', ' ', name)
        name = ' '.join(name.split())
        
        return name.strip()
    
    def _guess_category(self, product_name: str) -> str:
        """Вгадує категорію товару"""
        name_lower = product_name.lower()
        
        # Перевіряємо ключові слова
        if any(word in name_lower for word in ['вода', 'пиво', 'сік', 'напій']):
            return 'напої'
        elif any(word in name_lower for word in ['молоко', 'сметана', 'йогурт']):
            return 'молочні продукти' 
        elif any(word in name_lower for word in ['каша', 'крупа', 'зірка']):
            return 'крупи та каші'
        elif any(word in name_lower for word in ['морозиво', 'торт', 'коржі']):
            return 'кондитерські вироби'
        elif any(word in name_lower for word in ['чипси']):
            return 'снеки'
        else:
            return 'інше'
    
    def _deduplicate_items(self, items: List[Dict]) -> List[Dict]:
        """Видаляє дублікати"""
        unique_items = []
        seen_names = set()
        
        for item in items:
            name_key = item['name'].lower().strip()
            if name_key not in seen_names and len(name_key) >= 3:
                seen_names.add(name_key)
                unique_items.append(item)
        
        return unique_items
    
    def _calculate_total_amount(self, text: str, items: List[Dict]) -> float:
        """Розраховує загальну суму"""
        # Спочатку шукаємо явно вказану суму
        patterns = [
            r'безготівкова[:\s]*(\d+[.,]\d{2})\s*грн',
            r'до\s+сплати[:\s]*(\d+[.,]\d{2})',
            r'сума[:\s]*(\d+[.,]\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return float(match.group(1).replace(',', '.'))
        
        # Інакше сумуємо товари
        return sum(item['price'] for item in items)
    
    def _extract_date_enhanced(self, text: str) -> str:
        """Покращене витягування дати"""
        date_patterns = [
            r'(\d{1,2}\.\d{1,2}\.\d{4})',
            r'(\d{1,2}\.\d{1,2}\.\d{2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_receipt_number_enhanced(self, text: str) -> str:
        """Покращене витягування номера чека"""
        patterns = [
            r'чек\s*№?\s*(\d+)',
            r'№\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1)
        return None
    
    def _categorize_items(self, items: List[Dict]) -> Dict[str, Dict]:
        """Категоризація товарів"""
        categorized = {}
        
        for item in items:
            category = item['category']
            if category not in categorized:
                categorized[category] = {
                    'items': [],
                    'total_amount': 0.0,
                    'item_count': 0
                }
            
            categorized[category]['items'].append(item)
            categorized[category]['total_amount'] += item['price']
            categorized[category]['item_count'] += 1
        
        return categorized


def test_enhanced_parser():
    """Тестуємо покращений парсер"""
    parser = TavriaReceiptParserEnhanced()
    
    receipts_dir = "/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/receipts"
    receipt_files = [f for f in os.listdir(receipts_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    for receipt_file in sorted(receipt_files):
        receipt_path = os.path.join(receipts_dir, receipt_file)
        print(f"\n{'='*60}")
        print(f"Тестуємо покращений парсер: {receipt_file}")
        print(f"{'='*60}")
        
        result = parser.parse_receipt_manual(receipt_path)
        if result:
            print(f"\n✅ РЕЗУЛЬТАТ:")
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
    test_enhanced_parser()
