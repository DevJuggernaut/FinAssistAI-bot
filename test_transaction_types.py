#!/usr/bin/env python3
"""
Тест логіки визначення типу транзакцій для PrivatBank
"""

def test_transaction_type_logic():
    """Тестуємо логіку визначення типу транзакцій"""
    
    # Тестові транзакції з різними описами та сумами
    test_transactions = [
        {'amount': 105.0, 'description': 'Uklon', 'expected': 'expense'},
        {'amount': 186.0, 'description': 'Сім23', 'expected': 'income'},
        {'amount': 0.99, 'description': 'Apple', 'expected': 'expense'},
        {'amount': 450.0, 'description': 'ФОП Мельник Роман Андрийович', 'expected': 'income'},
        {'amount': 65.0, 'description': 'Нова пошта', 'expected': 'expense'},
        {'amount': 458.84, 'description': 'Сільпо', 'expected': 'expense'},
        {'amount': 2.49, 'description': 'Spotify', 'expected': 'expense'},
        {'amount': 528.66, 'description': 'Сільпо', 'expected': 'expense'},
        {'amount': 100.0, 'description': 'АТБ', 'expected': 'expense'},
        {'amount': 118.5, 'description': 'АТБ', 'expected': 'expense'},
        {'amount': 200.0, 'description': 'На картку', 'expected': 'income'},
        {'amount': 1005.03, 'description': 'Степанов Є.', 'expected': 'income'},
        {'amount': -105.0, 'description': 'Якійсь витрата', 'expected': 'expense'},
    ]
    
    print("🧪 Тестування логіки визначення типу транзакцій\n")
    print("=" * 70)
    
    correct = 0
    total = len(test_transactions)
    
    for i, trans in enumerate(test_transactions, 1):
        amount = trans['amount']
        description = trans['description']
        expected = trans['expected']
        
        # Застосовуємо логіку з show_transactions_preview
        trans_type = 'expense'  # За замовчуванням
        
        if isinstance(amount, (int, float)):
            if amount < 0:
                trans_type = 'expense'
                amount = abs(amount)
            else:
                # Для позитивних сум аналізуємо опис
                description_lower = description.lower()
                # Список ключових слів для витрат
                expense_keywords = [
                    'атб', 'сільпо', 'фора', 'ашан', 'metro', 'каррефур',
                    'макдональдс', 'kfc', 'burger', 'pizza', 'кафе', 'ресторан',
                    'аптека', 'фармація', 'pharmacy',
                    'заправка', 'wog', 'okko', 'shell', 'паливо',
                    'uber', 'bolt', 'uklon', 'taxi', 'таксі',
                    'apple', 'google', 'steam', 'netflix', 'spotify',
                    'нова пошта', 'укрпошта', 'deliveri',
                    'оплата', 'платіж', 'купівля', 'покупка'
                ]
                
                # Перевіряємо, чи містить опис ключові слова витрат
                is_expense = any(keyword in description_lower for keyword in expense_keywords)
                
                if is_expense:
                    trans_type = 'expense'
                else:
                    trans_type = 'income'
        
        # Перевіряємо результат
        status = "✅" if trans_type == expected else "❌"
        if trans_type == expected:
            correct += 1
            
        print(f"{i:2d}. {status} {amount:8.2f} ₴ | {description:25s} | {trans_type:7s} (очікувалось: {expected})")
    
    print("=" * 70)
    accuracy = (correct / total) * 100
    print(f"📊 Результат: {correct}/{total} правильних ({accuracy:.1f}% точність)")
    
    if accuracy >= 90:
        print("🎉 Відмінно! Логіка працює правильно.")
    elif accuracy >= 70:
        print("⚠️ Логіка потребує покращення.")
    else:
        print("❌ Логіка потребує серйозних виправлень.")

if __name__ == "__main__":
    test_transaction_type_logic()
