#!/usr/bin/env python3
"""
Скрипт для аналізу чеків магазину "Таврія В"
"""

import os
import sys
from PIL import Image
import pytesseract
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_receipt_image(image_path):
    """Аналізує зображення чека"""
    print(f"\n=== Аналіз чека: {os.path.basename(image_path)} ===")
    
    try:
        # Відкриваємо зображення
        image = Image.open(image_path)
        print(f"Розмір зображення: {image.size}")
        
        # Витягуємо текст з різними налаштуваннями
        
        # Стандартний OCR
        print("\n--- Стандартний OCR ---")
        text_standard = pytesseract.image_to_string(image, lang='ukr+eng')
        print(text_standard)
        
        # OCR з покращеними налаштуваннями для цифр
        print("\n--- OCR з налаштуваннями для цифр ---")
        config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789абвгдежзийклмнопрстуфхцчшщьюяАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЮЯabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.,:\-+*/=()№% '
        text_digits = pytesseract.image_to_string(image, lang='ukr+eng', config=config)
        print(text_digits)
        
        # Зберігаємо результат в файл
        output_file = f"/Users/abobina/telegram_bot/FinAssistAI-bot/analysis_results_{os.path.basename(image_path).replace('.jpeg', '.txt')}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"=== Аналіз чека: {os.path.basename(image_path)} ===\n\n")
            f.write("--- Стандартний OCR ---\n")
            f.write(text_standard)
            f.write("\n\n--- OCR з налаштуваннями для цифр ---\n")
            f.write(text_digits)
        
        print(f"\nРезультат збережено в: {output_file}")
        
    except Exception as e:
        logger.error(f"Помилка при аналізі {image_path}: {str(e)}")

def main():
    """Головна функція"""
    receipts_dir = "/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/receipts"
    
    # Знаходимо всі чеки
    receipt_files = [f for f in os.listdir(receipts_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    print(f"Знайдено {len(receipt_files)} чеків для аналізу")
    
    for receipt_file in sorted(receipt_files):
        receipt_path = os.path.join(receipts_dir, receipt_file)
        analyze_receipt_image(receipt_path)

if __name__ == "__main__":
    main()
