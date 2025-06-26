#!/usr/bin/env python3
"""
Простий тест для перевірки роботи категоризації
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Імпортуємо та створюємо парсер
try:
    from services.statement_parser import StatementParser
    from services.ml_categorizer import transaction_categorizer
    parser = StatementParser()
    print("✅ Парсер створено успішно")
    
    # Перевіряємо, чи є метод категоризації в ML категоризаторі
    if hasattr(transaction_categorizer, 'suggest_category_for_bank_statement'):
        print("✅ Метод suggest_category_for_bank_statement знайдено в ML категоризаторі")
        
        # Тестуємо кілька простих випадків
        test_cases = [
            ("Сільпо", "expense"),
            ("Зарплата", "income"),
            ("McDonald's", "expense"),
            ("Кешбек", "income")
        ]
        
        print("\n🧪 Тестування категоризації:")
        for description, trans_type in test_cases:
            try:
                category = transaction_categorizer.suggest_category_for_bank_statement(description, trans_type)
                print(f"✅ '{description}' ({trans_type}) -> '{category}'")
            except Exception as e:
                print(f"❌ Помилка при обробці '{description}': {e}")
    else:
        print("❌ Метод suggest_category_for_bank_statement НЕ знайдено в ML категоризаторі")
        print("Доступні методи в ML категоризаторі:")
        for attr in dir(transaction_categorizer):
            if not attr.startswith('__'):
                print(f"  - {attr}")
        
except Exception as e:
    print(f"❌ Помилка створення парсера: {e}")
    import traceback
    traceback.print_exc()
