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
    
    def _find_header_row(self, df: pd.DataFrame) -> int:
        """
        Знаходить рядок з заголовками у DataFrame
        
        Повертає індекс рядка з заголовками або 0, якщо не знайдено
        """
        # Перевіряємо перші 10 рядків на наявність типових заголовків
        max_rows_to_check = min(10, len(df))
        
        # Ключові слова, які часто зустрічаються в заголовках
        header_keywords = [
            'дата', 'date', 'сума', 'amount', 'опис', 'description', 'призначення', 
            'transaction', 'тип', 'type', 'категорія', 'category'
        ]
        
        for i in range(max_rows_to_check):
            row = df.iloc[i].astype(str)
            row_text = ' '.join(row).lower()
            
            # Рахуємо, скільки ключових слів міститься в рядку
            matches = sum(keyword in row_text for keyword in header_keywords)
            
            # Якщо знайдено достатньо ключових слів, вважаємо це рядком заголовків
            if matches >= 2:
                return i
        
        # Якщо не знайдено, повертаємо 0 (перший рядок)
        return 0
    
    def parse_bank_statement(self, file_path: str, bank_type: str = None) -> List[Dict]:
        """
        Parse bank statement file and extract transactions (sync version)
        """
        try:
            # Визначаємо тип файлу
            if file_path.endswith('.csv'):
                if bank_type == 'monobank':
                    return self._parse_monobank_csv(file_path)
                return self._parse_csv(file_path)
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                if bank_type == 'privatbank':
                    return self._parse_privatbank_statement(file_path)
                elif bank_type == 'monobank':
                    return self._parse_monobank_xls(file_path)
                return self._parse_excel(file_path)
            elif file_path.endswith('.pdf'):
                if bank_type == 'privatbank':
                    return self._parse_privatbank_pdf(file_path)
                elif bank_type == 'monobank':
                    return self._parse_monobank_pdf(file_path)
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
        Покращений парсинг Excel з обробкою кількох аркушів і спеціальними обробниками для банків
        """
        try:
            transactions = []
            
            # Спочатку перевіряємо, чи це виписка з Приватбанку
            privatbank_transactions = self._parse_privatbank_statement(file_path)
            if privatbank_transactions:
                return privatbank_transactions
            
            # Якщо це не Приватбанк або обробка не вдалась, переходимо до загального парсера
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
            
    def _parse_privatbank_statement(self, file_path: str) -> List[Dict]:
        """
        Спеціальний парсер для виписок Приватбанку у форматі xlsx
        """
        try:
            logger.info(f"Parsing PrivatBank Excel statement from: {file_path}")
            transactions = []
            
            # Спочатку спробуємо прочитати файл як є, щоб визначити його структуру
            try:
                # Пробуємо зчитати всі аркуші
                excel_file = pd.ExcelFile(file_path)
                
                for sheet_name in excel_file.sheet_names:
                    logger.info(f"Processing sheet: {sheet_name}")
                    
                    # Прочитаємо файл без заголовків для пошуку структури
                    df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                    
                    # Шукаємо рядок, який містить "Дата операції" або інші ознаки заголовка
                    header_row = -1
                    for i in range(min(30, len(df_raw))): # Перевіряємо перші 30 рядків
                        row_text = ' '.join([str(val).lower() if not pd.isna(val) else '' for val in df_raw.iloc[i].values])
                        if 'дата операції' in row_text or ('дата' in row_text and ('опис' in row_text or 'сума' in row_text)):
                            header_row = i
                            logger.info(f"Found header row at index {header_row} with text: {row_text}")
                            break
                    
                    # Якщо знайшли заголовок, використовуємо його як початок даних
                    if header_row >= 0:
                        # Зчитуємо дані правильно з заголовком
                        try:
                            df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
                            logger.info(f"Read sheet with headers: {df.columns.tolist()}")
                            
                            # Колонки для транзакцій
                            date_col = None
                            amount_col = None
                            description_col = None
                            
                            # Знаходимо відповідні колонки по патернах
                            for col in df.columns:
                                col_lower = str(col).lower()
                                if 'дата' in col_lower or 'date' in col_lower:
                                    date_col = col
                                elif 'сума' in col_lower or 'amount' in col_lower:
                                    amount_col = col
                                elif 'опис' in col_lower or 'дescript' in col_lower or 'призначення' in col_lower:
                                    description_col = col
                            
                            # Якщо не знайшли основні колонки, беремо за позицією
                            if not date_col and len(df.columns) > 0:
                                date_col = df.columns[0]
                            if not amount_col and len(df.columns) > 5:
                                amount_col = df.columns[5]
                            if not description_col and len(df.columns) > 2:
                                description_col = df.columns[2]
                            
                            logger.info(f"Using columns: date={date_col}, amount={amount_col}, description={description_col}")
                                
                            # Проходимо по рядках і шукаємо транзакції
                            for idx, row in df.iterrows():
                                try:
                                    # Пропускаємо порожні рядки
                                    if row.isna().all():
                                        continue
                                        
                                    # Перевіряємо, чи містить дату
                                    if not date_col or pd.isna(row[date_col]):
                                        continue
                                    
                                    date_str = str(row[date_col])
                                    
                                    # Пропускаємо рядки з текстом "виписка" або "період"
                                    if 'виписка' in date_str.lower() or 'період' in date_str.lower():
                                        continue
                                    
                                    # Парсимо дату
                                    date_value = self._parse_date(date_str)
                                    if not date_value:
                                        continue
                                        
                                    # Отримуємо суму
                                    amount = None
                                    if amount_col and not pd.isna(row[amount_col]):
                                        try:
                                            amount_str = str(row[amount_col]).strip().replace(' ', '').replace(',', '.')
                                            amount = float(re.sub(r'[^\d\.\-\+]', '', amount_str))
                                        except:
                                            continue
                                    else:
                                        continue
                                        
                                    # Отримуємо опис
                                    description = "Транзакція Приватбанку"
                                    if description_col and not pd.isna(row[description_col]):
                                        description = str(row[description_col])
                                    
                                    # Тип транзакції
                                    transaction_type = 'expense' if amount < 0 else 'income'
                                    
                                    # Автоматична категоризація буде виконана пізніше з категоріями користувача
                                    # Поки що залишаємо категорію порожньою
                                    category = None
                                    
                                    # Додаємо транзакцію зі збереженням правильного знаку суми
                                    transaction = {
                                        'date': date_value.strftime('%Y-%m-%d'),
                                        'amount': amount,  # Зберігаємо оригінальний знак
                                        'description': description,
                                        'type': transaction_type,
                                        'category': category,
                                        'source': 'PrivatBank'
                                    }
                                    
                                    transactions.append(transaction)
                                    logger.debug(f"Added transaction: {transaction}")
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing row {idx}: {e}")
                            
                            logger.info(f"Extracted {len(transactions)} transactions from sheet {sheet_name}")
                                
                        except Exception as e:
                            logger.warning(f"Error processing sheet {sheet_name} after header: {e}")
            
                # Якщо знайшли транзакції, повертаємо їх
                if transactions:
                    logger.info(f"Total PrivatBank transactions found: {len(transactions)}")
                    return self._clean_and_validate_transactions(transactions)
                    
            except Exception as e:
                logger.error(f"Error in initial PrivatBank Excel parsing: {str(e)}")
            
            # Якщо не вдалося знайти транзакції, спробуємо більш загальний підхід
            logger.info("Trying fallback approach for PrivatBank statement")
            df = pd.read_excel(file_path)
            
            # Визначаємо, чи це виписка Приватбанку
            if not self._is_privatbank_statement(df):
                return []  # Це не виписка Приватбанку
            
            logger.info("Using general approach for PrivatBank statement")
            
            # Використовуємо загальний метод обробки DataFrame
            return self._process_dataframe(df)
            
        except Exception as e:
            logger.error(f"Error parsing PrivatBank statement: {str(e)}")
            return []
            
            # Приватбанк має такі колонки:
            # Дата операції, Час, Опис операції, МCC, Картка/Рахунок, Сума в валюті картки, Валюта картки, 
            # Сума в валюті операції, Валюта операції, Залишок на кінець операції, Бонус+
            
            # Отримуємо назви колонок для парсингу
            date_col = self._find_column_by_patterns(df.columns, ['дата', 'date', 'дата операції'])
            description_col = self._find_column_by_patterns(df.columns, ['опис', 'description', 'опис операції'])
            amount_col = self._find_column_by_patterns(df.columns, ['сума', 'amount', 'сума в валюті картки'])
            currency_col = self._find_column_by_patterns(df.columns, ['валюта', 'currency', 'валюта картки'])
            
            # Перебираємо рядки та витягуємо транзакції
            for _, row in df.iterrows():
                try:
                    # Пропускаємо порожні рядки або рядки із заголовками/підсумками
                    if row.isna().all() or self._is_header_or_summary_row(row):
                        continue
                    
                    # Отримуємо дату транзакції
                    date_value = None
                    if date_col is not None:
                        date_str = str(row[date_col])
                        date_value = self._parse_date(date_str)
                    
                    if not date_value:
                        continue  # Пропускаємо рядки без дати
                    
                    # Отримуємо опис транзакції
                    description = ""
                    if description_col is not None:
                        description = str(row[description_col]).strip()
                    
                    # Отримуємо суму транзакції
                    amount = 0
                    if amount_col is not None:
                        try:
                            # Можливо сума представлена у різних форматах
                            amount_str = str(row[amount_col]).strip().replace(" ", "").replace(",", ".")
                            amount = float(amount_str) if amount_str else 0
                        except (ValueError, TypeError):
                            continue  # Пропускаємо, якщо не можемо визначити суму
                    
                    if amount == 0:
                        continue  # Пропускаємо транзакції з нульовою сумою
                    
                    # Визначаємо тип транзакції (дохід чи витрата)
                    # У Приватбанку витрати вказуються зі знаком "-"
                    transaction_type = 'expense' if amount < 0 else 'income'
                    
                    # Автоматична категоризація буде виконана пізніше з категоріями користувача
                    category = None
                    
                    transaction = {
                        'date': date_value,
                        'amount': amount,  # Зберігаємо оригінальний знак
                        'description': description,
                        'type': transaction_type,
                        'category': category,
                        'source': 'PrivatBank',
                        'raw_data': row.to_dict()  # Зберігаємо оригінальні дані
                    }
                    
                    # Додаємо валюту, якщо є
                    if currency_col is not None:
                        currency = str(row[currency_col]).strip().upper()
                        if currency:
                            transaction['currency'] = currency
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    logger.warning(f"Error processing PrivatBank row: {str(e)}")
                    continue
            
            return self._clean_and_validate_transactions(transactions)
            
        except Exception as e:
            logger.error(f"Error parsing PrivatBank statement: {str(e)}")
            return []  # Повертаємо порожній список у випадку помилки
    


    def _is_privatbank_statement(self, df: pd.DataFrame) -> bool:
        """
        Визначає, чи є файл випискою з Приватбанку
        """
        # Конвертуємо DataFrame в текст для пошуку ключових фраз
        all_text = ' '.join([str(col) for col in df.columns])
        for row in df.iloc[:10].iterrows():  # Перевіряємо перші 10 рядків
            all_text += ' '.join([str(val) for val in row[1].values])
        
        all_text = all_text.lower()
        
        # Ключові слова та фрази, які зазвичай зустрічаються у виписках Приватбанку
        privatbank_keywords = [
            'приватбанк', 
            'приват24', 
            'privat', 
            'privatbank', 
            'privat24', 
            'бонус+',
            'бонус плюс'
        ]
        
        # Ключові колонки, які зазвичай є у виписках Приватбанку
        privatbank_columns = [
            'дата операції',
            'опис операції',
            'картка/рахунок',
            'сума в валюті картки',
            'валюта картки',
            'залишок',
            'mcc'
        ]
        
        # Перевіряємо ключові слова
        for keyword in privatbank_keywords:
            if keyword in all_text:
                return True
        
        # Перевіряємо наявність типових колонок
        column_matches = 0
        for col in privatbank_columns:
            if any(col in str(c).lower() for c in df.columns):
                column_matches += 1
        
        # Якщо знайдено більше 3 типових колонок, вважаємо що це виписка Приватбанку
        if column_matches >= 3:
            return True
        
        return False
    
    def _find_privatbank_header_row(self, df: pd.DataFrame) -> int:
        """
        Знаходить рядок з заголовками у виписці Приватбанку
        """
        # Ключові слова, які часто зустрічаються в заголовках Приватбанку
        header_keywords = [
            'дата операції', 'час', 'опис операції', 'mcc', 'картка', 'рахунок', 
            'сума в валюті картки', 'валюта картки', 'сума в валюті операції', 
            'валюта операції', 'залишок на кінець операції'
        ]
        
        # Перевіряємо перші 15 рядків
        for i in range(min(15, len(df))):
            row_text = ' '.join([str(x).lower() if x is not None else '' for x in df.iloc[i].values])
            
            # Рахуємо кількість ключових слів у рядку
            keyword_count = sum(1 for kw in header_keywords if kw in row_text)
            
            # Якщо знайдено достатньо ключових слів, ймовірно це заголовок
            if keyword_count >= 3:
                return i
        
        # Якщо нічого не знайдено, повертаємо -1
        return -1
    
    def _is_header_or_summary_row(self, row: pd.Series) -> bool:
        """
        Визначає, чи є рядок заголовком або підсумковим рядком
        """
        # Конвертуємо всі значення в рядку до рядкового типу і з'єднуємо для аналізу
        row_text = ' '.join([str(x).lower() if not pd.isna(x) else '' for x in row.values])
        
        # Ключові слова, які зазвичай зустрічаються в заголовках або підсумкових рядках
        header_keywords = ['всього', 'підсумок', 'total', 'sum', 'дата', 'сума', 'опис', 
                          'баланс', 'balance', 'залишок', 'amount', 'дебет', 'кредит']
        
        # Рядок є заголовком, якщо містить кілька ключових слів і не містить багато цифр
        keyword_count = sum(1 for kw in header_keywords if kw in row_text)
        digit_count = sum(1 for c in row_text if c.isdigit())
        
        # Якщо рядок містить багато ключових слів і мало цифр, ймовірно це заголовок
        if keyword_count >= 2 and digit_count < 10:
            return True
        
        # Перевірка на підсумковий рядок (містить 'всього', 'підсумок', 'total' тощо)
        summary_keywords = ['всього', 'total', 'підсумок', 'sum', 'итого']
        if any(kw in row_text for kw in summary_keywords):
            return True
        
        return False
    
    def _contains_numeric(self, text: str) -> bool:
        """
        Перевіряє, чи містить рядок числові значення
        """
        return bool(re.search(r'\d', text))
    
    def _find_column_by_patterns(self, columns, patterns: List[str]) -> Optional[str]:
        """
        Знаходить колонку за шаблонами
        """
        columns_lower = [str(col).lower().strip() for col in columns]
        
        for col in columns:
            col_lower = str(col).lower().strip()
            for pattern in patterns:
                if pattern in col_lower:
                    return col
        
        return None
    
    def _parse_text_transactions(self, text: str) -> List[Dict]:
        """
        Парсинг транзакцій з неструктурованого тексту (покращений для Monobank)
        """
        transactions = []
        lines = text.split('\n')
        
        # Паттерни для пошуку транзакцій (розширені для Monobank)
        date_pattern = r'\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b'
        time_pattern = r'\b\d{1,2}:\d{2}(:\d{2})?\b'
        amount_pattern = r'[-+]?\b\d+[.,]\d{2}\b'
        
        # Спеціальні паттерни для Monobank
        monobank_line_pattern = r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}:\d{2})?.*?([+-]?\d+[.,]\d{2})\s*(UAH|грн)?'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Спробуємо спочатку Monobank паттерн
            monobank_match = re.search(monobank_line_pattern, line)
            if monobank_match:
                try:
                    date_str = monobank_match.group(1)
                    time_str = monobank_match.group(2) or "00:00:00"
                    amount_str = monobank_match.group(3).replace(',', '.')
                    
                    # Парсимо дату
                    date_obj = self._parse_date(date_str)
                    if not date_obj:
                        continue
                    
                    # Парсимо суму
                    amount = float(amount_str)
                    
                    # Витягуємо опис (все між датою/часом і сумою)
                    description = line
                    description = re.sub(r'\d{2}\.\d{2}\.\d{4}', '', description)
                    description = re.sub(r'\d{2}:\d{2}:\d{2}', '', description)
                    description = re.sub(r'[+-]?\d+[.,]\d{2}\s*(UAH|грн)?', '', description)
                    description = re.sub(r'\s+', ' ', description).strip()
                    
                    if not description:
                        description = "Операція Monobank"
                    
                    # Визначаємо тип за контекстом
                    transaction_type = 'expense' if amount < 0 else 'income'
                    
                    # Призначаємо категорію через ML категоризатор
                    from services.ml_categorizer import transaction_categorizer
                    category = transaction_categorizer.suggest_category_for_bank_statement(description, transaction_type)
                    
                    transaction = {
                        'date': date_obj.strftime('%Y-%m-%d'),
                        'time': time_str,
                        'amount': abs(amount),
                        'description': description[:200],
                        'type': transaction_type,
                        'category': category,
                        'source': 'text_parsing'
                    }
                    
                    transactions.append(transaction)
                    continue
                    
                except Exception as e:
                    logger.warning(f"Error parsing Monobank line: {line}, error: {str(e)}")
                    continue
            
            # Якщо Monobank паттерн не спрацював, використовуємо загальний підхід
            # Шукаємо рядки, що містять і дату, і суму
            dates = re.findall(date_pattern, line)
            amounts = re.findall(amount_pattern, line)
            
            if dates and amounts:
                try:
                    # Беремо першу дату та останню суму
                    date_str = dates[0]
                    amount_str = amounts[-1].replace(',', '.')
                    
                    # Парсимо дату
                    date_obj = self._parse_date(date_str)
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
                    
                    # Призначаємо категорію через ML категоризатор
                    from services.ml_categorizer import transaction_categorizer
                    category = transaction_categorizer.suggest_category_for_bank_statement(description, transaction_type)
                    
                    transaction = {
                        'date': date_obj,
                        'amount': abs(amount),
                        'description': description[:200],
                        'type': transaction_type,
                        'category': category
                    }
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    logger.warning(f"Error parsing line: {line}, error: {str(e)}")
                    continue
        
        return transactions
    
    def _clean_and_validate_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """
        Очищує та валідує транзакції перед поверненням
        """
        if not transactions:
            return []
            
        cleaned_transactions = []
        
        for trans in transactions:
            # Перевірка наявності обов'язкових полів
            if 'date' not in trans or 'amount' not in trans:
                continue
                
            # Створюємо нову транзакцію з обов'язковими полями
            cleaned_trans = {
                'date': trans.get('date'),
                'amount': float(trans.get('amount', 0)),
                'description': trans.get('description', ''),
                'type': trans.get('type', 'expense')  # За замовчуванням це витрати
            }
            
            # Якщо тип не визначений і є сума, визначаємо тип за знаком
            if 'type' not in trans and 'original_amount' in trans:
                original_amount = float(trans['original_amount'])
                cleaned_trans['type'] = 'expense' if original_amount < 0 else 'income'
            
            # Копіювання додаткових полів, якщо вони є
            for key in ['category_hint', 'time', 'currency', 'mcc', 'balance', 'source']:
                if key in trans:
                    cleaned_trans[key] = trans[key]
            
            # Переконуємось, що сума - це дійсне число і більше нуля
            try:
                amount = float(cleaned_trans['amount'])
                if amount <= 0:
                    continue  # Пропускаємо нульові або від'ємні суми
                cleaned_trans['amount'] = amount
            except (ValueError, TypeError):
                continue  # Пропускаємо недійсні суми
            
            cleaned_transactions.append(cleaned_trans)
        
        # Сортуємо транзакції за датою від найновіших до найстаріших
        return sorted(cleaned_transactions, key=lambda x: x['date'], reverse=True)

    def _process_dataframe(self, df: pd.DataFrame) -> List[Dict]:
        """
        Обробляє DataFrame і витягує транзакції
        """
        transactions = []
        
        try:
            # Відфільтруємо порожні стовпці
            df = df.dropna(axis=1, how='all')
            if df.empty or len(df.columns) < 2:
                return []
            
            # Знайдемо колонки з датою, описом та сумою
            date_col = self._find_column_by_patterns(df.columns, ['дата', 'date', 'дата операції', 'transaction_date'])
            amount_cols = [
                self._find_column_by_patterns(df.columns, ['сума', 'amount', 'сума в валюті картки', 'value']),
                self._find_column_by_patterns(df.columns, ['дебет', 'debit', 'витрата', 'expense']),
                self._find_column_by_patterns(df.columns, ['кредит', 'credit', 'дохід', 'income']),
            ]
            # Використаємо першу знайдену колонку з сумою
            amount_col = next((col for col in amount_cols if col is not None), None)
            description_col = self._find_column_by_patterns(df.columns, ['опис', 'description', 'призначення', 'comment'])
            
            # Якщо не знайшли необхідні колонки, спробуємо використати колонки за індексами
            if not date_col or not amount_col:
                logger.warning("Could not find required columns by name, trying to use column indices")
                if len(df.columns) >= 3:
                    date_col = df.columns[0]
                    amount_col = df.columns[1]
                    description_col = df.columns[2] if len(df.columns) > 2 else None
            
            if not date_col or not amount_col:
                logger.warning("Could not determine transaction columns, returning empty list")
                return []
            
            logger.info(f"Using columns: date={date_col}, amount={amount_col}, description={description_col}")
            
            # Перебираємо рядки та витягуємо транзакції
            for _, row in df.iterrows():
                try:
                    # Пропускаємо порожні рядки або рядки із заголовками
                    if row.isna().all() or self._is_header_or_summary_row(row):
                        continue
                    
                    # Отримуємо дату транзакції
                    date_value = None
                    if date_col is not None and not pd.isna(row[date_col]):
                        date_str = str(row[date_col])
                        date_value = self._parse_date(date_str)
                    
                    if not date_value:
                        continue  # Пропускаємо рядки без дати
                    
                    # Отримуємо суму транзакції
                    amount = None
                    transaction_type = None
                    
                    if amount_col is not None and not pd.isna(row[amount_col]):
                        amount_str = str(row[amount_col])
                        amount_clean = re.sub(r'[^\d\-\+\.\,]', '', amount_str)
                        amount_clean = amount_clean.replace(',', '.')
                        
                        try:
                            amount = float(amount_clean)
                            # Визначаємо тип транзакції на основі знаку суми
                            transaction_type = 'expense' if amount < 0 else 'income'
                            amount = abs(amount)  # Зберігаємо суму як позитивне число
                        except ValueError:
                            continue  # Пропускаємо рядки з неправильною сумою
                    
                    # Якщо не змогли визначити суму, пропускаємо рядок
                    if amount is None:
                        continue
                    
                    # Отримуємо опис транзакції
                    description = ""
                    if description_col is not None and not pd.isna(row[description_col]):
                        description = str(row[description_col])
                    
                    # Призначаємо категорію через ML категоризатор
                    from services.ml_categorizer import transaction_categorizer
                    category = transaction_categorizer.suggest_category_for_bank_statement(description, transaction_type)
                    
                    # Створюємо словник транзакції
                    transaction = {
                        'date': date_value.strftime('%Y-%m-%d'),
                        'amount': amount,
                        'description': description,
                        'type': transaction_type,
                        'category': category
                    }
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    logger.warning(f"Error processing DataFrame row: {str(e)}")
                    continue
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error processing DataFrame: {str(e)}")
            return []

    def _parse_date(self, date_str: str):
        """
        Парсить різні формати дати
        """
        if not date_str or pd.isna(date_str):
            return None
        
        date_str = str(date_str).strip()
        
        # Спробуємо різні формати дати
        date_formats = [
            '%d.%m.%Y',  # 01.01.2024
            '%Y-%m-%d',  # 2024-01-01
            '%d/%m/%Y',  # 01/01/2024
            '%m/%d/%Y',  # 01/01/2024 (US format)
            '%d-%m-%Y',  # 01-01-2024
            '%d.%m.%y',  # 01.01.24
            '%d %b %Y',  # 01 Jan 2024
            '%d %B %Y',  # 01 January 2024
            '%Y.%m.%d',  # 2024.01.01
        ]
        
        # Спочатку спробуємо стандартний парсинг
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Якщо не вдалося, спробуємо витягти дату з рядка за допомогою regex
        date_patterns = [
            r'(\d{1,2})[\.\/\-](\d{1,2})[\.\/\-](\d{2,4})',  # DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY
            r'(\d{4})[\.\/\-](\d{1,2})[\.\/\-](\d{1,2})',    # YYYY.MM.DD, YYYY/MM/DD, YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # YYYY-MM-DD
                        year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    else:  # DD-MM-YYYY
                        day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        
                    # Додаємо 2000 до року, якщо він двозначний
                    if year < 100:
                        year += 2000 if year < 50 else 1900
                    
                    return datetime(year, month, day)
                except (ValueError, TypeError):
                    continue
        
        # Якщо нічого не спрацювало, спробуємо використати pandas
        try:
            return pd.to_datetime(date_str).to_pydatetime()
        except:
            return None

    def _parse_monobank_datetime(self, datetime_str: str):
        """
        Спеціальний парсер для дати і часу Монобанку у форматі "DD.MM.YYYY HH:MM:SS"
        """
        if not datetime_str or pd.isna(datetime_str):
            return None
        
        datetime_str = str(datetime_str).strip()
        
        # Формати дати і часу, які використовує Монобанк
        datetime_formats = [
            '%d.%m.%Y %H:%M:%S',  # 19.06.2025 14:42:15
            '%Y-%m-%d %H:%M:%S',  # 2025-06-19 14:42:15
            '%d/%m/%Y %H:%M:%S',  # 19/06/2025 14:42:15
            '%d-%m-%Y %H:%M:%S',  # 19-06-2025 14:42:15
            '%d.%m.%y %H:%M:%S',  # 19.06.25 14:42:15
            '%d.%m.%Y',           # 19.06.2025 (лише дата)
            '%Y-%m-%d',           # 2025-06-19 (лише дата)
        ]
        
        # Спробуємо кожен формат
        for fmt in datetime_formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        
        # Якщо стандартні формати не спрацювали, спробуємо витягти дату і час регулярним виразом
        # Паттерн для дати і часу: DD.MM.YYYY HH:MM:SS
        pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{1,2}):(\d{1,2})'
        match = re.search(pattern, datetime_str)
        if match:
            try:
                day, month, year, hour, minute, second = map(int, match.groups())
                return datetime(year, month, day, hour, minute, second)
            except ValueError:
                pass
        
        # Спробуємо парсити лише дату, якщо часу немає
        return self._parse_date(datetime_str)
    
    def _parse_monobank_csv(self, file_path: str) -> List[Dict]:
        """
        Спеціальний парсер для виписок Монобанку у форматі CSV
        """
        try:
            # Спробуємо зчитати CSV файл з різними кодуваннями
            df = None
            encodings = ['utf-8', 'windows-1251', 'cp1251', 'latin1']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, sep=None, engine='python')
                    break
                except Exception as e:
                    logger.warning(f"Failed to read CSV with encoding {encoding}: {e}")
                    continue
            
            if df is None or df.empty:
                logger.error(f"Could not read the monobank CSV file with any encoding")
                return []
            
            logger.info(f"Successfully read monobank CSV file: {df.shape[0]} rows, {df.shape[1]} columns")
            logger.info(f"Columns detected: {df.columns.tolist()}")
            
            # Спеціальний підхід для нового формату Монобанку
            # Формат: "Дата i час операції", "Деталі операції", MCC, "Сума в валюті картки (UAH)", ...
            
            # Знайдемо потрібні колонки за специфічними назвами Монобанку
            date_col = None
            description_col = None
            amount_col = None
            
            # Шукаємо колонки за точними назвами з нового формату Монобанку
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if 'дата' in col_lower and 'час' not in col_lower:
                    date_col = col
                elif 'деталі' in col_lower and 'операції' in col_lower:
                    description_col = col
                elif 'сума' in col_lower and 'валюті картки' in col_lower:
                    amount_col = col
            
            # Якщо не знайшли специфічні колонки, використовуємо загальний підхід
            if not date_col:
                date_col = self._find_column_by_patterns(df.columns, ['дата', 'date', 'time', 'час'])
            if not description_col:
                description_col = self._find_column_by_patterns(df.columns, ['опис', 'description', 'операція', 'comment', 'деталі'])
            if not amount_col:
                amount_col = self._find_column_by_patterns(df.columns, ['сума', 'amount', 'операції'])
                
            logger.info(f"Found columns - Date: {date_col}, Description: {description_col}, Amount: {amount_col}")
            
            # Якщо необхідні колонки не знайдені, спробуємо за індексами
            if not date_col or not amount_col:
                logger.warning("Monobank CSV: Could not find required columns by name patterns")
                columns_count = len(df.columns)
                if columns_count >= 4:
                    date_col = df.columns[0]  # Перша колонка - дата
                    description_col = df.columns[1] if columns_count > 1 else None  # Друга - деталі
                    amount_col = df.columns[3] if columns_count > 3 else df.columns[columns_count - 2]  # Четверта - сума
                    
                    logger.info(f"Using column indexes: date={date_col}, description={description_col}, amount={amount_col}")
            
            transactions = []
            
            # Перебираємо рядки та витягуємо транзакції
            for _, row in df.iterrows():
                try:
                    # Пропускаємо порожні рядки
                    if row.isna().all():
                        continue
                    
                    # Отримуємо дату і час транзакції
                    date_value = None
                    if date_col is not None:
                        date_str = str(row[date_col])
                        date_value = self._parse_monobank_datetime(date_str)
                    
                    if not date_value:
                        logger.warning(f"Could not parse date: {row[date_col] if date_col else 'N/A'}")
                        continue  # Пропускаємо рядки без дати
                    
                    # Отримуємо суму транзакції
                    amount = None
                    if amount_col is not None:
                        amount_str = str(row[amount_col])
                        # Монобанк використовує різні формати сум, спробуємо розпізнати різні варіанти
                        amount_clean = re.sub(r'[^\d\-\+\.\,]', '', amount_str)
                        amount_clean = amount_clean.replace(',', '.')
                        try:
                            amount = float(amount_clean)
                        except ValueError:
                            logger.warning(f"Could not parse amount: {amount_str}")
                            continue  # Пропускаємо рядки з неправильною сумою
                    
                    # Визначаємо тип транзакції (дохід чи витрата)
                    transaction_type = 'expense' if amount < 0 else 'income'
                    amount = abs(amount)  # Перетворюємо на додатне число для зберігання
                    
                    # Отримуємо опис транзакції
                    description = ""
                    if description_col is not None and not pd.isna(row[description_col]):
                        description = str(row[description_col]) if not pd.isna(row[description_col]) else ""
                    
                    # Призначаємо категорію через ML категоризатор
                    from services.ml_categorizer import transaction_categorizer
                    category = transaction_categorizer.suggest_category_for_bank_statement(description, transaction_type)
                    
                    # Створюємо словник транзакції
                    transaction = {
                        'date': date_value.strftime('%Y-%m-%d'),
                        'time': date_value.strftime('%H:%M:%S'),
                        'amount': amount,
                        'description': description,
                        'type': transaction_type,
                        'category': category,
                        'source': 'monobank_csv'
                    }
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    logger.warning(f"Error processing monobank CSV row: {str(e)}")
                    continue
            
            logger.info(f"Extracted {len(transactions)} transactions from monobank CSV file")
            return self._clean_and_validate_transactions(transactions)
            
        except Exception as e:
            logger.error(f"Error parsing monobank CSV: {str(e)}", exc_info=True)
            raise

    def _parse_monobank_xls(self, file_path: str) -> List[Dict]:
        """
        Спеціальний парсер для виписок Монобанку у форматі XLS
        """
        try:
            logger.info(f"Parsing Monobank XLS statement from: {file_path}")
            transactions = []
            
            # Читаємо XLS файл
            try:
                # Пробуємо прочитати всі аркуші
                excel_file = pd.ExcelFile(file_path)
                logger.info(f"Found sheets: {excel_file.sheet_names}")
                
                for sheet_name in excel_file.sheet_names:
                    logger.info(f"Processing sheet: {sheet_name}")
                    
                    # Прочитаємо файл без заголовків для пошуку структури
                    df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                    
                    # Шукаємо рядок з заголовками
                    header_row = -1
                    for i in range(min(30, len(df_raw))):
                        row_text = ' '.join([str(val).lower() if not pd.isna(val) else '' for val in df_raw.iloc[i].values])
                        # Шукаємо характерні для Monobank заголовки
                        if any(keyword in row_text for keyword in ['дата', 'час', 'операції', 'сума', 'деталі', 'mcc']):
                            # Перевіряємо, чи є це рядок заголовків (має кілька ключових слів)
                            keywords_count = sum(1 for keyword in ['дата', 'час', 'операції', 'сума', 'деталі'] if keyword in row_text)
                            if keywords_count >= 3:  # Збільшили мінімум до 3
                                header_row = i
                                logger.info(f"Found header row at index {header_row}: {row_text}")
                                break
                    
                    # Додатковий пошук за точним патерном Monobank
                    if header_row == -1:
                        for i in range(min(30, len(df_raw))):
                            # Перевіряємо чи є в рядку точні назви колонок Monobank
                            first_col = str(df_raw.iloc[i, 0]) if not pd.isna(df_raw.iloc[i, 0]) else ""
                            if "дата i час операції" in first_col.lower():
                                header_row = i
                                logger.info(f"Found Monobank header row at index {header_row}")
                                break
                    
                    # Якщо знайшли заголовок, читаємо дані
                    if header_row >= 0:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
                        logger.info(f"Columns found: {df.columns.tolist()}")
                        
                        # Знаходимо потрібні колонки для формату Monobank
                        date_col = None
                        time_col = None
                        amount_col = None
                        description_col = None
                        mcc_col = None
                        
                        for col in df.columns:
                            col_lower = str(col).lower().strip()
                            if 'дата' in col_lower and 'час' in col_lower:
                                date_col = col  # "Дата i час операції"
                            elif 'деталі' in col_lower and 'операції' in col_lower:
                                description_col = col
                            elif 'сума' in col_lower and 'картки' in col_lower:
                                amount_col = col  # "Сума в валюті картки (UAH)"
                            elif col_lower == 'mcc':
                                mcc_col = col
                        
                        # Якщо не знайшли за назвами, використовуємо позиції відповідно до структури Monobank
                        if not date_col and len(df.columns) > 0:
                            # Перша колонка - "Дата i час операції"
                            date_col = df.columns[0]
                        if not description_col and len(df.columns) > 1:
                            # Друга колонка - "Деталі операції"
                            description_col = df.columns[1]
                        if not mcc_col and len(df.columns) > 2:
                            # Третя колонка - "MCC"
                            mcc_col = df.columns[2]
                        if not amount_col and len(df.columns) > 3:
                            # Четверта колонка - "Сума в валюті картки (UAH)"
                            amount_col = df.columns[3]
                            
                        logger.info(f"Using columns - Date: {date_col}, Time: {time_col}, Description: {description_col}, Amount: {amount_col}")
                        
                        # Обробляємо рядки
                        for idx, row in df.iterrows():
                            try:
                                # Пропускаємо порожні рядки
                                if row.isna().all():
                                    continue
                                
                                # Парсимо дату та час (в Monobank вони в одній колонці)
                                date_value = None
                                time_value = "00:00:00"
                                
                                if date_col and not pd.isna(row[date_col]):
                                    datetime_str = str(row[date_col])
                                    try:
                                        # Формат Monobank: "19.06.2025 14:42:15"
                                        if ' ' in datetime_str:
                                            date_part, time_part = datetime_str.split(' ', 1)
                                            # Парсимо дату
                                            date_value = self._parse_date(date_part)
                                            # Парсимо час
                                            time_value = time_part
                                        else:
                                            # Якщо тільки дата
                                            date_value = self._parse_date(datetime_str)
                                    except:
                                        # Якщо не вдалося розділити, пробуємо як дату
                                        date_value = self._parse_date(datetime_str)
                                
                                if not date_value:
                                    continue
                                
                                # Парсимо суму
                                amount = None
                                if amount_col and not pd.isna(row[amount_col]):
                                    try:
                                        amount_str = str(row[amount_col]).strip()
                                        # Очищуємо від валюти та інших символів
                                        amount_clean = re.sub(r'[^\d\-\+\.\,]', '', amount_str)
                                        amount_clean = amount_clean.replace(',', '.')
                                        amount = float(amount_clean)
                                    except:
                                        continue
                                else:
                                    continue
                                
                                # Тип транзакції
                                transaction_type = 'expense' if amount < 0 else 'income'
                                amount = abs(amount)
                                
                                # Опис
                                description = ""
                                if description_col and not pd.isna(row[description_col]):
                                    description = str(row[description_col]).strip()
                                
                                # Призначаємо категорію через ML категоризатор
                                from services.ml_categorizer import transaction_categorizer
                                category = transaction_categorizer.suggest_category_for_bank_statement(description, transaction_type)
                                
                                # Створюємо транзакцію
                                transaction = {
                                    'date': date_value.strftime('%Y-%m-%d'),
                                    'time': time_value,
                                    'amount': amount,
                                    'description': description,
                                    'type': transaction_type,
                                    'category': category,
                                    'source': 'monobank_xls'
                                }
                                
                                transactions.append(transaction)
                                
                            except Exception as e:
                                logger.warning(f"Error processing XLS row {idx}: {str(e)}")
                                continue
                    
                    else:
                        logger.warning(f"No header row found in sheet {sheet_name}")
                        
            except Exception as e:
                logger.error(f"Error reading XLS file: {str(e)}")
                raise
            
            logger.info(f"Extracted {len(transactions)} transactions from Monobank XLS file")
            return self._clean_and_validate_transactions(transactions)
            
        except Exception as e:
            logger.error(f"Error parsing monobank XLS: {str(e)}", exc_info=True)
            raise

    def _parse_monobank_pdf(self, file_path: str) -> List[Dict]:
        """
        Спеціальний парсер для виписок Монобанку у форматі PDF (універсал банк)
        """
        try:
            transactions = []
            
            # Використовуємо pdfplumber для читання PDF файлу
            with pdfplumber.open(file_path) as pdf:
                logger.info(f"Processing monobank PDF with {len(pdf.pages)} pages")
                
                # Обробляємо кожну сторінку
                for page_num, page in enumerate(pdf.pages):
                    logger.info(f"Processing page {page_num + 1}")
                    
                    # Витягуємо таблиці з поточної сторінки
                    tables = page.extract_tables()
                    
                    if not tables:
                        logger.warning(f"No tables found on page {page_num + 1}, trying text extraction")
                        # Якщо таблиць немає, спробуємо витягти текст
                        text = page.extract_text()
                        if text:
                            logger.info(f"Extracted text from page {page_num + 1}: {len(text)} characters")
                            text_transactions = self._parse_text_transactions(text)
                            transactions.extend(text_transactions)
                        continue
                    
                    for table_num, table in enumerate(tables):
                        logger.info(f"Processing table {table_num + 1} on page {page_num + 1}")
                        
                        if not table or len(table) < 2:
                            logger.warning(f"Table {table_num + 1} is empty or too small")
                            continue
                        
                        # Аналізуємо заголовки таблиці
                        headers = table[0] if table else []
                        logger.info(f"Table headers: {headers}")
                        
                        # Логуємо кожен заголовок окремо для кращої діагностики
                        for i, header in enumerate(headers):
                            logger.info(f"Header {i}: '{header}' -> '{str(header or '').lower().strip()}'")
                        
                        # Логуємо перший рядок даних для розуміння структури
                        if len(table) > 1:
                            first_row = table[1]
                            logger.info(f"First data row: {first_row}")
                            for i, cell in enumerate(first_row):
                                logger.info(f"Cell {i}: '{cell}'")
                        
                        # Шукаємо індекси потрібних колонок
                        date_col_idx = None
                        amount_col_idx = None
                        description_col_idx = None
                        
                        for i, header in enumerate(headers):
                            header_str = str(header or '').lower().replace('\n', ' ').strip()
                            
                            # Пошук колонки з датою
                            if ('дата' in header_str or 'date' in header_str) and ('час' in header_str or 'операції' in header_str or 'time' in header_str):
                                date_col_idx = i
                                logger.info(f"Found date column at index {i}: {header}")
                            # Пошук колонки з описом - розширений список ключових слів
                            elif any(keyword in header_str for keyword in [
                                'деталі', 'опис', 'details', 'операці', 'призначення', 'purpose', 
                                'comment', 'коментар', 'description', 'merchant', 'торговець',
                                'контрагент', 'назва', 'name', 'transaction', 'операція', 'operation',
                                'мфо', 'отримувач', 'платник', 'одержувач', 'receiver', 'sender',
                                'інформація', 'info', 'дод', 'additional', 'додатк', 'опер'
                            ]):
                                description_col_idx = i
                                logger.info(f"Found description column at index {i}: {header}")
                            # Пошук колонки з сумою транзакції (НЕ з балансом!)
                            elif 'сума' in header_str and 'картки' in header_str and 'uah' in header_str and 'залишок' not in header_str and 'після' not in header_str:
                                amount_col_idx = i
                                logger.info(f"Found amount column at index {i}: {header}")
                        
                        # Якщо не знайшли колонки за назвами, спробуємо за позиціями для Monobank
                        if date_col_idx is None and len(headers) > 0:
                            date_col_idx = 0  # Перша колонка завжди "Дата i час операції"
                            logger.info(f"Using first column as date: {headers[0] if headers else 'N/A'}")
                        
                        if description_col_idx is None and len(headers) > 1:
                            description_col_idx = 1  # Друга колонка завжди "Деталі операції"
                            logger.info(f"Using second column as description: {headers[1] if len(headers) > 1 else 'N/A'}")
                        
                        if amount_col_idx is None:
                            # Для Monobank PDF це завжди 4-та колонка (індекс 3) - "Сума в валюті картки (UAH)"
                            if len(headers) > 3:
                                amount_col_idx = 3
                                logger.info(f"Using column 3 as amount (Monobank standard): {headers[3] if len(headers) > 3 else 'N/A'}")
                            else:
                                logger.warning("Not enough columns for Monobank format")
                        
                        logger.info(f"Final column mapping: date={date_col_idx}, description={description_col_idx}, amount={amount_col_idx}")
                        
                        if date_col_idx is None:
                            logger.warning(f"Date column not found in table {table_num + 1}")
                            continue
                        
                        if amount_col_idx is None:
                            logger.warning(f"Amount column not found in table {table_num + 1}")
                            continue
                        
                        logger.info(f"Processing table with {len(table)-1} data rows")
                        
                        # Обробляємо рядки даних (пропускаємо заголовок)
                        for row_num, row in enumerate(table[1:], 1):
                            try:
                                # Перевіряємо, що рядок не порожній та має достатньо колонок
                                if not row or len(row) == 0:
                                    continue
                                
                                # Перевіряємо, що всі значення не порожні
                                if all(not str(cell).strip() for cell in row):
                                    continue
                                
                                # Витягуємо дані з рядка за індексами
                                date_str = str(row[date_col_idx] if date_col_idx is not None and date_col_idx < len(row) else '').strip()
                                amount_str = str(row[amount_col_idx] if amount_col_idx is not None and amount_col_idx < len(row) else '').strip()
                                
                                # Для Monobank PDF завжди використовуємо колонку 1 як опис (Деталі операції)
                                description_str = ''
                                if len(row) > 1:
                                    description_str = str(row[1] or '').strip()  # Колонка 1 = "Деталі операції"
                                
                                # Якщо опис порожній, використовуємо запасний варіант
                                if not description_str:
                                    description_str = 'Банківська операція'
                                
                                # Пропускаємо порожні рядки
                                if not date_str or not amount_str:
                                    logger.debug(f"Skipping row {row_num}: empty date ({date_str}) or amount ({amount_str})")
                                    continue
                                
                                # Логуємо отримані дані для діагностики
                                logger.debug(f"Row {row_num}: date='{date_str}', amount='{amount_str}', description='{description_str}'")
                                
                                # Парсимо дату та час
                                # Monobank може мати формат "19.06.2025\n14:42:15" або просто дату
                                date_time_parts = date_str.replace('\n', ' ').split()
                                if len(date_time_parts) >= 2:
                                    date_part = date_time_parts[0].strip()
                                    time_part = date_time_parts[1].strip()
                                else:
                                    # Якщо час відсутній, використовуємо лише дату
                                    date_part = date_str.strip()
                                    time_part = "00:00:00"
                                
                                # Парсимо дату
                                try:
                                    # Спробуємо різні формати дат
                                    date_parsed = None
                                    for date_format in ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                                        try:
                                            date_parsed = datetime.strptime(date_part, date_format)
                                            break
                                        except ValueError:
                                            continue
                                    
                                    if not date_parsed:
                                        # Використовуємо загальний метод парсингу дат
                                        date_parsed = self._parse_date(date_part)
                                        
                                    if not date_parsed:
                                        logger.warning(f"Cannot parse date: {date_part}")
                                        continue
                                        
                                except Exception as e:
                                    logger.warning(f"Error parsing date '{date_part}': {e}")
                                    continue
                                
                                # Парсимо час
                                try:
                                    if ':' in time_part and len(time_part.split(':')) >= 2:
                                        time_parsed = datetime.strptime(time_part, '%H:%M:%S' if time_part.count(':') == 2 else '%H:%M').time()
                                    else:
                                        time_parsed = datetime.strptime("00:00:00", '%H:%M:%S').time()
                                except ValueError:
                                    logger.warning(f"Cannot parse time: {time_part}, using 00:00:00")
                                    time_parsed = datetime.strptime("00:00:00", '%H:%M:%S').time()
                                
                                # Об'єднуємо дату та час
                                transaction_datetime = datetime.combine(date_parsed.date(), time_parsed)
                                
                                # Парсимо суму
                                amount_clean = re.sub(r'[^\d\-\+\.\,\s]', '', amount_str)
                                amount_clean = amount_clean.replace(' ', '').replace(',', '.')
                                
                                try:
                                    amount = float(amount_clean)
                                except ValueError:
                                    logger.warning(f"Cannot parse amount: {amount_str} -> {amount_clean}")
                                    continue
                                
                                # Визначаємо тип транзакції
                                transaction_type = 'expense' if amount < 0 else 'income'
                                amount = abs(amount)
                                
                                # Призначаємо категорію через ML категоризатор
                                from services.ml_categorizer import transaction_categorizer
                                category = transaction_categorizer.suggest_category_for_bank_statement(description_str, transaction_type)
                                
                                # Створюємо транзакцію
                                transaction = {
                                    'date': transaction_datetime.strftime('%Y-%m-%d'),
                                    'time': transaction_datetime.strftime('%H:%M:%S'),
                                    'amount': amount,
                                    'description': description_str,
                                    'type': transaction_type,
                                    'category': category,
                                    'source': 'monobank_pdf',
                                    'raw_date': date_str,
                                    'raw_amount': amount_str
                                }
                                
                                transactions.append(transaction)
                                logger.debug(f"Parsed transaction: {transaction}")
                                
                            except Exception as e:
                                logger.warning(f"Error processing row {row_num}: {str(e)}")
                                continue
            
            logger.info(f"Extracted {len(transactions)} transactions from monobank PDF file")
            return transactions
        
        except Exception as e:
            logger.error(f"Error parsing monobank PDF: {str(e)}", exc_info=True)
            raise

    def _parse_privatbank_pdf(self, file_path: str) -> List[Dict]:
        """
        Спеціальний парсер для виписок Приватбанку у форматі PDF
        """
        try:
            transactions = []
            
            # Використовуємо pdfplumber для читання PDF файлу
            with pdfplumber.open(file_path) as pdf:
                logger.info(f"Processing PrivatBank PDF with {len(pdf.pages)} pages")
                
                # Обробляємо кожну сторінку
                for page_num, page in enumerate(pdf.pages):
                    logger.info(f"Processing page {page_num + 1}")
                    
                    # Витягуємо таблиці з поточної сторінки
                    tables = page.extract_tables()
                    
                    if not tables:
                        # Якщо таблиць немає, спробуємо витягти текст
                        text = page.extract_text()
                        if text:
                            text_transactions = self._parse_text_transactions(text)
                            transactions.extend(text_transactions)
                        continue
                    
                    for table_num, table in enumerate(tables):
                        logger.info(f"Processing table {table_num + 1} on page {page_num + 1}")
                        
                        if not table or len(table) < 2:
                            logger.warning(f"Table {table_num + 1} is empty or too small")
                            continue
                        
                        # Конвертуємо таблицю в DataFrame
                        df = pd.DataFrame(table[1:], columns=table[0])
                        
                        # Шукаємо індекси потрібних колонок для ПриватБанку
                        date_col_idx = None
                        amount_col_idx = None
                        description_col_idx = None
                        
                        for i, header in enumerate(df.columns):
                            header_str = str(header or '').lower().replace('\n', ' ').strip()
                            
                            if 'дата' in header_str:
                                date_col_idx = i
                                logger.info(f"Found date column at index {i}: {header}")
                            elif 'опис' in header_str or 'операц' in header_str:
                                description_col_idx = i
                                logger.info(f"Found description column at index {i}: {header}")
                            elif 'сума' in header_str:
                                amount_col_idx = i
                                logger.info(f"Found amount column at index {i}: {header}")
                        
                        if date_col_idx is None or amount_col_idx is None:
                            logger.warning(f"Essential columns not found: date={date_col_idx}, amount={amount_col_idx}")
                            continue
                        
                        # Обробляємо рядки даних
                        for row_num, row in df.iterrows():
                            try:
                                if row.isna().all():
                                    continue
                                
                                # Витягуємо дані з рядка
                                date_str = str(row.iloc[date_col_idx] if date_col_idx < len(row) else '').strip()
                                amount_str = str(row.iloc[amount_col_idx] if amount_col_idx < len(row) else '').strip()
                                description_str = str(row.iloc[description_col_idx] if description_col_idx is not None and description_col_idx < len(row) else 'Транзакція ПриватБанку').strip()
                                
                                # Пропускаємо порожні рядки
                                if not date_str or not amount_str:
                                    continue
                                
                                # Парсимо дату
                                date_parsed = self._parse_date(date_str)
                                if not date_parsed:
                                    logger.warning(f"Cannot parse date: {date_str}")
                                    continue
                                
                                # Парсимо суму
                                amount_clean = re.sub(r'[^\d\-\+\.\,\s]', '', amount_str)
                                amount_clean = amount_clean.replace(' ', '').replace(',', '.')
                                
                                try:
                                    amount = float(amount_clean)
                                except ValueError:
                                    logger.warning(f"Cannot parse amount: {amount_str} -> {amount_clean}")
                                    continue
                                
                                # Визначаємо тип транзакції
                                transaction_type = 'expense' if amount < 0 else 'income'
                                amount = abs(amount)
                                
                                # Призначаємо категорію через ML категоризатор
                                from services.ml_categorizer import transaction_categorizer
                                category = transaction_categorizer.suggest_category_for_bank_statement(description_str, transaction_type)
                                
                                # Створюємо транзакцію
                                transaction = {
                                    'date': date_parsed.strftime('%Y-%m-%d'),
                                    'amount': amount,
                                    'description': description_str,
                                    'type': transaction_type,
                                    'category': category,
                                    'source': 'privatbank_pdf'
                                }
                                
                                transactions.append(transaction)
                                logger.debug(f"Parsed transaction: {transaction}")
                                
                            except Exception as e:
                                logger.warning(f"Error processing row {row_num}: {str(e)}")
                                continue
            
            logger.info(f"Extracted {len(transactions)} transactions from PrivatBank PDF file")
            return self._clean_and_validate_transactions(transactions)
        
        except Exception as e:
            logger.error(f"Error parsing PrivatBank PDF: {str(e)}", exc_info=True)
            raise

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
            from PIL import Image
            import pytesseract
            
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
        import re
        amounts = re.findall(self.currency_pattern, text)
        if amounts:
            return float(amounts[-1].replace(',', '.'))
        return 0.0

    def _extract_date(self, text: str) -> datetime:
        import re
        dates = re.findall(self.date_pattern, text)
        if dates:
            return datetime.strptime(dates[0], '%d/%m/%Y')
        return datetime.now()

    def _extract_items(self, text: str) -> List[Dict]:
        import re
        items = []
        lines = text.split('\n')
        for line in lines:
            if re.search(self.currency_pattern, line):
                amount_match = re.findall(self.currency_pattern, line)
                if amount_match:
                    amount = float(amount_match[0].replace(',', '.'))
                    description = line.split(str(amount))[0].strip()
                    items.append({
                        'description': description,
                        'amount': amount
                    })
        return items

# Create an instance for import
statement_parser = StatementParser()
receipt_processor = ReceiptProcessor()