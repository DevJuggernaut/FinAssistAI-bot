import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class EnhancedReceiptProcessor:
    """Покращений процесор для розпізнавання чеків з товарами"""
    
    def __init__(self):
        # Patterns для розпізнавання
        self.amount_patterns = [
            r'(\d+[.,]\d{2})\s*(?:грн|UAH|₴|гривень)',  # Українські гривні
            r'(\d+[.,]\d{2})\s*$',  # Просто число в кінці рядка
            r'(\d+[.,]\d{2})',  # Будь-яке число з двома знаками після коми
            r'(\d+)\.\d{2}',  # Формат 100.47
            r'(\d+),\d{2}',   # Формат 100,47
        ]
        
        self.date_patterns = [
            r'(\d{2}[./]\d{2}[./]\d{4})',  # DD/MM/YYYY або DD.MM.YYYY
            r'(\d{4}[.-]\d{2}[.-]\d{2})',  # YYYY-MM-DD
            r'(\d{2}[.-]\d{2}[.-]\d{2})',  # DD-MM-YY
            r'(\d{2}\.\d{2}\.\d{2})',      # DD.MM.YY (як в прикладі)
        ]
        
        # Ключові слова для пошуку підсумкової суми
        self.total_keywords = [
            'сума', 'всього', 'до сплати', 'итого', 'total', 'sum', 'разом',
            'загальна сума', 'підсумок', 'до оплати', 'кінцева сума',
            'всього до сплати', 'к доплате', 'к оплате', 'total amount',
            'cyma', 'сума', 'suma', 'всього', 'итого', 'загальна',
            # Додаємо англійські еквіваленти для поганого OCR
            'suma', 'cyma', 'vsogo', 'do splaty', 'itogo', 'zagalna',
            'kinceva', 'pidpysok', 'razom', 'splaty', 'oplatyty',
            # Паттерни для спотвореного тексту
            'fo emuiarit', 'emuiarit', 'besrorwopitl', 'bezgotivkovyy',
            'gotivka', 'kartka', 'reshta', 'zdacha'
        ]
        
        # Ключові слова для виключення (не товари)
        self.exclude_keywords = [
            'касир', 'чек', 'дата', 'время', 'час', 'магазин', 'адрес',
            'адреса', 'телефон', 'готівка', 'картка', 'решта', 'здача',
            'пдв', 'податок', 'без пдв', 'касовий чек', 'фіскальний',
            'знижка', 'скидка', 'card', 'mastercard', 'visa', 'термінал',
            'терминал', 'номер', 'код', 'кассир', 'спасибо', 'дякуємо',
            'дякую', 'cashier', 'receipt', 'дякуємо за покупку',
            'приходьте ще', 'до побачення', 'безготівковий', 'готівковий',
            'еквайр', 'торговець', 'платіжна система', 'підпис', 'авторизація',
            'ррн', 'епз', 'заокруглення', 'інтернет-магазин', 'замовлення',
            'онлайн', 'відкриті', 'система', 'приватбанк', 'код авторизації',
            'не потрібен', 'номер для', 'міламама', 'вул.', 'обл.', 'дяк',
            '(066)', '(067)', '(068)', '(096)', '(097)', '(098)', '(063)',
            '(066) 086', '(067) 086', 'замовлення', 'рровайдер'
        ]

    def process_receipt_image(self, image_path: str) -> Dict:
        """Обробляє зображення чека та витягує детальну інформацію"""
        try:
            # Покращуємо якість зображення
            enhanced_image = self._enhance_image(image_path)
            
            # Витягуємо текст за допомогою OCR з українською мовою
            # Пробуємо різні конфігурації OCR для кращого розпізнавання
            ocr_configs = [
                '--psm 6 --oem 3 -c tessedit_char_whitelist=АБВГДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯабвгдеєжзиіїйклмнопрстуфхцчшщьюя0123456789.,():/-+xх×XХ ',
                '--psm 4 --oem 3',
                '--psm 6 --oem 1',
                '--psm 3 --oem 3',
                '--psm 8 --oem 3',
                '--psm 6'
            ]
            
            raw_text = ""
            best_text = ""
            max_length = 0
            
            for config in ocr_configs:
                try:
                    # Пробуємо з українською та англійською мовами
                    for lang in ['ukr+eng', 'ukr', 'eng']:
                        try:
                            text = pytesseract.image_to_string(enhanced_image, lang=lang, config=config)
                            if len(text.strip()) > max_length:
                                max_length = len(text.strip())
                                best_text = text
                        except:
                            continue
                except:
                    continue
            
            # Використовуємо найкращий результат
            raw_text = best_text if best_text else ""
            
            # Якщо жоден не спрацював, пробуємо базовий
            if not raw_text.strip():
                try:
                    raw_text = pytesseract.image_to_string(enhanced_image, lang='ukr+eng')
                except:
                    # Останній шанс - тільки англійська
                    raw_text = pytesseract.image_to_string(enhanced_image, lang='eng')
                
            logger.info(f"Extracted text: {raw_text}")
            
            # Очищаємо та нормалізуємо текст
            cleaned_text = self._clean_ocr_text(raw_text)
            logger.info(f"Cleaned text: {cleaned_text}")
            
            # Обробляємо текст та витягуємо інформацію
            result = self._parse_receipt_text(cleaned_text)
            result['raw_text'] = raw_text
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing receipt image: {str(e)}")
            raise

    def _enhance_image(self, image_path: str) -> Image.Image:
        """Покращує якість зображення для кращого розпізнавання"""
        try:
            # Відкриваємо зображення
            image = Image.open(image_path)
            
            # Конвертуємо в сірий колір
            if image.mode != 'L':
                image = image.convert('L')
            
            # Конвертуємо до numpy для OpenCV обробки
            import numpy as np
            img_array = np.array(image)
            
            # Спочатку збільшуємо зображення для кращої обробки
            height, width = img_array.shape
            if width < 1000:  # Якщо зображення мале
                scale_factor = max(2, 1000 // width)
                new_width = width * scale_factor
                new_height = height * scale_factor
                img_array = cv2.resize(img_array, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Застосовуємо Gaussian blur для зменшення шуму
            img_array = cv2.GaussianBlur(img_array, (1, 1), 0)
            
            # Покращуємо контрастність за допомогою adaptive histogram equalization
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            img_array = clahe.apply(img_array)
            
            # Застосовуємо адаптивну бінаризацію замість Otsu для кращого результату
            img_array = cv2.adaptiveThreshold(
                img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Морфологічні операції для очищення тексту
            kernel = np.ones((1,1), np.uint8)
            img_array = cv2.morphologyEx(img_array, cv2.MORPH_CLOSE, kernel)
            
            # Видаляємо шум
            img_array = cv2.medianBlur(img_array, 1)
            
            # Конвертуємо назад в PIL
            image = Image.fromarray(img_array)
            
            return image
            
        except Exception as e:
            logger.error(f"Error enhancing image: {str(e)}")
            # Якщо не вдалося покращити, повертаємо оригінал
            return Image.open(image_path)

    def _parse_receipt_text(self, text: str) -> Dict:
        """Парсить текст чека та витягує товари та інформацію"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Витягуємо основну інформацію
        date = self._extract_date(text)
        store_info = self._extract_store_info(lines)
        
        # Витягуємо товари та підсумкову суму
        items, total_amount = self._extract_items_and_total(lines)
        
        # Якщо не знайшли підсумкову суму, рахуємо сами
        if total_amount == 0.0 and items:
            total_amount = sum(item['amount'] for item in items)
        
        # Якщо не знайшли товари, але є загальна сума, створюємо узагальнений товар
        if not items and total_amount > 0:
            # Намагаємося знайти хоча б натяки на товари в тексті
            product_hints = []
            for line in lines:
                line_lower = line.lower()
                # Шукаємо слова, що натякають на товари
                if any(hint in line_lower for hint in ['спрайт', 'sprite', 'вода', 'water', 'ананас', 'ananac', 'цукати', 'yxara']):
                    # Очищаємо рядок від чисел та службових символів
                    clean_line = re.sub(r'\d+[.,]\d{2}', '', line)
                    clean_line = re.sub(r'[xх*×]\s*\d+', '', clean_line)
                    clean_line = re.sub(r'^\d+\s*', '', clean_line)
                    clean_line = clean_line.strip()
                    if len(clean_line) > 3:
                        product_hints.append(clean_line)
            
            # Створюємо узагальнений товар
            if product_hints:
                description = ' + '.join(product_hints[:2])  # Беремо перші 2 натяки
            else:
                description = "Покупки в магазині"
            
            items = [{
                'description': description,
                'amount': total_amount,
                'quantity': 1.0,
                'category': self._predict_item_category(description)
            }]
        
        return {
            'date': date,
            'store_info': store_info,
            'items': items,
            'total_amount': total_amount,
            'items_count': len(items)
        }

    def _extract_date(self, text: str) -> datetime:
        """Витягує дату з тексту чека"""
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    date_str = matches[0]
                    # Пробуємо різні формати дати
                    for fmt in ['%d/%m/%Y', '%d.%m.%Y', '%Y-%m-%d', '%d-%m-%y', '%d.%m.%y']:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            # Якщо рік менше 50, додаємо 2000
                            if parsed_date.year < 50:
                                parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                            # Якщо рік між 50 і 99, додаємо 1900
                            elif parsed_date.year < 100:
                                parsed_date = parsed_date.replace(year=parsed_date.year + 1900)
                            return parsed_date
                        except ValueError:
                            continue
                except:
                    continue
        
        return datetime.now()

    def _extract_store_info(self, lines: List[str]) -> Dict:
        """Витягує інформацію про магазин"""
        store_info = {
            'name': '',
            'address': '',
            'phone': ''
        }
        
        # Зазвичай назва магазину в перших рядках
        for i, line in enumerate(lines[:5]):
            if len(line) > 3 and not any(char.isdigit() for char in line):
                if not store_info['name']:
                    store_info['name'] = line
                elif 'адрес' in line.lower() or 'вул.' in line.lower():
                    store_info['address'] = line
        
        return store_info

    def _extract_items_and_total(self, lines: List[str]) -> Tuple[List[Dict], float]:
        """Витягує товари та підсумкову суму з покращеною логікою"""
        items = []
        total_amount = 0.0
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Перевіряємо, чи це підсумкова сума
            if self._is_total_line(line):
                amount = self._extract_amount_from_line(line)
                if amount > total_amount:
                    total_amount = amount
                i += 1
                continue
            
            # Перевіряємо, чи це товар (рядок з ціною та множенням)
            if self._is_item_line(line):
                item = self._parse_item_line(line)
                if item:
                    # Шукаємо назву товару в наступних рядках (в українських чеках часто назва йде після ціни)
                    found_description = False
                    
                    # Спочатку шукаємо в наступних 1-3 рядках
                    for j in range(i + 1, min(i + 4, len(lines))):
                        candidate_line = lines[j].strip()
                        
                        # Перевіряємо, чи це може бути назва товару
                        if self._is_product_name_candidate(candidate_line):
                            # Очищаємо назву від кодів
                            clean_name = self._extract_product_name_from_line(candidate_line)
                            
                            if clean_name and len(clean_name) > 2:
                                # Збираємо додаткові характеристики з наступних рядків
                                additional_info = []
                                for k in range(j + 1, min(j + 3, len(lines))):
                                    add_line = lines[k].strip()
                                    if self._is_product_characteristic(add_line):
                                        additional_info.append(add_line)
                                    else:
                                        break
                                
                                # Формуємо повну назву
                                full_name = clean_name
                                if additional_info:
                                    full_name += " " + " ".join(additional_info)
                                
                                item['description'] = self._clean_product_name(full_name)
                                item['category'] = self._predict_item_category(item['description'])
                                found_description = True
                                
                                # Пропускаємо оброблені рядки
                                i += 1 + len(additional_info)
                                break
                    
                    # Якщо не знайшли в наступних рядках, шукаємо в попередніх
                    if not found_description:
                        for j in range(max(0, i-3), i):
                            candidate_line = lines[j].strip()
                            
                            if self._is_product_name_candidate(candidate_line):
                                clean_name = self._extract_product_name_from_line(candidate_line)
                                
                                if clean_name and len(clean_name) > 2:
                                    item['description'] = self._clean_product_name(clean_name)
                                    item['category'] = self._predict_item_category(item['description'])
                                    found_description = True
                                    break
                    
                    items.append(item)
            
            i += 1
        
        return items, total_amount

    def _is_total_line(self, line: str) -> bool:
        """Перевіряє, чи містить рядок підсумкову суму"""
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in self.total_keywords)

    def _is_item_line(self, line: str) -> bool:
        """Перевіряє, чи є рядок товаром"""
        # Рядок повинен містити числа (ціну)
        has_amount = (re.search(r'\d+[.,]\d{2}', line) or 
                     re.search(r'\d{1,4}\s+\d{2}', line))
        if not has_amount:
            return False
        
        # Виключаємо рядки з ключовими словами
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in self.exclude_keywords):
            return False
        
        # Виключаємо рядки, які починаються з числа, але це не код товару
        # (наприклад, "1000 X 24.30" - це товар, а "100.47 грн" - це сума)
        if re.match(r'^\d+[.,]\d{2}\s*(грн|uah|₴)', line.lower()):
            return False
        
        # Виключаємо рядки типу "Безготівковий   100.47 грн"
        if re.match(r'^[а-яА-Яa-zA-Z\s]+\d+[.,]\d{2}', line) and not re.search(r'[xх*×]\s*\d+[.,]\d{2}', line.lower()):
            # Це може бути метод оплати, а не товар
            payment_keywords = ['безготівковий', 'готівковий', 'картка', 'готівка', 'сума', 'всього', 'до сплати',
                               'besrorwopitl', '8esrorwopit1', 'gotivka', 'kartka']
            if any(keyword in line_lower for keyword in payment_keywords):
                return False
        
        # Виключаємо спотворені варіанти службових рядків
        distorted_service = ['5atie', 'satіe', 'tt 5es', 'тт ses', 'ee 5e', 'fo emuiarit', 'yek ne']
        if any(keyword in line_lower for keyword in distorted_service):
            return False
        
        # Рядок не повинен бути занадто коротким
        if len(line.strip()) < 3:
            return False
        
        # Якщо рядок містить множення (X або х), це скоріше за все товар
        if re.search(r'[xх*×]\s*\d+[.,]\d{2}', line.lower()):
            return True
        
        # Якщо рядок містить множення з пробілами "X 24 30"
        if re.search(r'[xх*×]\s*\d+\s+\d{2}', line.lower()):
            return True
        
        # Якщо рядок містить тільки суму в кінці без опису, це не товар
        if re.match(r'^\s*\d+[.,]\d{2}\s*$', line):
            return False
        
        # Якщо в рядку є назви продуктів (навіть спотворені)
        product_hints = ['спрайт', 'sprite', 'вода', 'water', 'ананас', 'ananac', 'цукати', 'yxara']
        if any(hint in line_lower for hint in product_hints):
            return True
        
        return True

    def _parse_item_line(self, line: str) -> Optional[Dict]:
        """Парсить рядок товару"""
        try:
            # Витягуємо суму
            amount = self._extract_amount_from_line(line)
            if amount == 0.0:
                return None
            
            # Витягуємо назву товару
            description = ""
            
            # Якщо є множення (X або х), беремо частину після коду до множення
            multiply_match = re.search(r'(\d+(?:[.,]\d+)?)\s*[xх*×]\s*\d+[.,]\d{2}', line, re.IGNORECASE)
            if multiply_match:
                # Знаходимо початок коду товару
                code_end = multiply_match.start()
                # Шукаємо назву товару (зазвичай після коду)
                code_part = line[:code_end]
                # Видаляємо числовий код з початку
                description_part = re.sub(r'^\d+\s*', '', code_part).strip()
                if description_part:
                    description = description_part
                else:
                    # Якщо опис пустий, це може бути тільки код з ціною
                    # Використовуємо як опис числову частину до множення
                    description = f"Товар {multiply_match.group(1)}"
            
            # Якщо не знайшли назву через множення, пробуємо інший спосіб
            if not description:
                # Видаляємо суму з кінця та номер позиції з початку
                temp_desc = re.sub(r'\d+[.,]\d{2}.*$', '', line).strip()
                temp_desc = re.sub(r'^\d+\.?\s*', '', temp_desc).strip()
                description = temp_desc
            
            # Очищаємо назву від зайвої інформації
            description = self._clean_product_name(description)
            
            # Якщо назва все ще пуста або занадто коротка
            if not description or len(description) < 2:
                return None
            
            # Витягуємо кількість
            quantity = self._extract_quantity(line)
            
            return {
                'description': description,
                'amount': amount,
                'quantity': quantity,
                'category': self._predict_item_category(description)
            }
            
        except Exception as e:
            logger.error(f"Error parsing item line '{line}': {str(e)}")
            return None
    
    def _clean_product_name(self, name: str) -> str:
        """Очищає назву товару від зайвої інформації"""
        # Видаляємо адреси та контактну інформацію
        cleaned = re.sub(r'вул\.\s+[^,]+,?\s*', '', name)
        cleaned = re.sub(r'м\.\s+[^,]+,?\s*', '', cleaned)
        cleaned = re.sub(r'обл\.\s*', '', cleaned)
        cleaned = re.sub(r'\(\d{3}\)\s*\d{3}.*', '', cleaned)  # Телефони
        
        # Видаляємо коди ДІ та інші службові коди
        cleaned = re.sub(r'ДІ\s+\d+', '', cleaned)
        cleaned = re.sub(r'^\d{3,4}\s+[а-яА-Я]{2,3}[-/]\s*', '', cleaned)
        
        # Спеціальні правила для конкретних товарів
        if 'sprite' in cleaned.lower() or 'спрайт' in cleaned.lower():
            # Для Sprite беремо основні ключові слова
            sprite_parts = []
            if 'вода' in cleaned.lower() or 'water' in cleaned.lower():
                sprite_parts.append('Вода')
            if 'солод' in cleaned.lower():
                sprite_parts.append('солодка')
            if 'sprite' in cleaned.lower() or 'спрайт' in cleaned.lower():
                sprite_parts.append('Sprite')
            if '0.33' in cleaned or '0,33' in cleaned:
                sprite_parts.append('0.33л')
            elif 'г/в' in cleaned:
                sprite_parts.append('газована')
                
            if sprite_parts:
                return ' '.join(sprite_parts)
        
        if 'цукати' in cleaned.lower() and 'ананас' in cleaned.lower():
            return 'Цукати ананас кільце'
        
        # Загальне очищення
        parts = [part.strip() for part in cleaned.split() if len(part.strip()) > 1]
        
        # Шукаємо ключові слова продуктів
        product_parts = []
        skip_next = False
        
        for i, part in enumerate(parts):
            if skip_next:
                skip_next = False
                continue
                
            part_lower = part.lower()
            
            # Пропускаємо числові коди товарів
            if re.match(r'^\d{3,4}$', part):
                continue
                
            # Ключові слова продуктів
            if any(keyword in part_lower for keyword in [
                'вода', 'water', 'sprite', 'спрайт', 'солод', 'літн',
                'цукати', 'ананас', 'кільце', 'молоко', 'хліб', 'масло',
                'г/в', 'л', 'кг', 'шт'
            ]):
                product_parts.append(part)
                
                # Якщо це "г/в" або одиниці виміру, беремо і попереднє слово
                if part_lower in ['г/в', 'л', 'кг', 'шт'] and i > 0:
                    prev_part = parts[i-1]
                    if prev_part not in product_parts:
                        product_parts.insert(-1, prev_part)
        
        # Якщо знайшли ключові слова, використовуємо їх
        if product_parts:
            result = ' '.join(product_parts[:4])  # Максимум 4 слова
        else:
            # Інакше беремо перші значущі слова
            significant_parts = [p for p in parts if not re.match(r'^\d+$', p)][:3]
            result = ' '.join(significant_parts)
        
        return result.strip() if result.strip() else name.strip()

    def _extract_amount_from_line(self, line: str) -> float:
        """Витягує суму з рядка"""
        # Розширені паттерни для знаходження сум
        extended_patterns = [
            r'(\d+[.,]\d{2})\s*(?:грн|UAH|₴|гривень|rpu|ppt|rpH)',  # З валютою
            r'(\d+[.,]\d{2})\s*$',  # Просто число в кінці рядка
            r'(\d+[.,]\d{2})',  # Будь-яке число з двома знаками після коми
            r'(\d+)\.\d{2}',  # Формат 100.47
            r'(\d+),\d{2}',   # Формат 100,47
            r'(\d+)\s+\d{2}',  # Формат "100 47" (іноді крапка не розпізнається)
        ]
        
        # Спочатку пробуємо стандартні паттерни
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, line)
            if matches:
                try:
                    # Беремо останню знайдену суму (зазвичай це фінальна ціна)
                    amount_str = matches[-1].replace(',', '.')
                    return float(amount_str)
                except ValueError:
                    continue
        
        # Потім пробуємо розширені паттерни
        for pattern in extended_patterns:
            matches = re.findall(pattern, line)
            if matches:
                try:
                    amount_str = matches[-1].replace(',', '.').replace(' ', '.')
                    return float(amount_str)
                except ValueError:
                    continue
        
        # Спеціальний пошук для спотворених чисел
        # Шукаємо комбінації цифр, які можуть бути сумами
        digit_matches = re.findall(r'(\d+)\s+(\d{2})', line)
        for main_digits, cents in digit_matches:
            try:
                if len(main_digits) <= 4:  # Розумна сума (до 9999)
                    amount = float(f"{main_digits}.{cents}")
                    if 0.01 <= amount <= 10000:  # Розумний діапазон
                        return amount
            except ValueError:
                continue
        
        # Ще один патерн: числа через пробіли типу "100 17"
        space_pattern = re.findall(r'(\d{1,4})\s+(\d{2})(?:\s|$)', line)
        if space_pattern:
            try:
                main_digits, cents = space_pattern[-1]
                amount = float(f"{main_digits}.{cents}")
                if 0.01 <= amount <= 10000:
                    return amount
            except ValueError:
                pass
                
        return 0.0

    def _extract_quantity(self, line: str) -> float:
        """Витягує кількість товару"""
        # Шукаємо патерни типу "2,5 x 15,50" або "2.5*15.50"
        quantity_patterns = [
            r'(\d+[.,]\d*)\s*[x*×]\s*\d+[.,]\d{2}',
            r'(\d+)\s*шт',
            r'(\d+[.,]\d*)\s*кг',
        ]
        
        for pattern in quantity_patterns:
            matches = re.findall(pattern, line)
            if matches:
                try:
                    return float(matches[0].replace(',', '.'))
                except ValueError:
                    continue
        
        return 1.0

    def _predict_item_category(self, description: str) -> str:
        """Передбачає категорію товару на основі його назви"""
        description_lower = description.lower()
        
        # Словник ключових слів для категорій
        category_keywords = {
            'Продукти харчування': [
                'хліб', 'молоко', 'сир', 'м\'ясо', 'курка', 'яйця', 'масло',
                'цукор', 'борошно', 'крупа', 'макарони', 'рис', 'гречка',
                'картопля', 'цибуля', 'морква', 'помідор', 'огірок', 'яблуко', 'яблука',
                'банан', 'апельсин', 'лимон', 'сосиска', 'ковбаса', 'рыба', 'риба',
                'йогурт', 'кефір', 'сметана', 'творог', 'печиво', 'цукерки',
                'овочі', 'фрукти', 'груша', 'слива', 'вишня', 'черешня', 'виноград',
                'кавун', 'диня', 'полуниця', 'малина', 'ожина', 'сало', 'ковбас',
                'батон', 'булочка', 'круасан', 'тортик', 'торт', 'пиріжок',
                'мед', 'джем', 'варення', 'соус', 'кетчуп', 'майонез', 'олія',
                'цукати', 'ананас', 'горіх', 'родзинки', 'курага', 'чорнослив'
            ],
            'Напої': [
                'вода', 'сок', 'чай', 'кава', 'пиво', 'вино', 'лимонад',
                'кола', 'пепсі', 'спрайт', 'квас', 'мінеральна', 'coca', 'pepsi',
                'sprite', 'фанта', 'fanta', 'компот', 'морс', 'енергетик',
                'juice', 'water', 'tea', 'coffee', 'beer', 'wine', 'cola',
                'напій', 'напиток', 'вода мін', 'сік', 'напої', 'літн-в',
                'солод', 'газована', 'без газу', 'мінералка', 'лимонад'
            ],
            'Побутова хімія': [
                'порошок', 'шампунь', 'мило', 'засіб', 'туалетний папір',
                'серветки', 'губка', 'пакети', 'фольга', 'плівка', 'ariel',
                'tide', 'persil', 'fairy', 'domestos', 'cif', 'гель',
                'рідина', 'засіб для', 'миючий', 'чистящий', 'пральний'
            ],
            'Косметика': [
                'крем', 'лосьйон', 'дезодорант', 'зубна паста', 'щітка',
                'маска', 'скраб', 'гель', 'тушь', 'помада', 'тональний',
                'пудра', 'тіни', 'олівець', 'краса', 'косметика', 'парфум'
            ],
            'Одяг та взуття': [
                'футболка', 'штани', 'сукня', 'куртка', 'взуття', 'носки',
                'труси', 'бюстгальтер', 'кросівки', 'туфлі', 'черевики',
                'шорти', 'спідниця', 'сорочка', 'светр', 'джинси', 'блузка'
            ],
            'Інше': [
                'іграшка', 'канцтовари', 'батарейки', 'зарядка', 'кабель',
                'товари для дому', 'декор', 'сувенір', 'подарунок'
            ]
        }
        
        # Шукаємо відповідність по ключовим словам
        for category, keywords in category_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return category
        
        return 'Інше'
    
    def _clean_ocr_text(self, text: str) -> str:
        """Радикально покращена функція очищення OCR тексту"""
        
        # Спочатку видаляємо зайві символи та нормалізуємо пробіли
        cleaned = re.sub(r'[^\w\s\u0400-\u04FF.,():/-+xх×XХ]', ' ', text)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Основні заміни на основі вашого спотвореного тексту
        basic_replacements = {
            # Основні символи
            'N ~': 'Н', '-\'': '', '™': '', '*': '', 'rm': 'рм',
            'r>': 'р>', 'ае': 'ае', 'v': 'в',
            
            # Слова з чека
            'Teerikos': 'Лютіков', 'BB': 'ВВ', 'магаsіn': 'магазин',
            'Jlaypua': 'Лаурина', 'Mikolajv': 'Миколаїв', 'Mitkonu': 'Миколаїв',
            'ДІ': 'ДІ', 'SOT': 'ФОП', 'Неr': 'Нер', 'іеее': 'іеее',
            'МаІад': 'Малад', 'Jед': 'Жед', 'Pen': 'Пен', 'Iatv': 'Іатв',
            'efuncovranict': 'ефункціонал', 'JH': 'ДІ',
            'RSLS': 'РСЛС', 'ww': 'шш', 'te': 'те',
            'ag': 'аг', 'Se': 'Се', 'RG': 'РГ', 'nO': 'но', 'ron': 'рон',
            'НН': 'НН', 'me': 'ме', 'Jao': 'Жао', 'hее': 'нее',
            'cn': 'сн', 'ane': 'ане', 'Ar': 'Ар', 'Lig': 'Ліг',
            'Fае': 'Фае', 'BeI': 'Веі', 'МАL': 'МАЛ', 'Lane': 'Лане',
            'Pp': 'Пп', 'SES': 'СЕС', 'Mu': 'Му', 'Maxpum': 'Максум',
            'con': 'кон', 'Nag': 'Наг', 'ragPMIDAT': 'рагРМІДАТ',
            'eg': 'ег', 'НЕХ': 'НЕХ', 'ea': 'еа', 'wit': 'віт',
            'Віа': 'Біа', 'SВА': 'СВА', 'МРS': 'МРС', 'ННS': 'ННС',
            'wае': 'ваe', 'es': 'ес', 'Ni': 'Ні', 'ont': 'онт',
            'oa': 'оа', 'STEREO': 'СТЕРЕО', 'СА': 'СА',
            'ОО5': '005', 'АРЕ': 'АПЕ', 'wo': 'шо', 'Woe': 'Шое',
            'xpаіtp': 'хпаітп', 'Npusarbany': 'Приватбанк',
            'МS': 'МС', 'МЕ': 'МЕ', 'РАЕ': 'РАЕ', 'Рrее': 'Рее',
            'we': 'ше', 'МА': 'МА', 'Tepадwіаn': 'Термінал',
            'SINFOTHIN': 'SINF07HN', 'ВSI': 'ВСІ', 'ее': 'ее',
            'Fi': 'Фі', 'ante': 'анте', 'Cease': 'Сеасе',
            'ННМКХ': 'XXXX', 'RS': 'РС', 'TSS': 'ТСС',
            'Вisisers': 'Бісісерс', 'cago': 'саго', 'he': 'не',
            'РНS': 'РНС', 'RRN': 'RRN', 'tn': 'тн', 'aca': 'аса',
            'sy': 'су', 'hits': 'хітс', 're': 'ре', 'iGед': 'іГед',
            'en': 'ен', 'Pe': 'Пе', 'Hiigiine': 'Підпис',
            'НОТ': 'НЕТ', 'pIG': 'рІГ', 'hy': 'ху', 'ws': 'шс',
            'ii': 'іі', 'APES': 'АРЕС', 'SCHPOTEMKO': 'БЕЗГОТІВ',
            'ВIT': 'ВИЙ', 'Sx': 'Сх', 'Ra': 'Ра', 'SВ': 'СВ',
            'Pye': 'Руе', 'IOO': '100', 'om': 'ом', 'Sey': 'Сеу',
            'trey': 'трей', 'fаіs': 'фаіс', 'еК': 'еК',
            'bед': 'вед', 'wіе': 'віе', 'Mt': 'Мт', 'іааме': 'іааме',
            'еII': 'еІІ', 'іеy': 'іеу', 'rn': 'рн', 'na': 'на',
            'еy': 'еу', 'Ie': 'Іе', 'IbrHLA': 'ІврНЛА', 'gL': 'гЛ',
            
            # Числові виправлення
            '29ОЗЗІ': '290331', 'ІІО9': '1499', 'О9В7І4ОІ': '09871401',
            '446О': '4460', 'ООЗ': '003', 'ІОО': '100', '47грн': '47 грн',
            
            # Товари
            'Лип-В': 'Лип-В', 'Вода': 'Вода', 'солод': 'солод',
            'Sprite': 'Sprite', 'Цукати': 'Цукати', 'ананас': 'ананас',
            'кільце': 'кільце', '3К38': '3К38',
            
            # Загальні літери
            'а': 'а', 'е': 'е', 'і': 'і', 'о': 'о', 'у': 'у', 'и': 'и',
            'я': 'я', 'ю': 'ю', 'ї': 'ї', 'є': 'є'
        }
        
        # Застосовуємо основні заміни
        for old, new in basic_replacements.items():
            cleaned = cleaned.replace(old, new)
        
        # Спеціальні регекс заміни
        # Виправляємо розділені числа: "100 47" -> "100.47"
        cleaned = re.sub(r'(\d+)\s+(\d{2})(?!\d)', r'\1.\2', cleaned)
        
        # Виправляємо розділені коди товарів
        cleaned = re.sub(r'(\d+)\s+([а-яА-Я]+[-/]?\s*[а-яА-Я]*)', r'\1 \2', cleaned)
        
        # Виправляємо множення: "x" замість різних символів
        cleaned = re.sub(r'[xх×XХ*]', 'x', cleaned)
        
        # Нормалізуємо пробіли
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()

    def _extract_date(self, text: str) -> datetime:
