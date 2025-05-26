import pytesseract
from PIL import Image
import pandas as pd
import re
import PyPDF2
import pdfplumber
from datetime import datetime, timedelta
from typing import List, Dict, Union, Optional
import logging
import asyncio
import aiofiles
import tempfile
import os

logger = logging.getLogger(__name__)

class StatementParser:
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.pdf']
        
        # Мово-специфічні паттерни для розпізнавання колонок
        self.column_patterns = {
            'date': ['date', 'дата', 'дата операції', 'transaction_date', 'операція'],
            'amount': ['amount', 'suma', 'сума', 'value', 'значення', 'операція'],
            'description': ['description', 'опис', 'purpose', 'призначення', 'comment', 'коментар'],
            'type': ['type', 'тип', 'operation_type', 'dr_cr', 'дебет_кредит']
        }
    
    def parse_bank_statement(self, file_path: str) -> List[Dict]:
        """
        Parse bank statement file and extract transactions (sync version)
        """
        try:
            if file_path.endswith('.csv'):
                return self._parse_csv(file_path)
            elif file_path.endswith('.xlsx'):
                return self._parse_excel(file_path)
            elif file_path.endswith('.pdf'):
                return self._parse_pdf(file_path)
            else:
                raise ValueError(f"Unsupported file format. Supported formats: {self.supported_formats}")
        except Exception as e:
            logger.error(f"Error parsing bank statement: {str(e)}")
            raise

    async def parse_pdf(self, file_path: str) -> List[Dict]:
        """
        Асинхронний парсинг PDF файлу
        """
        return await asyncio.to_thread(self._parse_pdf, file_path)
    
    async def parse_excel(self, file_path: str) -> List[Dict]:
        """
        Асинхронний парсинг Excel файлу
        """
        return await asyncio.to_thread(self._parse_excel, file_path)
    
    async def parse_csv(self, file_path: str) -> List[Dict]:
        """
        Асинхронний парсинг CSV файлу
        """
        return await asyncio.to_thread(self._parse_csv, file_path)
    
    def _parse_pdf(self, file_path: str) -> List[Dict]:
        """
        Парсинг PDF файлу з використанням pdfplumber
        """
        transactions = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    # Спробуємо витягти таблиці
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            df = pd.DataFrame(table[1:], columns=table[0])  # Перший рядок як заголовки
                            transactions.extend(self._process_dataframe(df))
                    else:
                        # Якщо таблиць немає, спробуємо розпізнати текст
                        text = page.extract_text()
                        if text:
                            transactions.extend(self._parse_text_transactions(text))
            
            return self._clean_and_validate_transactions(transactions)
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            # Fallback до PyPDF2
            return self._parse_pdf_fallback(file_path)

    def _parse_csv(self, file_path: str) -> List[Dict]:
        """
        Покращений парсинг CSV з автовизначенням кодування та роздільників
        """
        try:
            # Спробуємо різні кодування
            encodings = ['utf-8', 'cp1251', 'iso-8859-1', 'utf-16']
            df = None
            
            for encoding in encodings:
                try:
                    # Спробуємо різні роздільники
                    for sep in [',', ';', '\t']:
                        try:
                            df = pd.read_csv(file_path, encoding=encoding, sep=sep, low_memory=False)
                            if len(df.columns) > 1:  # Перевіряємо, що файл правильно розпарсений
                                break
                        except:
                            continue
                    if df is not None and len(df.columns) > 1:
                        break
                except:
                    continue
            
            if df is None or len(df.columns) <= 1:
                raise ValueError("Не вдалося розпізнати структуру CSV файлу")
            
            return self._process_dataframe(df)
        except Exception as e:
            logger.error(f"Error parsing CSV: {str(e)}")
            raise

    def _parse_excel(self, file_path: str) -> List[Dict]:
        """
        Покращений парсинг Excel з обробкою кількох аркушів
        """
        try:
            transactions = []
            
            # Читаємо всі аркуші
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Пропускаємо порожні аркуші
                    if df.empty or len(df.columns) == 0:
                        continue
                    
                    # Спробуємо знайти рядок з заголовками
                    header_row = self._find_header_row(df)
                    if header_row > 0:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
                    
                    sheet_transactions = self._process_dataframe(df)
                    transactions.extend(sheet_transactions)
                    
                except Exception as e:
                    logger.warning(f"Error processing sheet {sheet_name}: {str(e)}")
                    continue
            
            return self._clean_and_validate_transactions(transactions)
        except Exception as e:
            logger.error(f"Error parsing Excel: {str(e)}")
            raise

    def _process_dataframe(self, df: pd.DataFrame) -> List[Dict]:
        """
        Покращена обробка DataFrame з автовизначенням колонок
        """
        if df.empty:
            return []
        
        transactions = []
        
        # Визначаємо колонки
        column_mapping = self._map_columns(df.columns)
        
        for _, row in df.iterrows():
            try:
                # Пропускаємо порожні рядки
                if row.isna().all():
                    continue
                
                # Витягуємо дату
                date_value = self._extract_date_from_row(row, column_mapping.get('date'))
                if not date_value:
                    continue  # Пропускаємо рядки без дати
                
                # Витягуємо суму
                amount_value = self._extract_amount_from_row(row, column_mapping.get('amount'))
                if amount_value == 0:
                    continue  # Пропускаємо рядки без суми
                
                # Витягуємо опис
                description = self._extract_description_from_row(row, column_mapping.get('description'))
                
                # Визначаємо тип транзакції
                transaction_type = self._determine_transaction_type(amount_value, row, column_mapping.get('type'))
                
                # Визначаємо категорію
                category = self._suggest_category(description, transaction_type)
                
                transaction = {
                    'date': date_value,
                    'amount': abs(amount_value),
                    'description': description,
                    'type': transaction_type,
                    'category': category,
                    'raw_data': row.to_dict()  # Зберігаємо оригінальні дані
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                logger.warning(f"Error processing row: {str(e)}")
                continue
        
        return transactions
    
    def _map_columns(self, columns) -> Dict[str, str]:
        """
        Автовизначення колонок на основі назв
        """
        column_mapping = {}
        columns_lower = [str(col).lower().strip() for col in columns]
        
        for field, patterns in self.column_patterns.items():
            for i, col in enumerate(columns_lower):
                for pattern in patterns:
                    if pattern.lower() in col:
                        column_mapping[field] = columns[i]
                        break
                if field in column_mapping:
                    break
        
        return column_mapping
    
    def _find_header_row(self, df: pd.DataFrame) -> int:
        """
        Знаходить рядок з заголовками в DataFrame
        """
        for i in range(min(5, len(df))):  # Перевіряємо перші 5 рядків
            row = df.iloc[i]
            text_values = [str(val).lower() for val in row if pd.notna(val)]
            
            # Перевіряємо, чи містить рядок ключові слова заголовків
            header_keywords = ['date', 'дата', 'amount', 'сума', 'description', 'опис']
            if any(keyword in ' '.join(text_values) for keyword in header_keywords):
                return i
        
        return 0
    
    def _extract_date_from_row(self, row, date_column) -> Optional[datetime]:
        """
        Витягує дату з рядка
        """
        if not date_column or date_column not in row:
            # Спробуємо знайти дату в будь-якій колонці
            for col_name, value in row.items():
                if pd.notna(value):
                    parsed_date = self._parse_date_value(value)
                    if parsed_date:
                        return parsed_date
            return None
        
        return self._parse_date_value(row[date_column])
    
    def _parse_date_value(self, value) -> Optional[datetime]:
        """
        Розпізнає дату з різних форматів
        """
        if pd.isna(value):
            return None
        
        # Якщо вже datetime
        if isinstance(value, datetime):
            return value
        
        # Спробуємо різні формати дат
        date_formats = [
            '%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y',
            '%d.%m.%y', '%d/%m/%y', '%y-%m-%d', '%d-%m-%y',
            '%Y/%m/%d', '%m/%d/%Y', '%m-%d-%Y'
        ]
        
        date_str = str(value).strip()
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        # Спробуємо розпізнати через pandas
        try:
            return pd.to_datetime(value, dayfirst=True)
        except:
            return None
    
    def _extract_amount_from_row(self, row, amount_column) -> float:
        """
        Витягує суму з рядка
        """
        if not amount_column or amount_column not in row:
            # Спробуємо знайти числове значення в будь-якій колонці
            for col_name, value in row.items():
                if pd.notna(value):
                    parsed_amount = self._parse_amount_value(value)
                    if parsed_amount != 0:
                        return parsed_amount
            return 0
        
        return self._parse_amount_value(row[amount_column])
    
    def _parse_amount_value(self, value) -> float:
        """
        Розпізнає суму з різних форматів
        """
        if pd.isna(value):
            return 0
        
        # Якщо вже число
        if isinstance(value, (int, float)):
            return float(value)
        
        # Очищуємо рядок від зайвих символів
        amount_str = str(value).strip()
        amount_str = re.sub(r'[^\d.,\-+]', '', amount_str)
        
        if not amount_str:
            return 0
        
        # Обробляємо різні формати чисел
        try:
            # Заміняємо кому на крапку
            amount_str = amount_str.replace(',', '.')
            return float(amount_str)
        except:
            return 0
    
    def _extract_description_from_row(self, row, description_column) -> str:
        """
        Витягує опис з рядка
        """
        if description_column and description_column in row:
            desc = str(row[description_column]) if pd.notna(row[description_column]) else ""
        else:
            # Спробуємо знайти текстовий опис
            desc_parts = []
            for col_name, value in row.items():
                if pd.notna(value) and isinstance(value, str) and len(value.strip()) > 3:
                    # Пропускаємо колонки з датами та сумами
                    if not re.match(r'^\d+[.,]\d{2}$', str(value)) and not re.match(r'^\d{2}[./]\d{2}[./]\d{4}$', str(value)):
                        desc_parts.append(str(value).strip())
            desc = " | ".join(desc_parts[:2])  # Беремо перші 2 текстових поля
        
        return desc[:200] if desc and desc != "nan" else "Транзакція"
    
    def _determine_transaction_type(self, amount: float, row, type_column) -> str:
        """
        Визначає тип транзакції
        """
        # Якщо є спеціальна колонка типу
        if type_column and type_column in row:
            type_value = str(row[type_column]).lower()
            if any(word in type_value for word in ['дебет', 'debit', '-', 'витрата', 'expense']):
                return 'expense'
            elif any(word in type_value for word in ['кредит', 'credit', '+', 'дохід', 'income']):
                return 'income'
        
        # Визначаємо за знаком суми
        return 'expense' if amount < 0 else 'income'
    
    def _suggest_category(self, description: str, transaction_type: str) -> str:
        """
        Пропонує категорію на основі опису
        """
        if not description:
            return 'Інше'
        
        desc_lower = description.lower()
        
        # Категорії витрат
        if transaction_type == 'expense':
            if any(word in desc_lower for word in ['магазин', 'супермаркет', 'продукти', 'їжа', 'food', 'market']):
                return 'Продукти'
            elif any(word in desc_lower for word in ['заправка', 'бензин', 'газ', 'fuel', 'gas']):
                return 'Транспорт'
            elif any(word in desc_lower for word in ['ресторан', 'кафе', 'restaurant', 'cafe']):
                return 'Ресторани'
            elif any(word in desc_lower for word in ['аптека', 'медицина', 'лікар', 'pharmacy', 'medical']):
                return 'Здоровʼя'
            elif any(word in desc_lower for word in ['комунальні', 'електроенергія', 'газ', 'вода', 'utilities']):
                return 'Комунальні послуги'
        
        # Категорії доходів
        elif transaction_type == 'income':
            if any(word in desc_lower for word in ['зарплата', 'salary', 'wage']):
                return 'Зарплата'
            elif any(word in desc_lower for word in ['бонус', 'премія', 'bonus']):
                return 'Бонуси'
        
        return 'Інше'
    
    def _parse_pdf_fallback(self, file_path: str) -> List[Dict]:
        """
        Fallback парсинг PDF з використанням PyPDF2
        """
        transactions = []
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                transactions = self._parse_text_transactions(text)
            
            return self._clean_and_validate_transactions(transactions)
        except Exception as e:
            logger.error(f"PDF fallback parsing failed: {str(e)}")
            return []
    
    def _parse_text_transactions(self, text: str) -> List[Dict]:
        """
        Парсинг транзакцій з неструктурованого тексту
        """
        transactions = []
        lines = text.split('\n')
        
        # Паттерни для пошуку транзакцій
        date_pattern = r'\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b'
        amount_pattern = r'\b\d+[.,]\d{2}\b'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Шукаємо рядки, що містять і дату, і суму
            dates = re.findall(date_pattern, line)
            amounts = re.findall(amount_pattern, line)
            
            if dates and amounts:
                try:
                    # Беремо першу дату та останню суму
                    date_str = dates[0]
                    amount_str = amounts[-1].replace(',', '.')
                    
                    # Парсимо дату
                    date_obj = self._parse_date_value(date_str)
                    if not date_obj:
                        continue
                    
                    # Парсимо суму
                    amount = float(amount_str)
                    
                    # Видаляємо дату та суму з опису
                    description = line
                    for d in dates:
                        description = description.replace(d, '')
                    for a in amounts:
                        description = description.replace(a, '')
                    description = re.sub(r'\s+', ' ', description).strip()
                    
                    if not description:
                        description = "Транзакція"
                    
                    # Визначаємо тип за контекстом
                    transaction_type = 'expense'
                    if any(word in description.lower() for word in ['зарахування', 'надходження', 'дохід', 'поповнення']):
                        transaction_type = 'income'
                    
                    transaction = {
                        'date': date_obj,
                        'amount': abs(amount),
                        'description': description[:200],
                        'type': transaction_type,
                        'category': self._suggest_category(description, transaction_type)
                    }
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    logger.warning(f"Error parsing line: {line}, error: {str(e)}")
                    continue
        
        return transactions
    
    def _clean_and_validate_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """
        Очищає та валідує транзакції
        """
        cleaned_transactions = []
        
        for transaction in transactions:
            try:
                # Перевіряємо обов'язкові поля
                if not transaction.get('date') or not transaction.get('amount'):
                    continue
                
                # Перевіряємо, що дата не надто стара (більше 5 років)
                if isinstance(transaction['date'], datetime):
                    years_ago = datetime.now() - timedelta(days=5*365)
                    if transaction['date'] < years_ago:
                        continue
                
                # Перевіряємо, що сума розумна (не більше 1 мільйона)
                if transaction['amount'] > 1000000:
                    continue
                
                # Заповнюємо відсутні поля
                if not transaction.get('description'):
                    transaction['description'] = 'Транзакція'
                
                if not transaction.get('type'):
                    transaction['type'] = 'expense'
                
                if not transaction.get('category'):
                    transaction['category'] = self._suggest_category(
                        transaction['description'], 
                        transaction['type']
                    )
                
                cleaned_transactions.append(transaction)
                
            except Exception as e:
                logger.warning(f"Error validating transaction: {str(e)}")
                continue
        
        # Сортуємо за датою
        cleaned_transactions.sort(key=lambda x: x['date'], reverse=True)
        
        return cleaned_transactions

class ReceiptProcessor:
    def __init__(self):
        self.currency_pattern = r'\d+[.,]\d{2}'
        self.date_pattern = r'\d{2}[./]\d{2}[./]\d{4}'

    def process_receipt_image(self, image_path: str) -> Dict:
        """
        Process receipt image and extract relevant information
        """
        try:
            # Read image
            image = Image.open(image_path)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image)
            
            # Extract information
            total_amount = self._extract_amount(text)
            date = self._extract_date(text)
            items = self._extract_items(text)
            
            return {
                'total_amount': total_amount,
                'date': date,
                'items': items,
                'raw_text': text
            }
        except Exception as e:
            logger.error(f"Error processing receipt image: {str(e)}")
            raise

    def _extract_amount(self, text: str) -> float:
        amounts = re.findall(self.currency_pattern, text)
        if amounts:
            return float(amounts[-1].replace(',', '.'))
        return 0.0

    def _extract_date(self, text: str) -> datetime:
        dates = re.findall(self.date_pattern, text)
        if dates:
            return datetime.strptime(dates[0], '%d/%m/%Y')
        return datetime.now()

    def _extract_items(self, text: str) -> List[Dict]:
        items = []
        lines = text.split('\n')
        for line in lines:
            if re.search(self.currency_pattern, line):
                amount = float(re.findall(self.currency_pattern, line)[0].replace(',', '.'))
                description = line.split(str(amount))[0].strip()
                items.append({
                    'description': description,
                    'amount': amount
                })
        return items

# Create instances for import
statement_parser = StatementParser()
receipt_processor = ReceiptProcessor()