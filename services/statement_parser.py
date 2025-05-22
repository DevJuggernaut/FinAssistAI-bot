import pytesseract
from PIL import Image
import pandas as pd
import re
from datetime import datetime
from typing import List, Dict, Union
import logging

logger = logging.getLogger(__name__)

class StatementParser:
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.pdf']
    
    def parse_bank_statement(self, file_path: str) -> List[Dict]:
        """
        Parse bank statement file and extract transactions
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

    def _parse_csv(self, file_path: str) -> List[Dict]:
        df = pd.read_csv(file_path)
        return self._process_dataframe(df)

    def _parse_excel(self, file_path: str) -> List[Dict]:
        df = pd.read_excel(file_path)
        return self._process_dataframe(df)

    def _process_dataframe(self, df: pd.DataFrame) -> List[Dict]:
        transactions = []
        for _, row in df.iterrows():
            transaction = {
                'date': row.get('date', row.get('Date', row.get('DATE'))),
                'amount': row.get('amount', row.get('Amount', row.get('AMOUNT'))),
                'description': row.get('description', row.get('Description', row.get('DESCRIPTION'))),
                'type': 'expense' if float(row.get('amount', 0)) < 0 else 'income'
            }
            transactions.append(transaction)
        return transactions

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