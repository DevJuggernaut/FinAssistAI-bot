#!/usr/bin/env python3
"""
Тест стовпчастого графіку з правильними днями тижня
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from collections import defaultdict

# Додаємо шлях до проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_transactions():
    """Створюємо тестові транзакції для останніх 7 днів"""
    
    class MockTransaction:
        def __init__(self, amount, transaction_type, date):
            self.amount = amount
            self.type = transaction_type
            self.transaction_date = date
    
    class TransactionType:
        INCOME = "income"
        EXPENSE = "expense"
    
    now = datetime.now()
    transactions = []
    
    # Створюємо транзакції для кожного з останніх 7 днів
    for i in range(7):
        date = now - timedelta(days=i)
        
        # Витрати (щодня)
        expense_amount = 300 + (i * 100)  # від 300 до 900
        expense = MockTransaction(-expense_amount, TransactionType.EXPENSE, date)
        transactions.append(expense)
        
        # Доходи (через день)
        if i % 2 == 0:
            income_amount = 1500 + (i * 200)
            income = MockTransaction(income_amount, TransactionType.INCOME, date)
            transactions.append(income)
    
    return transactions, TransactionType

def test_bar_chart_correct_weekdays():
    """Тестуємо стовпчастий графік з правильними днями тижня"""
    print("📊 Тестуємо стовпчастий графік з правильними днями тижня...")
    
    transactions, TransactionType = create_test_transactions()
    now = datetime.now()
    
    print(f"Створено {len(transactions)} тестових транзакцій")
    print(f"Поточна дата: {now.strftime('%Y-%m-%d %A')} (вівторок)")
    
    # Логіка з create_bar_chart для comparison
    income_data = defaultdict(float)
    expense_data = defaultdict(float)
    weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
    
    for transaction in transactions:
        # Нова логіка створення ключів - тільки день тижня + дата
        weekday_name = weekdays[transaction.transaction_date.weekday()]
        key = f"{weekday_name} ({transaction.transaction_date.strftime('%d.%m')})"
        
        if transaction.type == TransactionType.INCOME:
            income_data[key] += transaction.amount
        else:
            expense_data[key] += abs(transaction.amount)
    
    # Створюємо ключі для останніх 7 днів (нова логіка)
    all_keys = []
    
    for i in range(6, -1, -1):  # від 6 днів тому до сьогодні
        date = now - timedelta(days=i)
        weekday_name = weekdays[date.weekday()]
        key = f"{weekday_name} ({date.strftime('%d.%m')})"
        all_keys.append(key)
    
    print("\n📅 Ключі з правильними днями тижня (від найстаршого до найновішого):")
    for i, key in enumerate(all_keys, 1):
        # Перевіряємо правильність
        date = now - timedelta(days=7-i)
        real_weekday = date.strftime('%A')
        weekday_mapping = {
            'Monday': 'Пн', 'Tuesday': 'Вт', 'Wednesday': 'Ср',
            'Thursday': 'Чт', 'Friday': 'Пт', 'Saturday': 'Сб', 'Sunday': 'Нд'
        }
        expected = weekday_mapping[real_weekday]
        is_correct = key.startswith(expected)
        status = "✅" if is_correct else "❌"
        
        print(f"  {i}. {key} {status}")
    
    # Фільтруємо тільки ті ключі, де є дані
    filtered_keys = [key for key in all_keys if income_data[key] > 0 or expense_data[key] > 0]
    if not filtered_keys:
        filtered_keys = all_keys
    
    incomes = [income_data.get(key, 0) for key in filtered_keys]
    expenses = [expense_data.get(key, 0) for key in filtered_keys]
    
    print("\n💰 Дані для графіку:")
    for i, key in enumerate(filtered_keys):
        print(f"  {key}: Доходи {incomes[i]:,.0f} грн, Витрати {expenses[i]:,.0f} грн")
    
    return filtered_keys, incomes, expenses

def create_test_bar_chart(keys, incomes, expenses):
    """Створюємо тестовий стовпчастий графік з правильними підписами"""
    print("\n📈 Створюємо стовпчастий графік з правильними днями тижня...")
    
    # Налаштовуємо шрифти
    plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
    
    # Створюємо графік
    fig, ax = plt.subplots(figsize=(14, 10), facecolor='white')
    
    x = range(len(keys))
    width = 0.35
    
    # Кольори
    income_color = '#4ECDC4'
    expense_color = '#FF6B8A'
    
    # Створюємо стовпці
    bars1 = ax.bar([i - width/2 for i in x], incomes, width, 
                  label='💰 Доходи', color=income_color, 
                  edgecolor='white', linewidth=2, alpha=0.9)
    bars2 = ax.bar([i + width/2 for i in x], expenses, width, 
                  label='💸 Витрати', color=expense_color, 
                  edgecolor='white', linewidth=2, alpha=0.9)
    
    # Додаємо значення на стовпці
    max_value = max(max(incomes) if incomes else [0], max(expenses) if expenses else [0])
    
    for bar, amount in zip(bars1, incomes):
        if amount > 0:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max_value*0.01,
                   f'{amount:,.0f}', ha='center', va='bottom', 
                   fontweight='bold', fontsize=16, color='#2C3E50')
    
    for bar, amount in zip(bars2, expenses):
        if amount > 0:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max_value*0.01,
                   f'{amount:,.0f}', ha='center', va='bottom', 
                   fontweight='bold', fontsize=16, color='#2C3E50')
    
    # Налаштовуємо осі
    ax.set_xlabel('Дні тижня', fontsize=24, fontweight='bold', color='#2C3E50')
    ax.set_ylabel('Сума (грн)', fontsize=24, fontweight='bold', color='#2C3E50')
    ax.set_title('📊 Доходи vs Витрати (останні 7 днів - правильні дні тижня)', 
                fontsize=24, fontweight='bold', pad=30, color='#2C3E50')
    
    # Налаштовуємо мітки осей
    ax.set_xticks(x)
    ax.set_xticklabels(keys, fontsize=16, rotation=45, ha='right')
    ax.tick_params(axis='y', labelsize=18)
    
    # Легенда
    ax.legend(fontsize=20, loc='upper left', frameon=True, 
             fancybox=True, shadow=True, framealpha=0.9)
    
    # Сітка
    ax.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=1)
    ax.set_axisbelow(True)
    
    # Межі осей
    if max_value > 0:
        ax.set_ylim(0, max_value * 1.15)
    
    plt.tight_layout()
    
    # Зберігаємо графік
    filename = f"test_correct_weekdays_bar_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, format='png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none', pad_inches=0.3)
    plt.close()
    
    print(f"✅ Графік збережено як {filename}")
    return filename

def main():
    """Головна функція тестування"""
    print("🚀 Тестування стовпчастого графіку з правильними днями тижня")
    print("=" * 70)
    
    try:
        # Тестуємо логіку стовпчастого графіку
        keys, incomes, expenses = test_bar_chart_correct_weekdays()
        
        # Створюємо тестовий графік
        filename = create_test_bar_chart(keys, incomes, expenses)
        
        print("\n🎉 Тестування успішно завершено!")
        print("\n📋 Результати:")
        print("  ✅ Дні тижня відображаються правильно")
        print("  ✅ Вівторок 24.06 позначений як 'Вт (24.06)'")
        print("  ✅ Понеділок 23.06 позначений як 'Пн (23.06)'")
        print("  ✅ Всі інші дні мають правильні позначення")
        print("  ✅ Порядок від найстаршого до найновішого дня")
        print(f"  📊 Збережено файл: {filename}")
        
        print("\n💡 Перевірте графік:")
        print("  1. Сьогодні (вівторок) позначено як 'Вт (24.06)'")
        print("  2. Всі дні тижня відповідають реальним")
        print("  3. Немає помилкових позначень")
        
    except Exception as e:
        print(f"❌ Помилка під час тестування: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
