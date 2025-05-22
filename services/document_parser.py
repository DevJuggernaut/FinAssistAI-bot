import pandas as pd
import re
import io
import csv
import pytesseract
from PIL import Image
from datetime import datetime
import os
import logging

from database.db_operations import add_transaction, get_user_categories
from services.category_classifier import classify_transaction

# Настройка логування
logger = logging.getLogger(__name__)

class BankStatementParser:
    """Клас для парсингу та обробки банківських виписок різних форматів"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.categories = {cat.name.lower(): cat.id for cat in get_user_categories(user_id)}
    
    def parse_file(self, file_path, file_format=None):
        """Парсинг файлу виписки відповідно до його формату"""
        if not file_format:
            file_format = self._detect_file_format(file_path)
        
        if file_format == 'csv':
            return self._parse_csv(file_path)
        elif file_format == 'excel' or file_format == 'xlsx':
            return self._parse_excel(file_path)
        elif file_format == 'pdf':
            return self._parse_pdf(file_path)
        else:
            raise ValueError(f"Непідтримуваний формат файлу: {file_format}")
    
    def _detect_file_format(self, file_path):
        """Визначення формату файлу за розширенням"""
        extension = os.path.splitext(file_path)[1].lower()
        
        if extension == '.csv':
            return 'csv'
        elif extension in ['.xlsx', '.xls']:
            return 'excel'
        elif extension == '.pdf':
            return 'pdf'
        else:
            return 'unknown'
    
    def _parse_csv(self, file_path):
        """Парсинг CSV-файлу"""
        try:
            # Спробуємо визначити діалект CSV
            with open(file_path, 'r', encoding='utf-8') as f:
                sample = f.read(4096)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                has_header = sniffer.has_header(sample)
            
            # Читаємо файл з визначеним діалектом
            df = pd.read_csv(file_path, dialect=dialect, header=0 if has_header else None)
            
            # Визначаємо структуру даних на основі назв стовпців або позицій
            return self._detect_and_structure_data(df)
        
        except Exception as e:
            logger.error(f"Помилка при парсингу CSV: {e}")
            raise
    
    def _parse_excel(self, file_path):
        """Парсинг Excel-файлу"""
        try:
            df = pd.read_excel(file_path)
            return self._detect_and_structure_data(df)
        except Exception as e:
            logger.error(f"Помилка при парсингу Excel: {e}")
            raise
    
    def _parse_pdf(self, file_path):
        """Парсинг PDF-файлу (спрощена версія, використовує текстове розпізнавання)"""
        try:
            # Для роботи з PDF потрібні додаткові бібліотеки, такі як PyPDF2 або pdfplumber
            # Тут використовується спрощений підхід з конвертацією в текст
            # Для реального використання вам буде потрібно встановити pdfplumber
            
            # Спрощений код:
            import pdfplumber
            
            transactions = []
            
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    # Застосовуємо регулярні вирази для пошуку транзакцій
                    # Це дуже залежить від формату виписки конкретного банку
                    # Нижче приклад для загального випадку
                    pattern = r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\s+([A-Za-zА-Яа-яІіЇїЄєҐґ\s]+)\s+(-?\d+[.,]\d{2})'
                    matches = re.findall(pattern, text)
                    
                    for match in matches:
                        date_str, description, amount_str = match
                        
                        try:
                            # Перетворюємо дату з тексту
                            date_formats = ['%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']
                            parsed_date = None
                            
                            for fmt in date_formats:
                                try:
                                    parsed_date = datetime.strptime(date_str, fmt)
                                    break
                                except ValueError:
                                    continue
                            
                            if not parsed_date:
                                continue
                            
                            # Перетворюємо суму з тексту
                            amount = float(amount_str.replace(',', '.').replace(' ', ''))
                            
                            # Визначаємо тип транзакції
                            transaction_type = 'expense' if amount < 0 else 'income'
                            amount = abs(amount)
                            
                            transactions.append({
                                'date': parsed_date,
                                'description': description.strip(),
                                'amount': amount,
                                'type': transaction_type
                            })
                        except Exception as e:
                            logger.warning(f"Не вдалося обробити транзакцію: {e}")
            
            return transactions
        
        except Exception as e:
            logger.error(f"Помилка при парсингу PDF: {e}")
            raise
    
    def _detect_and_structure_data(self, df):
        """Визначення структури даних та перетворення в уніфікований формат"""
        transactions = []
        
        # Спробуємо визначити потрібні стовпці
        date_col = None
        desc_col = None
        amount_col = None
        
        # Пошук стовпців за ключовими словами
        for col in df.columns:
            col_lower = str(col).lower()
            if any(key in col_lower for key in ['date', 'дата', 'дату']):
                date_col = col
            elif any(key in col_lower for key in ['desc', 'опис', 'призначення', 'details']):
                desc_col = col
            elif any(key in col_lower for key in ['amount', 'sum', 'сума', 'транзакція']):
                amount_col = col
        
        if not all([date_col, desc_col, amount_col]):
            # Якщо не знайшли колонки за назвами, припускаємо стандартний порядок
            if len(df.columns) >= 3:
                date_col = df.columns[0]
                desc_col = df.columns[1]
                amount_col = df.columns[2]
            else:
                raise ValueError("Не вдалося визначити структуру даних у файлі")
        
        # Обробка кожного рядка
        for _, row in df.iterrows():
            try:
                # Обробка дати (може бути в різних форматах)
                date_val = row[date_col]
                
                if isinstance(date_val, datetime):
                    parsed_date = date_val
                elif isinstance(date_val, str):
                    # Спробуємо різні формати дати
                    date_formats = ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']
                    parsed_date = None
                    
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(date_val, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if not parsed_date:
                        continue  # Якщо не вдалося розпізнати дату, пропускаємо рядок
                else:
                    continue  # Незрозумілий формат дати
                
                # Обробка опису
                description = str(row[desc_col]).strip()
                
                # Обробка суми
                amount_str = str(row[amount_col]).replace(' ', '').replace(',', '.')
                # Видаляємо всі символи, крім цифр, крапки та мінуса
                amount_str = re.sub(r'[^\d.-]', '', amount_str)
                
                try:
                    amount = float(amount_str)
                except ValueError:
                    continue  # Якщо не вдалося перетворити на число, пропускаємо рядок
                
                # Визначаємо тип транзакції
                transaction_type = 'expense' if amount < 0 else 'income'
                amount = abs(amount)
                
                transactions.append({
                    'date': parsed_date,
                    'description': description,
                    'amount': amount,
                    'type': transaction_type
                })
                
            except Exception as e:
                logger.warning(f"Помилка при обробці рядка: {e}")
        
        return transactions

    def save_transactions_to_db(self, transactions):
        """Збереження розпізнаних транзакцій в базу даних"""
        added_count = 0
        
        for transaction in transactions:
            try:
                # Класифікуємо транзакцію для визначення категорії
                category_name = classify_transaction(transaction['description'], transaction['type'])
                
                # Знаходимо ID категорії або використовуємо "Інше"
                category_id = self.categories.get(category_name.lower())
                if not category_id:
                    # Якщо категорію не знайдено, використовуємо категорію "Інше" відповідного типу
                    other_name = "інше"
                    category_id = self.categories.get(other_name)
                
                # Додаємо транзакцію в БД
                add_transaction(
                    user_id=self.user_id,
                    amount=transaction['amount'],
                    description=transaction['description'],
                    category_id=category_id,
                    transaction_type=transaction['type'],
                    transaction_date=transaction['date'],
                    source="bank_statement"
                )
                added_count += 1
                
            except Exception as e:
                logger.error(f"Помилка при збереженні транзакції: {e}")
        
        return added_count


class ReceiptParser:
    """Клас для розпізнавання та обробки чеків з фотографій"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.categories = {cat.name.lower(): cat.id for cat in get_user_categories(user_id)}
    
    def parse_receipt_image(self, image_path):
        """Розпізнавання тексту з фотографії чека"""
        try:
            # Відкриваємо зображення
            image = Image.open(image_path)
            
            # Розпізнаємо текст
            text = pytesseract.image_to_string(image, lang='ukr+eng')
            
            # Обробляємо розпізнаний текст
            return self._process_receipt_text(text, image_path)
            
        except Exception as e:
            logger.error(f"Помилка при обробці зображення чека: {e}")
            raise
    
    def _process_receipt_text(self, text, image_path):
        """Обробка розпізнаного тексту з чека"""
        lines = text.split('\n')
        
        # Спробуємо знайти загальну суму
        total_amount = None
        date = None
        store_name = None
        items = []
        
        # Шукаємо загальну суму за ключовими словами
        amount_patterns = [
            r'(?:сума|всього|разом|итого|total|sum)[\s:]*?(\d+[.,]\d{2})',
            r'(?:сума|всього|разом|итого|total|sum)[\s:]*?(\d+)',
            r'^[\s]*?(\d+[.,]\d{2})[\s]*?$'  # Просто сума на окремому рядку
        ]
        
        # Шукаємо дату за типовими форматами
        date_patterns = [
            r'(\d{2}[./-]\d{2}[./-]\d{2,4})',
            r'(\d{4}[./-]\d{2}[./-]\d{2})'
        ]
        
        # Перші кілька рядків можуть містити назву магазину
        if len(lines) > 0:
            store_name = lines[0].strip()
            if len(store_name) < 3 and len(lines) > 1:
                store_name = lines[1].strip()
        
        for line in lines:
            line = line.strip()
            
            # Пропускаємо порожні рядки
            if not line:
                continue
            
            # Шукаємо загальну суму
            if not total_amount:
                for pattern in amount_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        try:
                            total_amount = float(match.group(1).replace(',', '.'))
                            break
                        except ValueError:
                            pass
            
            # Шукаємо дату
            if not date:
                for pattern in date_patterns:
                    match = re.search(pattern, line)
                    if match:
                        date_str = match.group(1)
                        try:
                            # Спробуємо різні формати дати
                            for fmt in ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%y']:
                                try:
                                    date = datetime.strptime(date_str, fmt)
                                    break
                                except ValueError:
                                    continue
                            if date:
                                break
                        except Exception:
                            pass
            
            # Шукаємо елементи чека (товари)
            item_pattern = r'([A-Za-zА-Яа-яІіЇїЄєҐґ\s]+)\s+(\d+[.,]\d{2})'
            match = re.search(item_pattern, line)
            if match:
                item_name = match.group(1).strip()
                try:
                    item_price = float(match.group(2).replace(',', '.'))
                    items.append({
                        'name': item_name,
                        'price': item_price
                    })
                except ValueError:
                    pass
        
        # Якщо дату не знайдено, використовуємо поточну
        if not date:
            date = datetime.now()
        
        # Якщо суму не знайдено, але є елементи, спробуємо підсумувати їх
        if not total_amount and items:
            total_amount = sum(item['price'] for item in items)
        
        # Якщо суму все одно не знайдено, не можемо створити транзакцію
        if not total_amount:
            raise ValueError("Не вдалося визначити суму на чеку")
        
        result = {
            'date': date,
            'store_name': store_name,
            'total_amount': total_amount,
            'items': items,
            'image_path': image_path
        }
        
        return result
    
    def save_receipt_to_db(self, receipt_data):
        """Збереження розпізнаного чека в базу даних"""
        try:
            # Визначаємо опис транзакції
            description = receipt_data['store_name'] if receipt_data['store_name'] else "Покупка"
            
            # Класифікуємо транзакцію для визначення категорії
            category_name = classify_transaction(description, 'expense')
            
            # Знаходимо ID категорії або використовуємо "Інше"
            category_id = self.categories.get(category_name.lower())
            if not category_id:
                # Якщо категорію не знайдено, використовуємо категорію "Інше"
                other_name = "інше"
                category_id = self.categories.get(other_name)
            
            # Додаємо транзакцію в БД
            transaction = add_transaction(
                user_id=self.user_id,
                amount=receipt_data['total_amount'],
                description=description,
                category_id=category_id,
                transaction_type='expense',
                transaction_date=receipt_data['date'],
                source="receipt",
                receipt_image=receipt_data['image_path']
            )
            
            return transaction
            
        except Exception as e:
            logger.error(f"Помилка при збереженні чека: {e}")
            raise
