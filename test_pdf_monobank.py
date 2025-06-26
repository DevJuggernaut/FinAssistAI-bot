#!/usr/bin/env python3
"""
Тест для перевірки парсингу PDF виписок Monobank
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.statement_parser import StatementParser
import tempfile

def test_monobank_pdf_parsing():
    """Тестує парсинг PDF виписок Monobank"""
    
    print("🚀 Тестування парсингу PDF виписок Monobank")
    print("=" * 60)
    
    parser = StatementParser()
    
    # Створюємо тестові дані у форматі, який може зустрітися в Monobank PDF
    test_pdf_text = """
    ВИПИСКА ПО КАРТЦІ
    Період: 01.01.2025 - 31.01.2025
    
    Дата і час операції    Деталі операції                 MCC    Сума в валюті картки (UAH)
    19.06.2025 14:42:15   Покупка в магазині Сільпо        5411   -150.50
    20.06.2025 09:30:00   McDonald's Київ                  5814   -89.25
    21.06.2025 16:15:30   Uber поїздка                     4121   -95.00
    22.06.2025 12:00:00   Кешбек від покупки               0000   +25.50
    23.06.2025 18:45:12   Комунальні послуги               4900   -850.00
    24.06.2025 10:30:00   Зарплата січень                  0000   +15000.00
    """
    
    print("🧪 Тестування текстового парсингу Monobank...")
    print("-" * 60)
    
    # Тестуємо текстовий парсинг
    transactions = parser._parse_text_transactions(test_pdf_text)
    
    if transactions:
        print(f"✅ Знайдено {len(transactions)} транзакцій")
        
        for i, trans in enumerate(transactions, 1):
            print(f"\nТранзакція {i}:")
            print(f"  📅 Дата: {trans.get('date', 'N/A')}")
            print(f"  🕐 Час: {trans.get('time', 'N/A')}")
            print(f"  💰 Сума: {trans.get('amount', 'N/A')} UAH")
            print(f"  📝 Опис: {trans.get('description', 'N/A')}")
            print(f"  📊 Тип: {trans.get('type', 'N/A')}")
            print(f"  🏷️  Категорія: {trans.get('category', 'N/A')}")
            print(f"  🏦 Джерело: {trans.get('source', 'N/A')}")
            
            # Перевіряємо, що основні поля заповнені
            if not trans.get('description') or trans.get('description') == 'Транзакція':
                print("  ⚠️  Увага: Опис не розпізнано або загальний")
            else:
                print("  ✅ Опис розпізнано правильно")
                
            if not trans.get('category') or trans.get('category') == 'other':
                print("  ⚠️  Увага: Категорія загальна")
            else:
                print("  ✅ Категорія призначена автоматично")
    else:
        print("❌ Транзакції не знайдено")
        return False
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТИ ТЕСТУВАННЯ:")
    
    # Перевіряємо статистику
    total_transactions = len(transactions)
    with_descriptions = sum(1 for t in transactions if t.get('description') and t.get('description') != 'Транзакція')
    with_categories = sum(1 for t in transactions if t.get('category') and t.get('category') != 'other')
    with_dates = sum(1 for t in transactions if t.get('date'))
    with_amounts = sum(1 for t in transactions if t.get('amount'))
    
    print(f"✅ Загальна кількість транзакцій: {total_transactions}")
    print(f"✅ З розпізнаними описами: {with_descriptions}/{total_transactions} ({(with_descriptions/total_transactions)*100:.1f}%)")
    print(f"✅ З автоматичними категоріями: {with_categories}/{total_transactions} ({(with_categories/total_transactions)*100:.1f}%)")
    print(f"✅ З правильними датами: {with_dates}/{total_transactions} ({(with_dates/total_transactions)*100:.1f}%)")
    print(f"✅ З правильними сумами: {with_amounts}/{total_transactions} ({(with_amounts/total_transactions)*100:.1f}%)")
    
    # Визначаємо успішність тесту
    success_rate = (with_descriptions + with_categories + with_dates + with_amounts) / (total_transactions * 4)
    
    if success_rate >= 0.8:  # 80% успішності
        print(f"\n🎉 ТЕСТ ПРОЙДЕНО! Успішність: {success_rate*100:.1f}%")
        print("PDF парсинг Monobank працює добре.")
        return True
    else:
        print(f"\n❌ ТЕСТ НЕ ПРОЙДЕНО! Успішність: {success_rate*100:.1f}%")
        print("Потрібно покращити PDF парсинг для Monobank.")
        return False

def test_different_monobank_formats():
    """Тестує різні формати тексту з Monobank PDF"""
    
    print("\n🔍 Тестування різних форматів тексту Monobank:")
    print("=" * 60)
    
    parser = StatementParser()
    
    test_formats = [
        # Формат 1: З повним часом
        "19.06.2025 14:42:15 Покупка в магазині АТБ -150.50 UAH",
        
        # Формат 2: Без секунд
        "20.06.2025 09:30 McDonald's Київ -89.25",
        
        # Формат 3: Тільки дата
        "21.06.2025 Uber поїздка до аеропорту -95.00 грн",
        
        # Формат 4: З додатковими пробілами
        "22.06.2025  12:00:00    Кешбек від покупки     +25.50",
        
        # Формат 5: Складний опис
        "23.06.2025 18:45 Платіж за комунальні послуги ЖЕК №1 -850.00 UAH",
        
        # Формат 6: Доходи
        "24.06.2025 10:30:00 Зарахування заробітної плати за січень +15000.00"
    ]
    
    total_formats = len(test_formats)
    parsed_successfully = 0
    
    for i, test_text in enumerate(test_formats, 1):
        print(f"\nФормат {i}: {test_text}")
        
        transactions = parser._parse_text_transactions(test_text)
        
        if transactions and len(transactions) > 0:
            trans = transactions[0]
            print(f"  ✅ Розпізнано: {trans.get('description', 'N/A')} | {trans.get('amount', 'N/A')} | {trans.get('category', 'N/A')}")
            parsed_successfully += 1
        else:
            print(f"  ❌ Не розпізнано")
    
    print(f"\n📊 Результат: {parsed_successfully}/{total_formats} форматів розпізнано успішно")
    
    return parsed_successfully / total_formats >= 0.8

if __name__ == "__main__":
    print("🏦 ТЕСТУВАННЯ ПОКРАЩЕНОГО ПАРСИНГУ PDF MONOBANK")
    print("=" * 70)
    
    test1_passed = test_monobank_pdf_parsing()
    test2_passed = test_different_monobank_formats()
    
    print("\n" + "=" * 70)
    print("📋 ПІДСУМОК ТЕСТУВАННЯ PDF ПАРСИНГУ:")
    
    if test1_passed and test2_passed:
        print("✅ Основний тест: ПРОЙДЕНО")
        print("✅ Тест форматів: ПРОЙДЕНО")
        print("\n🎉 ВСІ ТЕСТИ ПРОЙДЕНО! Покращений PDF парсинг готовий.")
    else:
        if not test1_passed:
            print("❌ Основний тест: НЕ ПРОЙДЕНО")
        else:
            print("✅ Основний тест: ПРОЙДЕНО")
            
        if not test2_passed:
            print("❌ Тест форматів: НЕ ПРОЙДЕНО")
        else:
            print("✅ Тест форматів: ПРОЙДЕНО")
            
        print("\n⚠️  Потрібно додатково покращити PDF парсинг.")
