"""
Безкоштовний парсер чеків на основі Tesseract OCR
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

logger = logging.getLogger(__name__)

class FreeReceiptParser:
    """
    Безкоштовний парсер чеків з використанням тільки Tesseract OCR
    """
    
    def __init__(self):
        self.common_store_patterns = {
            'АТБ': [r'АТБ', r'atb'],
            'Сільпо': [r'сільпо', r'silpo'],
            'Novus': [r'novus', r'новус'],
            'Ашан': [r'ашан', r'auchan'],
            'Метро': [r'метро', r'metro'],
            'Фора': [r'фора', r'fora'],
            'MIDA': [r'МІДА', r'MIDA', r'mid\.ua', r'ЛЮТІКОВ'],
            'Varus': [r'varus', r'варус'],
            'EkoMarket': [r'еко[\s\-]*маркет', r'eco[\s\-]*market']
        }
        
        self.amount_patterns = [
            r'(?:сума|всього|разом|итого|total|sum|до\s+сплати|безготівков)[\s:]*?(\d+[.,]\d{2})',
            r'(?:сума|всього|разом|итого|total|sum)[\s:]*?(\d+)',
            r'(\d+[.,]\d{2})[\s]*(?:грн|uah|₴)',
            r'^[\s]*?(\d+[.,]\d{2})[\s]*?$'
        ]
        
        self.date_patterns = [
            r'(\d{2}[./-]\d{2}[./-]\d{4})',
            r'(\d{4}[./-]\d{2}[./-]\d{2})',
            r'(\d{2}[./-]\d{2}[./-]\d{2})'
        ]

    def parse_receipt(self, image_path: str) -> Dict:
        """
        Розпізнає чек з використанням безкоштовного OCR
        """
        try:
            # Відкриваємо зображення
            image = Image.open(image_path)
            
            # Спробуємо кілька варіантів обробки зображення
            results = []
            
            # Варіант 1: Базова обробка
            processed_image1 = self._preprocess_basic(image.copy())
            text1 = self._extract_text(processed_image1)
            if text1:
                result1 = self._parse_text(text1)
                if result1:
                    results.append(result1)
            
            # Варіант 2: Агресивна обробка для поганих фото
            processed_image2 = self._preprocess_aggressive(image.copy())
            text2 = self._extract_text(processed_image2)
            if text2 and text2 != text1:
                result2 = self._parse_text(text2)
                if result2:
                    results.append(result2)
            
            # Варіант 3: Консервативна обробка для чітких фото
            processed_image3 = self._preprocess_conservative(image.copy())
            text3 = self._extract_text(processed_image3)
            if text3 and text3 != text1 and text3 != text2:
                result3 = self._parse_text(text3)
                if result3:
                    results.append(result3)
            
            # Вибираємо найкращий результат
            if results:
                return self._choose_best_result(results)
            
            return None
            
        except Exception as e:
            logger.error(f"Помилка при розпізнаванні чеку: {e}")
            return None

    def _preprocess_basic(self, image: Image.Image) -> Image.Image:
        """Базова обробка зображення"""
        # Конвертуємо в градації сірого
        if image.mode != 'L':
            image = image.convert('L')
        
        # Збільшуємо розмір, якщо зображення мале
        width, height = image.size
        if width < 800 or height < 800:
            scale_factor = max(800/width, 800/height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Покращуємо контрастність
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Покращуємо різкість
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)
        
        return image

    def _preprocess_aggressive(self, image: Image.Image) -> Image.Image:
        """Агресивна обробка для поганих фото"""
        # Конвертуємо в градації сірого
        if image.mode != 'L':
            image = image.convert('L')
        
        # Сильно збільшуємо розмір
        width, height = image.size
        scale_factor = max(1200/width, 1200/height)
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Сильно збільшуємо контрастність
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(3.0)
        
        # Сильно збільшуємо різкість
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(3.0)
        
        # Застосовуємо фільтри
        image = image.filter(ImageFilter.MedianFilter())
        image = image.filter(ImageFilter.SHARPEN)
        
        return image

    def _preprocess_conservative(self, image: Image.Image) -> Image.Image:
        """Консервативна обробка для чітких фото"""
        # Конвертуємо в градації сірого
        if image.mode != 'L':
            image = image.convert('L')
        
        # Легке покращення
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        
        return image

    def _extract_text(self, image: Image.Image) -> str:
        """Витягує текст з зображення"""
        try:
            # Спробуємо різні конфігурації OCR
            configs = [
                '--oem 3 --psm 6',  # Основний режим
                '--oem 3 --psm 4',  # Одна колонка тексту
                '--oem 3 --psm 3',  # Автоматичне визначення
                '--oem 3 --psm 11', # Розрізнений текст
            ]
            
            best_text = ""
            max_length = 0
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(image, lang='ukr+eng', config=config)
                    if len(text) > max_length:
                        max_length = len(text)
                        best_text = text
                except:
                    continue
            
            return best_text
            
        except Exception as e:
            logger.error(f"Помилка при витягуванні тексту: {e}")
            return ""

    def _parse_text(self, text: str) -> Optional[Dict]:
        """Парсить текст чеку"""
        if not text or len(text.strip()) < 10:
            return None
        
        try:
            result = {
                'store_name': self._extract_store_name(text),
                'total_amount': self._extract_total_amount(text),
                'date': self._extract_date(text),
                'items': self._extract_items(text),
                'raw_text': text
            }
            
            # Перевіряємо мінімальні вимоги
            if result['total_amount'] <= 0:
                return None
            
            return result
            
        except Exception as e:
            logger.error(f"Помилка при парсингу тексту: {e}")
            return None

    def _extract_store_name(self, text: str) -> str:
        """Витягує назву магазину"""
        text_lower = text.lower()
        
        for store, patterns in self.common_store_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return store
        
        # Якщо не знайшли відомий магазин, беремо перший рядок
        lines = text.strip().split('\n')
        for line in lines[:3]:  # Перші 3 рядки
            line = line.strip()
            if len(line) > 3 and not re.match(r'^\d', line):
                return line
        
        return 'Невідомий магазин'

    def _extract_total_amount(self, text: str) -> float:
        """Витягує загальну суму"""
        # Спочатку шукаємо за ключовими словами
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                for match in matches:
                    try:
                        amount = float(match.replace(',', '.'))
                        if 1 <= amount <= 50000:  # Розумні межі для чеку
                            return amount
                    except ValueError:
                        continue
        
        # Якщо не знайшли за ключовими словами, шукаємо всі числа
        all_amounts = re.findall(r'\d+[.,]\d{2}', text)
        if all_amounts:
            amounts = []
            for amount_str in all_amounts:
                try:
                    amount = float(amount_str.replace(',', '.'))
                    if 1 <= amount <= 50000:
                        amounts.append(amount)
                except ValueError:
                    continue
            
            # Повертаємо найбільшу суму (зазвичай це загальна сума)
            if amounts:
                return max(amounts)
        
        return 0.0

    def _extract_date(self, text: str) -> datetime:
        """Витягує дату"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                # Спробуємо різні формати
                formats = [
                    '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y',
                    '%Y.%m.%d', '%Y/%m/%d', '%Y-%m-%d',
                    '%d.%m.%y', '%d/%m/%y', '%d-%m-%y'
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
        
        return datetime.now()

    def _extract_items(self, text: str) -> List[Dict]:
        """Витягує список товарів"""
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Шукаємо рядки з цінами
            price_matches = re.findall(r'\d+[.,]\d{2}', line)
            if price_matches:
                # Беремо останню ціну в рядку
                price_str = price_matches[-1]
                try:
                    price = float(price_str.replace(',', '.'))
                    if 0.1 <= price <= 5000:  # Розумні межі для товару
                        # Витягуємо назву товару (все що перед ціною)
                        name_part = line
                        for price_match in price_matches:
                            name_part = name_part.replace(price_match, '', 1)
                        
                        name = re.sub(r'[^\w\sА-Яа-яІіЇїЄєҐґ]', ' ', name_part).strip()
                        
                        if len(name) > 2:
                            items.append({
                                'name': name,
                                'price': price,
                                'quantity': 1
                            })
                except ValueError:
                    continue
        
        return items

    def _choose_best_result(self, results: List[Dict]) -> Dict:
        """Вибирає найкращий результат з кількох варіантів"""
        if not results:
            return None
        
        if len(results) == 1:
            return results[0]
        
        # Оцінюємо результати за кількістю розпізнаних товарів та наявністю суми
        best_result = None
        best_score = 0
        
        for result in results:
            score = 0
            
            # Бали за наявність суми
            if result.get('total_amount', 0) > 0:
                score += 10
            
            # Бали за кількість товарів
            items_count = len(result.get('items', []))
            score += items_count * 2
            
            # Бали за наявність назви магазину
            if result.get('store_name') and result['store_name'] != 'Невідомий магазин':
                score += 5
            
            # Бали за довжину тексту (більше тексту = краще розпізнавання)
            text_length = len(result.get('raw_text', ''))
            score += min(text_length / 100, 10)
            
            if score > best_score:
                best_score = score
                best_result = result
        
        return best_result

# Створюємо екземпляр для використання
free_receipt_parser = FreeReceiptParser()
