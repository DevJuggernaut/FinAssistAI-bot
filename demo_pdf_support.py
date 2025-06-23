#!/usr/bin/env python3
"""
Демонстрація нової функціональності: завантаження PDF виписок з Monobank
"""

import sys
import os
sys.path.insert(0, '/Users/abobina/telegram_bot/FinAssistAI-bot')

from services.statement_parser import StatementParser
import pdfplumber
from datetime import datetime

def demo_pdf_parsing():
    """Демонстрація PDF парсингу для Monobank"""
    print("=" * 80)
    print("🎯 ДЕМОНСТРАЦІЯ: Завантаження PDF виписок з МоноБанку")
    print("=" * 80)
    
    pdf_file = "/Users/abobina/telegram_bot/FinAssistAI-bot/uploads/statements/report_20-06-2025_16-12-03.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ PDF файл не знайдено: {pdf_file}")
        return
    
    print(f"📄 Файл: {os.path.basename(pdf_file)}")
    print(f"📊 Розмір: {os.path.getsize(pdf_file) / 1024:.1f} KB")
    
    # Аналіз структури PDF
    print("\n🔍 АНАЛІЗ СТРУКТУРИ PDF:")
    try:
        with pdfplumber.open(pdf_file) as pdf:
            print(f"   📖 Сторінок: {len(pdf.pages)}")
            
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                text_lines = len([line.strip() for line in (page.extract_text() or "").split('\n') if line.strip()])
                print(f"   📄 Сторінка {i+1}: {len(tables)} таблиць, {text_lines} рядків тексту")
    except Exception as e:
        print(f"   ❌ Помилка аналізу: {e}")
        return
    
    # Парсинг транзакцій
    print("\n⚙️ ПАРСИНГ ТРАНЗАКЦІЙ:")
    try:
        parser = StatementParser()
        start_time = datetime.now()
        
        transactions = parser.parse_bank_statement(pdf_file, bank_type='monobank')
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"   ✅ Успішно оброблено за {processing_time:.2f} секунд")
        print(f"   📈 Знайдено транзакцій: {len(transactions)}")
        
        if not transactions:
            print("   ⚠️ Транзакції не знайдені")
            return
        
        # Статистика
        income_transactions = [t for t in transactions if t['type'] == 'income']
        expense_transactions = [t for t in transactions if t['type'] == 'expense']
        
        total_income = sum(t['amount'] for t in income_transactions)
        total_expense = sum(t['amount'] for t in expense_transactions)
        
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   💰 Доходи: {len(income_transactions)} транзакцій на суму {total_income:.2f} грн")
        print(f"   💸 Витрати: {len(expense_transactions)} транзакцій на суму {total_expense:.2f} грн")
        print(f"   💵 Баланс: {total_income - total_expense:.2f} грн")
        
        # Найбільші транзакції
        print(f"\n🔝 ТОП-3 НАЙБІЛЬШІ ТРАНЗАКЦІЇ:")
        sorted_transactions = sorted(transactions, key=lambda x: x['amount'], reverse=True)
        for i, transaction in enumerate(sorted_transactions[:3], 1):
            type_icon = "💰" if transaction['type'] == 'income' else "💸"
            print(f"   {i}. {type_icon} {transaction['amount']:.2f} грн - {transaction['description']} ({transaction['date']})")
        
        # Останні транзакції
        print(f"\n📅 ОСТАННІ 5 ТРАНЗАКЦІЙ:")
        sorted_by_date = sorted(transactions, key=lambda x: x['date'], reverse=True)
        for i, transaction in enumerate(sorted_by_date[:5], 1):
            type_icon = "💰" if transaction['type'] == 'income' else "💸"
            print(f"   {i}. {transaction['date']} {transaction.get('time', '00:00:00')} - {type_icon} {transaction['amount']:.2f} грн")
            print(f"      📝 {transaction['description']}")
        
        # Категорії транзакцій
        print(f"\n🏷️ ТИПИ ТРАНЗАКЦІЙ:")
        expense_descriptions = [t['description'] for t in expense_transactions]
        income_descriptions = [t['description'] for t in income_transactions]
        
        # Часто зустрічаються витрати
        expense_keywords = {}
        for desc in expense_descriptions:
            for word in desc.lower().split():
                if len(word) > 3:
                    expense_keywords[word] = expense_keywords.get(word, 0) + 1
        
        if expense_keywords:
            top_expense_keywords = sorted(expense_keywords.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"   💸 Часті витрати: {', '.join([f'{k}({v})' for k, v in top_expense_keywords])}")
        
        # Джерела доходів
        income_keywords = {}
        for desc in income_descriptions:
            for word in desc.lower().split():
                if len(word) > 3:
                    income_keywords[word] = income_keywords.get(word, 0) + 1
        
        if income_keywords:
            top_income_keywords = sorted(income_keywords.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"   💰 Джерела доходу: {', '.join([f'{k}({v})' for k, v in top_income_keywords])}")
        
    except Exception as e:
        print(f"   ❌ Помилка парсингу: {e}")
        import traceback
        traceback.print_exc()

def demo_bot_integration():
    """Демонстрація інтеграції з ботом"""
    print("\n" + "=" * 80)
    print("🤖 ІНТЕГРАЦІЯ З БОТОМ")
    print("=" * 80)
    
    print("📱 Як користуватися новою функціональністю:")
    print()
    print("1️⃣ **Відкрийте бота** і натисніть команду /start")
    print()
    print("2️⃣ **Перейдіть до додавання транзакцій:**")
    print("   • Натисніть '💳 Додати транзакцію'")
    print("   • Оберіть '📤 Завантажити виписку'")
    print()
    print("3️⃣ **Оберіть МоноБанк:**")
    print("   • Натисніть '🏦 МоноБанк'")
    print("   • Оберіть '📄 PDF виписка'")
    print()
    print("4️⃣ **Завантажте PDF файл:**")
    print("   • Натисніть '📤 Надіслати PDF файл'")
    print("   • Виберіть PDF файл з вашою випискою")
    print("   • Надішліть файл боту")
    print()
    print("5️⃣ **Перевірте результат:**")
    print("   • Бот автоматично розпізнає всі транзакції")
    print("   • Покаже кількість знайдених операцій")
    print("   • Додасть їх до вашої бази даних")
    
    print("\n📋 **Що підтримується в PDF виписках МоноБанку:**")
    print("   ✅ Дата та час операції")
    print("   ✅ Сума в гривнях (UAH)")
    print("   ✅ Опис операції (магазин, сервіс)")
    print("   ✅ Автоматичне визначення типу (дохід/витрата)")
    print("   ✅ Обробка багатосторінкових документів")
    print("   ✅ Розпізнавання таблиць з транзакціями")
    
    print("\n⚠️ **Обмеження:**")
    print("   • Максимальний розмір файлу: 10 МБ")
    print("   • Підтримується лише формат PDF")
    print("   • Файл має містити структуровані таблиці")
    
    print("\n💡 **Поради:**")
    print("   • Використовуйте оригінальні PDF виписки з додатку Monobank")
    print("   • Переконайтеся, що виписка містить деталі операцій")
    print("   • Для кращої точності використовуйте CSV або Excel формати")

def demo_supported_formats():
    """Демонстрація підтримуваних форматів"""
    print("\n" + "=" * 80)
    print("📁 ПІДТРИМУВАНІ ФОРМАТИ ФАЙЛІВ")
    print("=" * 80)
    
    formats = {
        "МоноБанк": {
            "CSV": "✅ Рекомендований, найвища точність",
            "Excel (.xls/.xlsx)": "✅ Підтримується, хороша точність",  
            "PDF": "✅ НОВА ФУНКЦІЯ! Базова підтримка"
        },
        "ПриватБанк": {
            "Excel (.xlsx)": "✅ Підтримується",
            "CSV": "❌ Не підтримується",
            "PDF": "❌ Не підтримується"
        },
        "Інші банки": {
            "CSV": "✅ Універсальний формат",
            "Excel": "✅ Базова підтримка",
            "PDF": "✅ Експериментальна підтримка"
        }
    }
    
    for bank, bank_formats in formats.items():
        print(f"\n🏦 **{bank}:**")
        for format_name, support in bank_formats.items():
            print(f"   {format_name}: {support}")

if __name__ == "__main__":
    demo_pdf_parsing()
    demo_bot_integration() 
    demo_supported_formats()
    
    print("\n" + "=" * 80)
    print("🎉 ГОТОВО! PDF підтримка для МоноБанку успішно додана!")
    print("=" * 80)
