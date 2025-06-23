"""
Розширений модуль аналітики для FinAssist бота.
Включає нові візуалізації, тренди, прогнози та інсайти.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import calendar
import io
import logging
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
import warnings
warnings.filterwarnings('ignore')

# Налаштування matplotlib
plt.style.use('default')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

logger = logging.getLogger(__name__)

class AdvancedAnalytics:
    """Розширений клас для фінансової аналітики з новими візуалізаціями"""
    
    def __init__(self):
        # Кольори для категорій
        self.category_colors = {
            'Їжа': '#FF6B6B',
            'Транспорт': '#4ECDC4', 
            'Розваги': '#45B7D1',
            'Здоров\'я': '#96CEB4',
            'Одяг': '#FECA57',
            'Дім': '#FF9FF3',
            'Освіта': '#54A0FF',
            'Інше': '#95A5A6'
        }
    
    def create_spending_heatmap(self, transactions: List[Dict]) -> io.BytesIO:
        """Створює теплову карту витрат по днях тижня та годинах"""
        try:
            # Підготовка даних
            df = pd.DataFrame([
                {
                    'hour': t['transaction_date'].hour,
                    'weekday': t['transaction_date'].weekday(),
                    'amount': t['amount'] if t['type'] == 'expense' else 0
                }
                for t in transactions if t['type'] == 'expense'
            ])
            
            if df.empty:
                return self._create_no_data_chart("Немає даних про витрати")
            
            # Створюємо матрицю для теплової карти
            heatmap_data = df.groupby(['weekday', 'hour'])['amount'].sum().unstack(fill_value=0)
            
            # Створюємо графік
            plt.figure(figsize=(14, 8))
            
            # Імена днів тижня українською
            weekday_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
            
            # Теплова карта
            sns.heatmap(
                heatmap_data, 
                cmap='YlOrRd',
                annot=False,
                fmt='.0f',
                cbar_kws={'label': 'Сума витрат (грн)'},
                yticklabels=weekday_names
            )
            
            plt.title('🔥 Теплова карта витрат по днях та годинах', fontsize=16, fontweight='bold')
            plt.xlabel('Година дня')
            plt.ylabel('День тижня')
            plt.tight_layout()
            
            # Зберігаємо в буфер
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error creating spending heatmap: {e}")
            return self._create_error_chart("Помилка створення теплової карти")
    
    def create_cash_flow_chart(self, transactions: List[Dict]) -> io.BytesIO:
        """Створює графік грошового потоку (доходи vs витрати)"""
        try:
            # Підготовка даних
            df = pd.DataFrame(transactions)
            df['date'] = pd.to_datetime(df['transaction_date']).dt.date
            
            # Групування по датах
            daily_data = df.groupby(['date', 'type'])['amount'].sum().unstack(fill_value=0)
            
            if 'income' not in daily_data.columns:
                daily_data['income'] = 0
            if 'expense' not in daily_data.columns:
                daily_data['expense'] = 0
            
            # Обчислюємо кумулятивний баланс
            daily_data['balance'] = daily_data['income'] - daily_data['expense']
            daily_data['cumulative_balance'] = daily_data['balance'].cumsum()
            
            # Створюємо графік
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            
            # Графік 1: Щоденні доходи та витрати
            x = daily_data.index
            ax1.bar(x, daily_data['income'], alpha=0.7, color='#2ECC71', label='Доходи')
            ax1.bar(x, -daily_data['expense'], alpha=0.7, color='#E74C3C', label='Витрати')
            ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            ax1.set_title('💰 Щоденні доходи та витрати', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Сума (грн)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Графік 2: Кумулятивний баланс
            ax2.plot(x, daily_data['cumulative_balance'], 
                    color='#3498DB', linewidth=2, marker='o', markersize=4)
            ax2.fill_between(x, daily_data['cumulative_balance'], 
                           alpha=0.3, color='#3498DB')
            ax2.axhline(y=0, color='red', linestyle='--', alpha=0.7)
            
            ax2.set_title('📈 Кумулятивний баланс', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Баланс (грн)')
            ax2.set_xlabel('Дата')
            ax2.grid(True, alpha=0.3)
            
            # Форматування дат
            for ax in [ax1, ax2]:
                ax.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Зберігаємо в буфер
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error creating cash flow chart: {e}")
            return self._create_error_chart("Помилка створення графіку грошового потоку")
    
    def create_category_trends_chart(self, transactions: List[Dict]) -> io.BytesIO:
        """Створює графік трендів по категоріях"""
        try:
            # Підготовка даних
            df = pd.DataFrame([
                {
                    'date': t['transaction_date'].date(),
                    'category': t.get('category_name', 'Без категорії'),
                    'amount': t['amount']
                }
                for t in transactions if t['type'] == 'expense'
            ])
            
            if df.empty:
                return self._create_no_data_chart("Немає даних про витрати по категоріях")
            
            # Групуємо по датах та категоріях
            pivot_data = df.groupby(['date', 'category'])['amount'].sum().unstack(fill_value=0)
            
            # Обираємо топ-5 категорій за сумою
            total_by_category = pivot_data.sum().sort_values(ascending=False)
            top_categories = total_by_category.head(5).index
            
            # Створюємо графік
            plt.figure(figsize=(14, 8))
            
            colors = plt.cm.Set3(np.linspace(0, 1, len(top_categories)))
            
            for i, category in enumerate(top_categories):
                if category in pivot_data.columns:
                    plt.plot(pivot_data.index, pivot_data[category], 
                           marker='o', linewidth=2, label=category, color=colors[i])
            
            plt.title('📊 Тренди витрат по категоріях', fontsize=16, fontweight='bold')
            plt.xlabel('Дата')
            plt.ylabel('Сума витрат (грн)')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Зберігаємо в буфер
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error creating category trends chart: {e}")
            return self._create_error_chart("Помилка створення графіку трендів")
    
    def create_spending_patterns_chart(self, transactions: List[Dict]) -> io.BytesIO:
        """Створює графік паттернів витрат (по днях тижня та місяцях)"""
        try:
            # Підготовка даних
            df = pd.DataFrame([
                {
                    'weekday': t['transaction_date'].weekday(),
                    'month': t['transaction_date'].month,
                    'amount': t['amount']
                }
                for t in transactions if t['type'] == 'expense'
            ])
            
            if df.empty:
                return self._create_no_data_chart("Немає даних про витрати")
            
            # Створюємо підграфіки
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            # Графік 1: Витрати по днях тижня
            weekday_stats = df.groupby('weekday')['amount'].agg(['sum', 'count', 'mean'])
            weekday_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
            
            bars1 = ax1.bar(range(7), weekday_stats['sum'], 
                           color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', 
                                  '#FECA57', '#FF9FF3', '#54A0FF'])
            ax1.set_title('📅 Витрати по днях тижня', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Загальна сума (грн)')
            ax1.set_xticks(range(7))
            ax1.set_xticklabels(weekday_names)
            
            # Додаємо підписи на стовпці
            for i, bar in enumerate(bars1):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.0f}', ha='center', va='bottom')
            
            # Графік 2: Витрати по місяцях
            month_stats = df.groupby('month')['amount'].agg(['sum', 'count', 'mean'])
            month_names = [calendar.month_abbr[i] for i in range(1, 13)]
            existing_months = month_stats.index
            
            bars2 = ax2.bar(existing_months, month_stats['sum'], 
                           color='#3498DB', alpha=0.7)
            ax2.set_title('📆 Витрати по місяцях', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Загальна сума (грн)')
            ax2.set_xlabel('Місяць')
            ax2.set_xticks(existing_months)
            ax2.set_xticklabels([month_names[m-1] for m in existing_months])
            
            # Додаємо підписи на стовпці
            for bar in bars2:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.0f}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Зберігаємо в буфер
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error creating spending patterns chart: {e}")
            return self._create_error_chart("Помилка створення графіку паттернів")
    
    def create_budget_vs_actual_chart(self, transactions: List[Dict], 
                                     monthly_budget: float = None) -> io.BytesIO:
        """Створює порівняння бюджету з фактичними витратами"""
        try:
            if not monthly_budget:
                return self._create_no_data_chart("Бюджет не встановлено")
            
            # Підготовка даних
            df = pd.DataFrame([
                {
                    'date': t['transaction_date'],
                    'amount': t['amount'],
                    'category': t.get('category_name', 'Без категорії')
                }
                for t in transactions if t['type'] == 'expense'
            ])
            
            if df.empty:
                return self._create_no_data_chart("Немає даних про витрати")
            
            # Групуємо по місяцях
            df['month_year'] = df['date'].dt.to_period('M')
            monthly_expenses = df.groupby('month_year')['amount'].sum()
            
            # Створюємо графік
            plt.figure(figsize=(14, 8))
            
            x = range(len(monthly_expenses))
            months = [str(m) for m in monthly_expenses.index]
            
            # Стовпці фактичних витрат
            colors = ['#E74C3C' if expense > monthly_budget else '#2ECC71' 
                     for expense in monthly_expenses.values]
            
            bars = plt.bar(x, monthly_expenses.values, color=colors, alpha=0.7, 
                          label='Фактичні витрати')
            
            # Лінія бюджету
            plt.axhline(y=monthly_budget, color='#3498DB', linestyle='--', 
                       linewidth=2, label=f'Бюджет ({monthly_budget:.0f} грн)')
            
            # Підписи на стовпцях
            for i, (bar, value) in enumerate(zip(bars, monthly_expenses.values)):
                height = bar.get_height()
                color = 'red' if value > monthly_budget else 'green'
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.0f}', ha='center', va='bottom', color=color, fontweight='bold')
            
            plt.title('💰 Бюджет vs Фактичні витрати', fontsize=16, fontweight='bold')
            plt.xlabel('Місяць')
            plt.ylabel('Сума (грн)')
            plt.xticks(x, months, rotation=45)
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Зберігаємо в буфер
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error creating budget vs actual chart: {e}")
            return self._create_error_chart("Помилка створення графіку бюджету")
    
    def create_expense_distribution_donut(self, transactions: List[Dict]) -> io.BytesIO:
        """Створює пончикову діаграму розподілу витрат"""
        try:
            # Підготовка даних
            category_totals = defaultdict(float)
            for t in transactions:
                if t['type'] == 'expense':
                    category = t.get('category_name', 'Без категорії')
                    category_totals[category] += t['amount']
            
            if not category_totals:
                return self._create_no_data_chart("Немає даних про витрати")
            
            # Сортуємо та берємо топ-6
            sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
            
            if len(sorted_categories) > 6:
                top_categories = sorted_categories[:5]
                other_sum = sum(amount for _, amount in sorted_categories[5:])
                top_categories.append(('Інше', other_sum))
            else:
                top_categories = sorted_categories
            
            labels = [cat for cat, _ in top_categories]
            values = [amount for _, amount in top_categories]
            
            # Створюємо пончикову діаграму
            plt.figure(figsize=(12, 8))
            
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
            
            wedges, texts, autotexts = plt.pie(values, labels=labels, autopct='%1.1f%%',
                                              colors=colors, startangle=90, 
                                              pctdistance=0.85)
            
            # Створюємо отвір в центрі
            centre_circle = plt.Circle((0,0), 0.50, fc='white')
            fig = plt.gcf()
            fig.gca().add_artist(centre_circle)
            
            # Центральний текст
            total = sum(values)
            plt.text(0, 0, f'Всього\n{total:.0f} грн', ha='center', va='center', 
                    fontsize=14, fontweight='bold')
            
            plt.title('🍩 Розподіл витрат по категоріях', fontsize=16, fontweight='bold', y=1.02)
            plt.axis('equal')
            
            # Зберігаємо в буфер
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error creating donut chart: {e}")
            return self._create_error_chart("Помилка створення пончикової діаграми")
    
    def _create_no_data_chart(self, message: str) -> io.BytesIO:
        """Створює заглушку, коли немає даних"""
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, message, ha='center', va='center', 
                fontsize=16, transform=plt.gca().transAxes)
        plt.title('📊 Аналітика')
        plt.axis('off')
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def _create_error_chart(self, message: str) -> io.BytesIO:
        """Створює графік з повідомленням про помилку"""
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, f"❌ {message}", ha='center', va='center', 
                fontsize=16, color='red', transform=plt.gca().transAxes)
        plt.title('Помилка аналітики')
        plt.axis('off')
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer

# Глобальний екземпляр для використання в інших модулях
advanced_analytics = AdvancedAnalytics()
