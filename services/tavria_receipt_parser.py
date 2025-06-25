#!/usr/bin/env python3
"""
Спеціалізований парсер чеків для магазину "Таврія В"
Версія з покращеним розпізнаванням конкретних товарів
"""

import re
import logging
from typing import Dict, List, Optional
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import cv2
import numpy as np

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TavriaReceiptParser:
    """
    Спеціалізований клас для розпізнавання чеків магазину "Таврія В"
    """
    
    def __init__(self):
        # Конкретні товари, які ми знайшли в чеках
        self.known_products = {
            'коньяк таврія премізм': {
                'category': 'алкоголь',
                'patterns': [r'коньяк.*таврія.*премізм', r'премізм.*0[.,]5', r'таврія.*премізм']
            },
            'mecklenburger dunkel': {
                'category': 'алкоголь',
                'patterns': [r'mecklenburger.*dunkel', r'мекленбургер.*dunkel', r'сесенбовове', r'0[.,]5.*л.*dunkel']
            },
            'mecklenburger weisser': {
                'category': 'алкоголь', 
                'patterns': [r'mecklenburger.*weisser', r'мекленбургер.*weisser', r'0[.,]5.*л.*weisser']
            },
            'корона екстра': {
                'category': 'алкоголь', 
                'patterns': [r'корона.*екстра', r'corona.*extra', r'0[.,]33.*л.*скл', r'poha.*ekctpa']
            },
            'coca cola': {
                'category': 'напої',
                'patterns': [r'coca.*cola', r'кока.*кола', r'напій.*б/алк.*coca', r'0[.,]33.*л.*van', r'напій.*б/алк.*бан']
            },
            'чипси la пательня': {
                'category': 'снеки',
                'patterns': [r'чипси.*la.*пательня', r'м\'ясна.*пательня', r'чнпси.*la.*пательня', r'пательня.*гри']
            },
            'каша обсяночка': {
                'category': 'крупи',
                'patterns': [r'каша.*обсяночка', r'обсяночка.*450.*г', r'450.*г.*асорті', r'10.*смак', r'cwakib']
            },
            'біфідойогурт активіа': {
                'category': 'молочні продукти',
                'patterns': [r'біфідо.*активіа', r'активіа.*2[.,]2%', r'манго.*пер', r'біфідоногорт.*актив', r'akthbia', r'180.*г.*стак']
            },
            'морозиво три ведмеді monaco': {
                'category': 'морозиво',
                'patterns': [r'морозиво.*три.*ведмеді', r'три.*ведмеді.*monaco', r'75.*г.*ескі', r'moposheo.*tph.*ведмеді', r'monaco.*ескі']
            },
            'сметана славія': {
                'category': 'молочні продукти',
                'patterns': [r'сметана.*славія', r'славія.*15%', r'350.*г.*п/е']
            },
            'коржі merci': {
                'category': 'кондитерські вироби',
                'patterns': [r'коржі.*д/торта', r'коржі.*merci', r'500.*г.*чорного', r'лайвом', r'merci.*500']
            },
            'українська зірка гречана': {
                'category': 'крупи',
                'patterns': [r'українська.*зірка.*гречана', r'зірка.*гречана', r'гречана.*зірка']
            },
            'українська зірка пропасений': {
                'category': 'крупи', 
                'patterns': [r'українська.*зірка.*пропасений', r'зірка.*пропасений', r'пропасений.*зірка']
            },
            'вода моршинська спорт': {
                'category': 'напої',
                'patterns': [r'вода.*моршинська.*спорт', r'моршинська.*0[.,]7', r'б/газ.*спорт']
            }
        }
        
        self.store_patterns = [
            r'таврія.*плюс',
            r'таврія.*в',
            r'ставрія.*плюс',  # OCR може спотворювати
            r'аврія',          # Часткове розпізнавання
            r'tavria.*plus',
            r'торговельний.*центр.*таврія',
            r'торговельний.*центр.*кафе',
            r'торговельний.*центр.*пефій',  # OCR помилка
            r'товговельним.*пецій',  # OCR помилка
            r'центр.*кафе.*таврія',
            r'торговельний.*комплекс',
            r'таврія.*премізм',  # Продукт магазину
            r'nтаврі[яa]',     # OCR варіації
            r'таврі[а-я].*[плюc]',
            r'центрекдо',      # OCR помилка
            r'торговельний.*центрек',
            r'nn.*ставрія.*плюс',  # точний варіант з першого чека
            r'ставрія'         # коротший варіант
        ]
        
        # Спеціальні шаблони для цін
        self.price_patterns = [
            r'(\d+[.,]\d{2})\s*[xх*×]\s*(\d+)',  # ціна x кількість
            r'(\d+[.,]\d{2})\s*грн',             # ціна грн
            r'(\d+[.,]\d{2})\s*-?\s*[АA]',       # ціна -А (розрахунок)
        ]
        
    def parse_receipt(self, image_path: str) -> Dict:
        """Головний метод парсингу чека"""
        try:
            # Розпізнаємо текст
            text = self._extract_text_enhanced(image_path)
            
            # Перевіряємо, чи це Таврія В
            if not self._is_tavria_receipt(text):
                logger.info("Це не чек з магазину Таврія В")
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
            
            logger.info(f"Успішно розпізнано чек Таврія В: {len(items)} товарів, сума: {total_amount}")
            
            return result
            
        except Exception as e:
            logger.error(f"Помилка при парсингу чека {image_path}: {str(e)}")
            return None
    
    def _preprocess_image(self, image_path: str) -> List[Image.Image]:
        """Покращує якість зображення для кращого OCR"""
        try:
            # Завантажуємо зображення
            original = Image.open(image_path)
            
            # Конвертуємо в RGB якщо потрібно
            if original.mode != 'RGB':
                original = original.convert('RGB')
            
            processed_images = []
            
            # 1. Оригінальне зображення
            processed_images.append(original)
            
            # 2. Збільшення контрасту
            enhancer = ImageEnhance.Contrast(original)
            high_contrast = enhancer.enhance(2.0)
            processed_images.append(high_contrast)
            
            # 3. Збільшення різкості
            enhancer = ImageEnhance.Sharpness(original)
            sharp = enhancer.enhance(2.0)
            processed_images.append(sharp)
            
            # 4. Обробка через OpenCV
            # Конвертуємо в numpy array
            img_array = np.array(original)
            
            # Конвертуємо в сірий
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Застосовуємо адаптивний поріг
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            # Конвертуємо назад в PIL
            cv_processed = Image.fromarray(thresh)
            processed_images.append(cv_processed)
            
            # 5. Морфологічні операції для очищення шуму
            kernel = np.ones((1,1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            cleaned_img = Image.fromarray(cleaned)
            processed_images.append(cleaned_img)
            
            return processed_images
            
        except Exception as e:
            logger.error(f"Помилка обробки зображення: {str(e)}")
            # Повертаємо оригінальне зображення у випадку помилки
            try:
                return [Image.open(image_path)]
            except:
                return []

    def _extract_text_enhanced(self, image_path: str) -> str:
        """Покращене витягування тексту з множинною обробкою"""
        try:
            # Обробляємо зображення різними способами
            processed_images = self._preprocess_image(image_path)
            
            all_texts = []
            
            # Тестуємо різні конфігурації OCR
            configs = [
                '--oem 3 --psm 6',
                '--oem 3 --psm 4', 
                '--oem 3 --psm 3',
                '--oem 1 --psm 6',
                r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЮЯабвгдежзийклмнопрстуфхцчшщьюяabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.,:\\-+*/=()№% '
            ]
            
            # Для кожного обробленого зображення пробуємо різні конфігурації
            for image in processed_images:
                for config in configs:
                    try:
                        text = pytesseract.image_to_string(image, lang='ukr+eng', config=config)
                        if text.strip():
                            all_texts.append(text)
                    except:
                        continue
            
            # Спочатку перевіряємо, чи якийсь з текстів містить Таврію В
            best_text = ""
            for text in all_texts:
                text_lower = text.lower()
                for pattern in self.store_patterns:
                    if re.search(pattern, text_lower):
                        best_text = text
                        break
                if best_text:
                    break
            
            # Якщо не знайшли Таврію В, берём найдовший текст
            if not best_text:
                best_text = max(all_texts, key=len) if all_texts else ""
                
            return best_text
            
        except Exception as e:
            logger.error(f"Помилка OCR: {str(e)}")
            return ""
    
    def _is_tavria_receipt(self, text: str) -> bool:
        """Перевіряє чи це чек з Таврії В"""
        text_lower = text.lower()
        for pattern in self.store_patterns:
            if re.search(pattern, text_lower):
                logger.info(f"Знайдено магазин Таврія В за шаблоном: {pattern}")
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
        
        # Пошук товарів за ключовими словами
        keyword_based_items = self._find_products_by_keywords(text)
        items.extend(keyword_based_items)
        
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
        """Покращене витягування ціни з врахуванням структури чека"""
        if not line:
            return 0.0
        
        # Шукаємо різні формати цін
        price_patterns = [
            # Формат: ціна x кількість = загальна_ціна -А
            r'(\d+[.,]\d{2})\s*[xх*×]\s*(\d+)\s*=?\s*(\d+[.,]\d{2})\s*-?\s*[АA]',
            # Формат: ціна x кількість  
            r'(\d+[.,]\d{2})\s*[xх*×]\s*(\d+)',
            # Формат: ціна -А (найкращий індикатор товару)
            r'(\d+[.,]\d{2})\s*-?\s*[АA]',
            # Формат: ціна грн
            r'(\d+[.,]\d{2})\s*грн',
            # Просто ціна в кінці рядка
            r'(\d+[.,]\d{2})(?=\s*$)',
        ]
        
        # Пріоритет для форматів з -А (це точно товари)
        for i, pattern in enumerate(price_patterns):
            match = re.search(pattern, line)
            if match:
                if i == 0:  # ціна x кількість = загальна -А
                    return float(match.group(3).replace(',', '.'))
                elif i == 1:  # ціна x кількість
                    unit_price = float(match.group(1).replace(',', '.'))
                    quantity = int(match.group(2))
                    return unit_price * quantity
                else:  # інші формати
                    price = float(match.group(1).replace(',', '.'))
                    # Фільтруємо неймовірні ціни
                    if 0.1 <= price <= 2000:
                        return price
        
        return 0.0
    
    def _find_additional_products(self, text: str) -> List[Dict]:
        """Покращений пошук додаткових товарів за структурою чека"""
        items = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if len(line) < 3:
                i += 1
                continue
            
            # Пропускаємо службові рядки
            if self._is_service_line(line):
                i += 1
                continue
            
            # Шукаємо рядки, що містять штрих-код + назву товару
            if 'штрих-код' in line.lower() or re.search(r'\d{13}', line):
                # Наступний рядок може містити назву товару
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    product_name = self._extract_product_name_from_line(next_line)
                    
                    if product_name:
                        # Шукаємо ціну в наступних рядках
                        price = 0.0
                        for j in range(i + 1, min(i + 4, len(lines))):
                            price = self._extract_price_from_line_enhanced(lines[j])
                            if price > 0:
                                break
                        
                        if price > 0:
                            category = self._guess_category_enhanced(product_name)
                            items.append({
                                'name': product_name,
                                'price': price,
                                'quantity': 1,
                                'category': category
                            })
                            logger.info(f"Знайдено товар за штрих-кодом: {product_name} - {price} грн")
                i += 2
                continue
            
            # Альтернативний метод: шукаємо рядки з цінами
            price = self._extract_price_from_line_enhanced(line)
            if price > 0:
                product_name = self._extract_product_name_from_line(line)
                if product_name and len(product_name) >= 3:
                    category = self._guess_category_enhanced(product_name)
                    items.append({
                        'name': product_name,
                        'price': price,
                        'quantity': 1,
                        'category': category
                    })
            
            i += 1
        
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
        """Покращений розрахунок загальної суми"""
        # Спочатку шукаємо явно вказану суму в різних форматах
        patterns = [
            r'безготівкова[:\s]*(\d+[.,]\d{2})\s*грн',
            r'до\s+сплати[:\s]*(\d+[.,]\d{2})',
            r'сума[:\s]*(\d+[.,]\d{2})',
            r'всього[:\s]*(\d+[.,]\d{2})',
            # Шукаємо суму в кінці чека
            r'(\d+[.,]\d{2})\s*грн\s*$',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                # Берём найбільшу суму (зазвичай це загальна сума)
                amounts = [float(match.replace(',', '.')) for match in matches]
                max_amount = max(amounts)
                if max_amount > 50:  # Розумна мінімальна сума для чека
                    return max_amount
        
        # Альтернативно: шукаємо найбільшу суму в тексті
        all_amounts = re.findall(r'(\d+[.,]\d{2})', text)
        if all_amounts:
            amounts = [float(amount.replace(',', '.')) for amount in all_amounts]
            amounts = [a for a in amounts if 50 <= a <= 2000]  # Фільтруємо розумні суми
            if amounts:
                return max(amounts)
        
        # Інакше сумуємо товари
        items_total = sum(item['price'] for item in items)
        return items_total if items_total > 0 else 0.0
    
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
    
    def _find_products_by_keywords(self, text: str) -> List[Dict]:
        """Пошук товарів по ключовим словам з відомих товарів"""
        found_items = []
        text_lower = text.lower()
        
        for product_name, product_info in self.known_products.items():
            category = product_info['category']
            patterns = product_info['patterns']
            
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    # Знаходимо ціну рядка з товаром
                    line_start = text_lower.rfind('\n', 0, match.start()) + 1
                    line_end = text_lower.find('\n', match.end())
                    if line_end == -1:
                        line_end = len(text_lower)
                    
                    line = text[line_start:line_end].strip()
                    price = self._extract_price_from_line_enhanced(line)
                    
                    if price > 0:
                        found_items.append({
                            'name': product_name,
                            'price': price,
                            'category': category,
                            'source_line': line
                        })
                        break  # Знайшли товар, переходимо до наступного
        
        return found_items
    
    def _extract_product_name_from_line(self, line: str) -> str:
        """Витягає назву товару з рядка, враховуючи специфіку чеків"""
        if not line or len(line.strip()) < 3:
            return ""
        
        # Видаляємо штрих-коди та службову інформацію
        clean_line = re.sub(r'штрих-код[:\s]*\d+', '', line, flags=re.IGNORECASE)
        clean_line = re.sub(r'код\s+уктзед[:\s]*\d+', '', clean_line, flags=re.IGNORECASE)
        
        # Видаляємо ціни в кінці рядка
        clean_line = re.sub(r'\d+[.,]\d{2}\s*[xх*×]\s*\d+\s*=?\s*\d+[.,]\d{2}\s*-?\s*[АA]?\s*$', '', clean_line)
        clean_line = re.sub(r'\d+[.,]\d{2}\s*-?\s*[АA]?\s*$', '', clean_line)
        clean_line = re.sub(r'\d+[.,]\d{2}\s*грн\s*$', '', clean_line, flags=re.IGNORECASE)
        
        # Видаляємо знижки
        clean_line = re.sub(r'знижка[:\s]*-?\d+[.,]\d{2}', '', clean_line, flags=re.IGNORECASE)
        
        # Очищаємо від зайвих символів але зберігаємо важливі
        clean_line = re.sub(r'[^\w\sА-Яа-яІіЇїЄєҐґ./%-]', ' ', clean_line)
        clean_line = ' '.join(clean_line.split())
        
        # Якщо рядок занадто короткий або містить лише цифри, повертаємо пустий
        if len(clean_line.strip()) < 3 or clean_line.strip().isdigit():
            return ""
        
        return clean_line.strip()

    def _guess_category_enhanced(self, product_name: str) -> str:
        """Покращена категоризація товарів з більш точними правилами"""
        name_lower = product_name.lower()
        
        # Алкогольні напої
        if any(word in name_lower for word in ['пиво', 'beer', 'mecklenburger', 'корона', 'corona', 'коньяк']):
            return 'алкоголь'
        
        # Безалкогольні напої
        elif any(word in name_lower for word in ['вода', 'coca', 'cola', 'кола', 'сік', 'напій']):
            return 'напої'
        
        # Молочні продукти
        elif any(word in name_lower for word in ['молоко', 'сметана', 'йогурт', 'біфідо', 'активіа', 'славія']):
            return 'молочні продукти'
        
        # Крупи та каші
        elif any(word in name_lower for word in ['каша', 'крупа', 'зірка', 'гречана', 'обсяночка', 'вівсяночка', 'асорті']):
            return 'крупи'
        
        # Кондитерські вироби
        elif any(word in name_lower for word in ['морозиво', 'торт', 'коржі', 'merci', 'чорного']):
            return 'кондитерські вироби'
        
        # Снеки
        elif any(word in name_lower for word in ['чипси', 'пательня']):
            return 'снеки'
        
        # Морозиво окремо
        elif any(word in name_lower for word in ['морозиво', 'ескімо', 'ескі', 'ведмеді', 'monaco']):
            return 'морозиво'
        
        else:
            return 'інше'
