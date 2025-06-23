"""
Спеціалізований парсер для чеків магазину MIDA
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional
from PIL import Image
import pytesseract
# Використовуємо тільки безкоштовний OCR без Vision API

logger = logging.getLogger(__name__)

class MidaReceiptParser:
    """
    Клас для розпізнавання чеків магазину MIDA з покращеною точністю
    """
    
    def __init__(self):
        # Використовуємо тільки безкоштовний Tesseract OCR
        self.mida_patterns = {
            'store_indicators': [
                r'ФОП\s+ЛЮТІКОВ\s+ВІТАЛІЙ\s+ВАЛЕРІЮОВИЧ',
                r'ФОП\s+Лютіков\s+В\.\s*В',
                r'MIDA',
                r'МІДА',
                r'mid\.ua',
                r'086\s+22\s+81',  # номер телефону MIDA
                r'Лазурна.*Миколаїв',  # адреса MIDA
                r'2903314199'  # ІД код MIDA
            ],
            'total_patterns': [
                r'СУМА\s+ДО\s+СПЛАТИ:\s*(\d+[.,]\d{2})',
                r'БЕЗГОТІВКОВА[.\s]*БЕЗГОТІВКОВИЙ:\s*(\d+[.,]\d{2})',
                r'Безготівковий\s+(\d+[.,]\d{2})\s*грн',
                r'СУМА\s+(\d+[.,]\d{2})',
                r'До\s+сплати\s+(\d+[.,]\d{2})\s*грн',
                r'Без\s+ПДВ.*?(\d+[.,]\d{2})',
                r'(\d+[.,]\d{2})\s*грн'
            ],
            'item_patterns': [
                r'(\d+[.,]\d{3})\s*[xX×]\s*(\d+[.,]\d{2})\s*(\d+[.,]\d{2})',  # кількість x ціна = сума
                r'([А-Яа-яІіЇїЄєҐґA-Za-z\s]+[а-яё])\s+(\d+[.,]\d{2})',  # назва + ціна
                r'АРТ\.\s*№\s*\d+\s*(\d+)[./]([А-Яа-яІіЇїЄєҐґA-Za-z\s]+)\s*(\d+[.,]\d{2})',
                r'/([А-Яа-яІіЇїЄєҐґA-Za-z\s]+)\s+([а-яё]+)\s+[а-я]+.*?(\d+[.,]\d{2})',  # /Назва товару ... ціна
                r'([А-Яа-яІіЇїЄєҐґ][А-Яа-яІіЇїЄєҐґA-Za-z\s]+)\s*(\d+[.,]\d{2})\s*грн'  # Назва ціна грн
            ],
            'date_patterns': [
                r'(\d{2}[-./]\d{2}[-./]\d{4})\s+(\d{2}:\d{2}:\d{2})',
                r'(\d{2}[-./]\d{2}[-./]\d{4})'
            ]
        }
        
        # Категорії товарів MIDA з покращеними ключовими словами
        self.category_mapping = {
            'напої': ['sprite', 'coca', 'cola', 'вода', 'сік', 'пиво', 'квас', 'лимонад', 'мінералка', 'солод'],
            'солодощі': ['цукерки', 'шоколад', 'печиво', 'тістечко', 'торт', 'цукати', 'мармелад', 'ананас', 'кільце'],
            'м\'ясо': ['ковбаса', 'сосиски', 'шинка', 'бекон', 'м\'ясо', 'фарш', 'котлети'],
            'молочні': ['молоко', 'йогурт', 'кефір', 'сметана', 'творог', 'сир', 'масло'],
            'хліб': ['хліб', 'батон', 'булочка', 'круасан', 'лаваш'],
            'овочі': ['помідор', 'огірок', 'картопля', 'морква', 'цибуля', 'капуста', 'перець'],
            'фрукти': ['яблук', 'банан', 'апельсин', 'мандарин', 'груш', 'виноград', 'ананас', 'кільце'],
            'крупи': ['рис', 'гречка', 'макарони', 'спагеті', 'крупа', 'борошно'],
            'консерви': ['тушонка', 'рибні консерви', 'овочеві консерви', 'соуси'],
            'гігієна': ['зубна паста', 'шампунь', 'мило', 'гель', 'дезодорант']
        }

    def is_mida_receipt(self, text: str) -> bool:
        """Перевіряє, чи це чек з магазину MIDA"""
        text_lower = text.lower()
        
        # Основні індикатори MIDA
        mida_indicators = [
            'міда', 'mida', 'лютіков', 'лазурна.*миколаїв', 
            '2903314199', 'mid.ua', 'інтернет-магазин.*міда'
        ]
        
        for indicator in mida_indicators:
            if re.search(indicator, text_lower):
                logger.info(f"MIDA індикатор знайдено: {indicator}")
                return True
        
        # Перевірка через додаткові шаблони
        for pattern in self.mida_patterns['store_indicators']:
            if re.search(pattern, text, re.IGNORECASE):
                logger.info(f"MIDA індикатор знайдено за шаблоном: {pattern}")
                return True
        
        # Додаткова перевірка для назви в лапках
        if '"міда"' in text_lower or '"mida"' in text_lower:
            logger.info("MIDA знайдено в лапках")
            return True
        
        # Перевірка комбінації індикаторів
        if ('лютіков' in text_lower or 'лазурна' in text_lower) and 'миколаїв' in text_lower:
            logger.info("MIDA знайдено за комбінацією адреси")
            return True
            
        return False

    def parse_receipt(self, image_path: str) -> Dict:
        """
        Розпізнає чек MIDA з використанням безкоштовного Tesseract OCR
        """
        try:
            # Використовуємо тільки OCR розпізнавання
            ocr_result = self._parse_with_ocr(image_path)
            
            if ocr_result and self._is_valid_result(ocr_result):
                return self._enhance_mida_data(ocr_result)
            
            # Якщо OCR не дав результатів, повертаємо None
            logger.warning("OCR не зміг розпізнати чек MIDA")
            return None
                
        except Exception as e:
            logger.error(f"Помилка при розпізнаванні чеку MIDA: {e}")
            return None

    def _parse_with_ocr(self, image_path: str) -> Dict:
        """Розпізнавання з використанням Tesseract OCR з покращеною обробкою"""
        try:
            # Відкриваємо і обробляємо зображення
            image = Image.open(image_path)
            
            # Покращуємо якість для OCR
            image = self._preprocess_image(image)
            
            # Розпізнаємо текст з кращими налаштуваннями для чеків
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюяІіЇїЄєҐґ.,:/()- '
            text = pytesseract.image_to_string(image, lang='ukr+eng', config=custom_config)
            
            # Додатково спробуємо з іншими PSM режимами, якщо перший не дав результату
            if not text.strip() or len(text.strip()) < 20:
                logger.info("Спробуємо інший режим розпізнавання")
                text = pytesseract.image_to_string(image, lang='ukr+eng', config='--oem 3 --psm 4')
            
            # Перевіряємо, чи це MIDA
            if not self.is_mida_receipt(text):
                logger.info("Чек не розпізнано як MIDA")
                return None
                
            # Витягуємо дані
            result = {
                'store_name': 'MIDA',
                'total_amount': self._extract_total_amount(text),
                'date': self._extract_date(text),
                'items': self._extract_items(text),
                'categorized_items': {},
                'raw_text': text
            }
            
            # Категоризуємо товари
            result['categorized_items'] = self._categorize_items(result['items'])
            
            logger.info(f"OCR розпізнав: {len(result['items'])} товарів, сума: {result['total_amount']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Помилка OCR розпізнавання: {e}")
            return None

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Покращення зображення для OCR з додатковими оптимізаціями для MIDA"""
        # Конвертуємо в градації сірого
        if image.mode != 'L':
            image = image.convert('L')
        
        # Збільшуємо розмір для кращого розпізнавання дрібного тексту
        width, height = image.size
        if width < 1000 or height < 1000:
            scale_factor = max(1000/width, 1000/height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Збільшуємо контрастність
        from PIL import ImageEnhance, ImageFilter
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5)
        
        # Збільшуємо різкість
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        # Застосовуємо фільтр для зменшення шуму
        image = image.filter(ImageFilter.MedianFilter())
        
        return image

    def _extract_total_amount(self, text: str) -> float:
        """Витягує загальну суму з тексту"""
        for pattern in self.mida_patterns['total_patterns']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '.')
                    return float(amount_str)
                except (ValueError, IndexError):
                    continue
        
        # Якщо не знайшли за шаблонами, шукаємо найбільшу суму
        amounts = re.findall(r'\d+[.,]\d{2}', text)
        if amounts:
            try:
                return max([float(amount.replace(',', '.')) for amount in amounts])
            except ValueError:
                pass
                
        return 0.0

    def _extract_date(self, text: str) -> datetime:
        """Витягує дату з тексту"""
        for pattern in self.mida_patterns['date_patterns']:
            match = re.search(pattern, text)
            if match:
                try:
                    date_str = match.group(1)
                    # Спробуємо різні формати
                    for fmt in ['%d-%m-%Y', '%d.%m.%Y', '%d/%m/%Y']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except IndexError:
                    continue
        
        return datetime.now()

    def _extract_items(self, text: str) -> List[Dict]:
        """Витягує список товарів з тексту з покращеним розпізнаванням для MIDA"""
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Пропускаємо службові рядки
            if any(skip in line.lower() for skip in ['дякуємо', 'інтернет-магазин', 'номер для', 'оплата', 'торговець', 'термінал', 'приватбанк', 'підпис', 'безготівков', 'сума', 'заокруглення']):
                continue
                
            # Шукаємо специфічні шаблони MIDA товарів
            # Шаблон 1: кількість X ціна (назва товару в наступному рядку або в тому ж)
            pattern1 = r'(\d+[.,]\d{3})\s*[xX×]\s*(\d+[.,]\d{2})'
            match1 = re.search(pattern1, line)
            if match1:
                try:
                    quantity = float(match1.group(1).replace(',', '.'))
                    unit_price = float(match1.group(2).replace(',', '.'))
                    total_price = quantity * unit_price
                    
                    # Шукаємо назву товару в цьому ж рядку або сусідніх
                    name_part = line.replace(match1.group(0), '').strip()
                    if len(name_part) < 3:
                        # Якщо в поточному рядку немає назви, шукаємо в сусідніх
                        current_idx = lines.index(line.strip()) if line.strip() in lines else -1
                        if current_idx > 0:
                            prev_line = lines[current_idx - 1].strip()
                            if not re.search(r'\d+[.,]\d{2}', prev_line):
                                name_part = prev_line
                    
                    if len(name_part) > 2:
                        # Очищуємо назву від артикулів та кодів
                        name_clean = re.sub(r'АРТ\.?\s*№?\s*\d+', '', name_part)
                        name_clean = re.sub(r'\d+/[а-я]+/[А-Я]/', '', name_clean)
                        name_clean = name_clean.strip()
                        
                        if len(name_clean) > 2:
                            items.append({
                                'name': name_clean,
                                'price': total_price,
                                'quantity': quantity,
                                'unit_price': unit_price
                            })
                            continue
                except (ValueError, IndexError):
                    pass
            
            # Шаблон 2: прямий пошук товарів за назвами (Sprite, цукати, etc.)
            known_products = ['sprite', 'цукати', 'ананас', 'вода', 'сік', 'хліб', 'молоко']
            for product in known_products:
                if product in line.lower():
                    price_match = re.search(r'(\d+[.,]\d{2})', line)
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace(',', '.'))
                            if 1 <= price <= 1000:  # Розумні межі
                                # Витягуємо повну назву товару
                                name_parts = line.split()
                                name = ' '.join([part for part in name_parts if not re.match(r'^\d+[.,]?\d*$', part)])
                                name = re.sub(r'[^\w\sА-Яа-яІіЇїЄєҐґ]', ' ', name).strip()
                                
                                if len(name) > 2:
                                    items.append({
                                        'name': name,
                                        'price': price,
                                        'quantity': 1
                                    })
                                    break
                        except ValueError:
                            continue
            
            # Шаблон 3: загальний пошук рядків з товарами (містять букви та ціну)
            if not any(item['name'].lower() in line.lower() for item in items):
                if re.search(r'[А-Яа-яІіЇїЄєҐґA-Za-z]{3,}', line) and re.search(r'\d+[.,]\d{2}', line):
                    # Пропускаємо рядки з технічною інформацією
                    if not any(tech in line.lower() for tech in ['арт', 'чек', 'прро', 'код', 'термінал', 'rn']):
                        price_match = re.search(r'(\d+[.,]\d{2})', line)
                        if price_match:
                            try:
                                price = float(price_match.group(1).replace(',', '.'))
                                if 1 <= price <= 1000:
                                    # Витягуємо назву (все крім цифр та спеціальних символів)
                                    name = re.sub(r'\d+[.,]?\d*', '', line)
                                    name = re.sub(r'[^\w\sА-Яа-яІіЇїЄєҐґ]', ' ', name)
                                    name = ' '.join(name.split())  # Видаляємо зайві пробіли
                                    
                                    if len(name) > 3:
                                        items.append({
                                            'name': name,
                                            'price': price,
                                            'quantity': 1
                                        })
                            except ValueError:
                                continue
        
        # Видаляємо дублікати на основі схожих назв
        unique_items = []
        for item in items:
            is_duplicate = False
            for existing in unique_items:
                if self._are_similar_items(item['name'], existing['name']):
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_items.append(item)
        
        logger.info(f"Витягнуто {len(unique_items)} унікальних товарів")
        return unique_items

    def _extract_items_simple(self, text: str) -> List[Dict]:
        """Простіше витягування товарів"""
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Шукаємо рядки з ціною
            price_match = re.search(r'(\d+[.,]\d{2})', line)
            if price_match:
                price = float(price_match.group(1).replace(',', '.'))
                # Витягуємо назву товару (все що перед ціною)
                name_part = line[:price_match.start()].strip()
                if len(name_part) > 2 and price > 0:
                    items.append({
                        'name': name_part,
                        'price': price,
                        'quantity': 1
                    })
        
        return items

    def _categorize_items(self, items: List[Dict]) -> Dict[str, List[Dict]]:
        """Категоризує товари за типами"""
        categorized = {}
        
        for item in items:
            category = self._get_item_category(item['name'])
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(item)
        
        # Обчислюємо загальну суму для кожної категорії
        for category in categorized:
            total_price = sum(item['price'] for item in categorized[category])
            categorized[category] = {
                'items': categorized[category],
                'total_amount': total_price,
                'item_count': len(categorized[category])
            }
        
        return categorized

    def _get_item_category(self, item_name: str) -> str:
        """Визначає категорію товару"""
        item_lower = item_name.lower()
        
        for category, keywords in self.category_mapping.items():
            for keyword in keywords:
                if keyword in item_lower:
                    return category
        
        return 'інше'

    def _enhance_mida_data(self, result: Dict) -> Dict:
        """Покращує дані специфічно для MIDA"""
        if not result:
            return result
            
        # Забезпечуємо назву магазину
        result['store_name'] = 'MIDA'
        
        # Додаємо додаткову інформацію
        result['store_info'] = {
            'chain': 'MIDA',
            'format': 'супермаркет',
            'location': 'Миколаїв'
        }
        
        # Категоризуємо товари, якщо це ще не зроблено
        if 'items' in result and 'categorized_items' not in result:
            result['categorized_items'] = self._categorize_items(result['items'])
        
        return result

    def _is_valid_result(self, result: Dict) -> bool:
        """Перевіряє валідність результату"""
        if not result:
            return False
        
        # Перевіряємо наявність загальної суми
        total_amount = result.get('total_amount', 0)
        if not total_amount or total_amount <= 0:
            return False
        
        # Перевіряємо наявність товарів
        items = result.get('items', [])
        if not items:
            return False
        
        return True

    def _are_similar_items(self, name1: str, name2: str) -> bool:
        """Перевіряє схожість назв товарів для видалення дублікатів"""
        name1_clean = name1.lower().strip()
        name2_clean = name2.lower().strip()
        
        # Якщо назви ідентичні
        if name1_clean == name2_clean:
            return True
        
        # Якщо одна назва міститься в іншій
        if name1_clean in name2_clean or name2_clean in name1_clean:
            return True
        
        # Перевіряємо за ключовими словами
        words1 = set(name1_clean.split())
        words2 = set(name2_clean.split())
        
        # Якщо є спільні значущі слова
        common_words = words1.intersection(words2)
        significant_words = {'sprite', 'цукати', 'ананас', 'вода', 'молоко', 'хліб', 'сік'}
        
        for word in common_words:
            if word in significant_words or len(word) > 4:
                return True
        
        return False

# Створюємо екземпляр для використання
mida_receipt_parser = MidaReceiptParser()
