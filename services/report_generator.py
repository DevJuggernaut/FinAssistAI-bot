import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Використовуємо Agg бекенд для роботи без GUI
import numpy as np
import io
import os
import logging
import seaborn as sns
from datetime import datetime, timedelta
import calendar
from sqlalchemy import func, extract
from pathlib import Path
from database.models import Session, Transaction, Category, User, TransactionType
from database.db_operations import get_monthly_stats, get_transactions

# Настроюємо логування
logger = logging.getLogger(__name__)

# Створюємо директорію для збереження звітів
reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
os.makedirs(reports_dir, exist_ok=True)

# Налаштування matplotlib для підтримки української мови
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
# Налаштування стилю seaborn для красивіших графіків
sns.set_style("whitegrid")

class FinancialReport:
    """Клас для генерації фінансових звітів та візуалізацій"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.session = Session()
    
    def __del__(self):
        """Закриваємо сесію при видаленні об'єкта"""
        if self.session:
            self.session.close()
    
    def _get_user_name(self):
        """Отримання імені користувача для звітів"""
        user = self.session.query(User).filter(User.id == self.user_id).first()
        if user:
            if user.first_name and user.last_name:
                return f"{user.first_name} {user.last_name}"
            elif user.first_name:
                return user.first_name
            elif user.username:
                return user.username
        return "Користувач"
    
    def generate_expense_pie_chart(self, year=None, month=None, save_path=None):
        """Генерація кругової діаграми витрат за категоріями"""
        try:
            if year is None or month is None:
                now = datetime.now()
                year = now.year
                month = now.month
            
            # Визначаємо початок і кінець місяця
            start_date = datetime(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime(year, month, last_day, 23, 59, 59)
            
            # Отримуємо дані про витрати за категоріями
            expenses_by_category = self.session.query(
                Category.name, 
                Category.icon,
                func.sum(Transaction.amount).label('total')
            ).join(Transaction, Transaction.category_id == Category.id
            ).filter(
                Transaction.user_id == self.user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date.between(start_date, end_date)
            ).group_by(Category.name, Category.icon
            ).order_by(func.sum(Transaction.amount).desc()).all()
            
            if not expenses_by_category:
                return None, "Немає даних про витрати за вказаний період"
            
            # Підготовка даних для діаграми
            labels = [f"{cat[0]} {cat[1]}" for cat in expenses_by_category]
            values = [cat[2] for cat in expenses_by_category]
            
            # Якщо більше 7 категорій, об'єднуємо найменші в "Інше"
            if len(labels) > 7:
                top_labels = labels[:6]
                top_values = values[:6]
                other_value = sum(values[6:])
                top_labels.append("Інше 📌")
                top_values.append(other_value)
                labels = top_labels
                values = top_values
            
            # Створюємо діаграму з гарним стилем
            plt.figure(figsize=(10, 7))
            colors = sns.color_palette("tab10", len(labels))
            explode = [0.05] * len(labels)  # Трохи "вибухаємо" всі сектори для кращого вигляду
            
            plt.pie(values, labels=None, autopct='%1.1f%%', startangle=90, 
                    colors=colors, explode=explode, shadow=True)
            plt.axis('equal')  # Забезпечує, що кругова діаграма буде намальована як коло
            
            # Додаємо заголовок
            month_names = {
                1: "січень", 2: "лютий", 3: "березень", 4: "квітень",
                5: "травень", 6: "червень", 7: "липень", 8: "серпень",
                9: "вересень", 10: "жовтень", 11: "листопад", 12: "грудень"
            }
            month_name = month_names.get(month, str(month))
            plt.title(f"Розподіл витрат за категоріями: {month_name} {year}", fontsize=16)
            
            # Додаємо легенду за межами діаграми
            plt.legend(labels, loc="center left", bbox_to_anchor=(1, 0.5))
            
            # Тісний вигляд
            plt.tight_layout()
            
            # Зберігаємо або повертаємо діаграму
            if save_path:
                plt.savefig(save_path, dpi=100, bbox_inches='tight')
                plt.close()
                return save_path, None
            else:
                # Зберігаємо в буфер
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
                buffer.seek(0)
                plt.close()
                return buffer, None
                
        except Exception as e:
            logger.error(f"Помилка при створенні кругової діаграми: {e}")
            return None, str(e)
    
    def generate_income_expense_bar_chart(self, months=6, save_path=None):
        """Генерація стовпчикової діаграми доходів і витрат за кілька місяців"""
        try:
            now = datetime.now()
            
            # Підготовка даних за останні N місяців
            labels = []
            income_data = []
            expense_data = []
            
            for i in range(months-1, -1, -1):
                # Визначаємо місяць і рік
                target_month = now.month - i
                target_year = now.year
                while target_month <= 0:
                    target_month += 12
                    target_year -= 1
                
                # Отримуємо дані за цей місяць
                stats = get_monthly_stats(self.user_id, target_year, target_month)
                
                # Додаємо до списків
                month_names = {
                    1: "Січ", 2: "Лют", 3: "Бер", 4: "Кві",
                    5: "Тра", 6: "Чер", 7: "Лип", 8: "Сер",
                    9: "Вер", 10: "Жов", 11: "Лис", 12: "Гру"
                }
                labels.append(f"{month_names.get(target_month)}")
                income_data.append(stats["income"])
                expense_data.append(stats["expenses"])
            
            # Створюємо діаграму з гарним стилем seaborn
            plt.figure(figsize=(12, 6))
            
            x = np.arange(len(labels))
            width = 0.35
            
            plt.bar(x - width/2, income_data, width, label='Доходи', color='#4CAF50', alpha=0.8)
            plt.bar(x + width/2, expense_data, width, label='Витрати', color='#F44336', alpha=0.8)
            
            plt.xlabel('Місяць', fontsize=12)
            plt.ylabel('Сума (грн)', fontsize=12)
            plt.title(f'Порівняння доходів і витрат за останні {months} місяців', fontsize=16)
            plt.xticks(x, labels, fontsize=10)
            plt.legend(fontsize=12)
            
            # Додаємо числові значення над стовпцями
            for i, v in enumerate(income_data):
                plt.text(i - width/2, v + 100, f"{int(v)}", ha='center')
            
            for i, v in enumerate(expense_data):
                plt.text(i + width/2, v + 100, f"{int(v)}", ha='center')
            
            # Додаємо сітку для кращої візуалізації
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            
            # Зберігаємо або повертаємо діаграму
            if save_path:
                plt.savefig(save_path, dpi=100)
                plt.close()
                return save_path, None
            else:
                # Зберігаємо в буфер
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                plt.close()
                return buffer, None
                
        except Exception as e:
            logger.error(f"Помилка при створенні стовпчикової діаграми: {e}")
            return None, str(e)
    
    def generate_expense_trend_chart(self, category_id=None, months=6, save_path=None):
        """Генерація графіка тренду витрат за категорією або всіх витрат"""
        try:
            now = datetime.now()
            
            # Підготовка даних
            labels = []
            expense_data = []
            
            for i in range(months-1, -1, -1):
                # Визначаємо місяць і рік
                target_month = now.month - i
                target_year = now.year
                while target_month <= 0:
                    target_month += 12
                    target_year -= 1
                
                # Визначаємо початок і кінець місяця
                start_date = datetime(target_year, target_month, 1)
                last_day = calendar.monthrange(target_year, target_month)[1]
                end_date = datetime(target_year, target_month, last_day, 23, 59, 59)
                
                # Отримуємо дані про витрати
                query = self.session.query(func.sum(Transaction.amount)
                ).filter(
                    Transaction.user_id == self.user_id,
                    Transaction.type == TransactionType.EXPENSE,
                    Transaction.transaction_date.between(start_date, end_date)
                )
                
                if category_id:
                    query = query.filter(Transaction.category_id == category_id)
                
                expense_sum = query.scalar() or 0
                
                # Додаємо до списків
                month_names = {
                    1: "Січ", 2: "Лют", 3: "Бер", 4: "Кві",
                    5: "Тра", 6: "Чер", 7: "Лип", 8: "Сер",
                    9: "Вер", 10: "Жов", 11: "Лис", 12: "Гру"
                }
                labels.append(f"{month_names.get(target_month)}")
                expense_data.append(expense_sum)
            
            # Отримуємо назву категорії, якщо вказана
            category_name = "всіх категорій"
            if category_id:
                category = self.session.query(Category).filter(Category.id == category_id).first()
                if category:
                    category_name = f"категорії '{category.name}'"
            
            # Створюємо графік з гарним стилем
            plt.figure(figsize=(12, 6))
            # Використовуємо seaborn для красивішого графіка
            sns.lineplot(x=labels, y=expense_data, marker='o', linewidth=2, color='#3F51B5')
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.xlabel('Місяць', fontsize=12)
            plt.ylabel('Сума витрат (грн)', fontsize=12)
            plt.title(f'Тренд витрат для {category_name} за останні {months} місяців', fontsize=16)
            
            # Додаємо числові значення біля точок
            for i, v in enumerate(expense_data):
                plt.text(i, v + max(expense_data) * 0.02, f"{int(v)}", ha='center')
            
            # Додаємо заповнення під кривою для кращого вигляду
            plt.fill_between(range(len(labels)), expense_data, alpha=0.2, color='#3F51B5')
            
            plt.tight_layout()
            
            # Зберігаємо або повертаємо діаграму
            if save_path:
                plt.savefig(save_path, dpi=100)
                plt.close()
                return save_path, None
            else:
                # Зберігаємо в буфер
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                plt.close()
                return buffer, None
                
        except Exception as e:
            logger.error(f"Помилка при створенні графіка тренду: {e}")
            return None, str(e)
    
    def generate_weekly_expense_heatmap(self, weeks=4, save_path=None):
        """Генерація теплової карти витрат по днях тижня і тижнях"""
        try:
            now = datetime.now()
            end_date = now.date()
            start_date = end_date - timedelta(days=weeks*7)
            
            # Отримуємо дані транзакцій
            transactions = self.session.query(
                Transaction.transaction_date,
                Transaction.amount
            ).filter(
                Transaction.user_id == self.user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date.between(start_date, end_date)
            ).all()
            
            if not transactions:
                return None, "Немає даних про витрати за вказаний період"
            
            # Створюємо DataFrame для витрат
            df = pd.DataFrame([
                {
                    'date': t.transaction_date.date(),
                    'weekday': t.transaction_date.weekday(), 
                    'week': (t.transaction_date.date() - start_date).days // 7,
                    'amount': t.amount
                } 
                for t in transactions
            ])
            
            # Групуємо по тижнях та днях тижня
            pivot_data = df.groupby(['week', 'weekday'])['amount'].sum().reset_index()
            pivot_table = pivot_data.pivot('weekday', 'week', 'amount').fillna(0)
            
            # Назви днів тижня
            weekday_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
            
            # Створюємо теплову карту
            plt.figure(figsize=(12, 8))
            ax = sns.heatmap(pivot_table, annot=True, fmt=".0f", cmap="YlOrRd", linewidths=.5)
            
            # Встановлюємо назви осей
            week_labels = [f"Тиждень {i+1}" for i in range(weeks)]
            plt.xticks(np.arange(weeks) + 0.5, week_labels)
            plt.yticks(np.arange(7) + 0.5, weekday_names)
            
            plt.title(f"Теплова карта витрат за останні {weeks} тижні", fontsize=16)
            plt.tight_layout()
            
            # Зберігаємо або повертаємо діаграму
            if save_path:
                plt.savefig(save_path, dpi=100)
                plt.close()
                return save_path, None
            else:
                # Зберігаємо в буфер
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                plt.close()
                return buffer, None
                
        except Exception as e:
            logger.error(f"Помилка при створенні теплової карти: {e}")
            return None, str(e)
    
    def generate_spending_patterns_chart(self, days=30, save_path=None):
        """Генерація діаграми патернів витрат за часом дня"""
        try:
            now = datetime.now()
            start_date = now - timedelta(days=days)
            
            # Отримуємо дані транзакцій
            transactions = self.session.query(
                Transaction.transaction_date,
                Transaction.amount
            ).filter(
                Transaction.user_id == self.user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date >= start_date
            ).all()
            
            if not transactions:
                return None, "Немає даних про витрати за вказаний період"
            
            # Розподіляємо транзакції за годинами дня
            hours = list(range(24))
            hourly_expenses = {hour: 0 for hour in hours}
            
            for transaction in transactions:
                hour = transaction.transaction_date.hour
                hourly_expenses[hour] += transaction.amount
            
            # Перетворюємо дані у формат для графіка
            hours_list = list(hourly_expenses.keys())
            amounts_list = list(hourly_expenses.values())
            
            # Створюємо графік
            plt.figure(figsize=(12, 6))
            
            # Використовуємо seaborn для кращого вигляду
            sns.barplot(x=hours_list, y=amounts_list, alpha=0.8, color="#FF9800")
            
            plt.xlabel("Година дня", fontsize=12)
            plt.ylabel("Сума витрат (грн)", fontsize=12)
            plt.title(f"Розподіл витрат за годинами дня (останні {days} днів)", fontsize=16)
            plt.xticks(np.arange(0, 24, 2)) # Показувати кожні 2 години
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            # Зберігаємо або повертаємо діаграму
            if save_path:
                plt.savefig(save_path, dpi=100)
                plt.close()
                return save_path, None
            else:
                # Зберігаємо в буфер
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                plt.close()
                return buffer, None
                
        except Exception as e:
            logger.error(f"Помилка при створенні графіка патернів витрат: {e}")
            return None, str(e)
    
    def generate_budget_usage_chart(self, year=None, month=None, save_path=None):
        """Генерація діаграми використання бюджету за категоріями"""
        try:
            if year is None or month is None:
                now = datetime.now()
                year = now.year
                month = now.month
            
            # Визначаємо початок і кінець місяця
            start_date = datetime(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime(year, month, last_day, 23, 59, 59)
            
            # Отримуємо категорії та їх бюджет
            from database.models import BudgetPlan, CategoryBudget
            budget_categories = self.session.query(
                Category.id,
                Category.name,
                Category.icon,
                CategoryBudget.allocated_amount
            ).join(CategoryBudget, Category.id == CategoryBudget.category_id
            ).join(BudgetPlan, BudgetPlan.id == CategoryBudget.budget_plan_id
            ).filter(
                BudgetPlan.user_id == self.user_id,
                BudgetPlan.start_date <= end_date,
                BudgetPlan.end_date >= start_date
            ).all()
            
            if not budget_categories:
                return None, "Немає даних про бюджет за вказаний період"
            
            # Збираємо дані про фактичні витрати
            budget_data = []
            for cat_id, name, icon, budget in budget_categories:
                # Отримуємо сумарні витрати по категорії
                actual_expense = self.session.query(
                    func.sum(Transaction.amount)
                ).filter(
                    Transaction.user_id == self.user_id,
                    Transaction.type == TransactionType.EXPENSE,
                    Transaction.category_id == cat_id,
                    Transaction.transaction_date.between(start_date, end_date)
                ).scalar() or 0
                
                # Розраховуємо відсоток використання бюджету
                percentage = (actual_expense / budget) * 100 if budget > 0 else 0
                budget_data.append({
                    'category': f"{name} {icon}",
                    'budget': budget,
                    'actual': actual_expense,
                    'percentage': percentage
                })
            
            # Сортуємо за відсотком використання
            budget_data.sort(key=lambda x: x['percentage'], reverse=True)
            
            # Підготовлюємо дані для графіка
            categories = [item['category'] for item in budget_data]
            percentages = [min(item['percentage'], 100) for item in budget_data]  # Обмежуємо 100%
            
            # Визначаємо кольори в залежності від відсотка
            colors = []
            for pct in percentages:
                if pct < 60:
                    colors.append('#4CAF50')  # Зелений
                elif pct < 85:
                    colors.append('#FF9800')  # Помаранчевий
                else:
                    colors.append('#F44336')  # Червоний
            
            # Створюємо горизонтальну стовпчикову діаграму
            plt.figure(figsize=(10, max(6, len(categories) * 0.5)))
            
            y_pos = np.arange(len(categories))
            
            # Основний графік
            plt.barh(y_pos, percentages, color=colors, alpha=0.8)
            
            # Додаємо вертикальну лінію на 100%
            plt.axvline(x=100, color='red', linestyle='--')
            
            # Додаємо мітки і заголовок
            plt.yticks(y_pos, categories)
            plt.xlabel('Використано бюджету (%)', fontsize=12)
            plt.title('Використання бюджету за категоріями', fontsize=16)
            
            # Додаємо відсотки біля стовпців
            for i, v in enumerate(percentages):
                actual = budget_data[i]['actual']
                budget = budget_data[i]['budget']
                plt.text(v + 1, i, f"{v:.1f}% ({actual:.0f}/{budget:.0f} грн)", va='center')
            
            plt.tight_layout()
            
            # Зберігаємо або повертаємо діаграму
            if save_path:
                plt.savefig(save_path, dpi=100)
                plt.close()
                return save_path, None
            else:
                # Зберігаємо в буфер
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                plt.close()
                return buffer, None
                
        except Exception as e:
            logger.error(f"Помилка при створенні діаграми використання бюджету: {e}")
            return None, str(e)
    
    def generate_monthly_report(self, year=None, month=None):
        """Генерація повного місячного звіту з усіма діаграмами"""
        try:
            if year is None or month is None:
                now = datetime.now()
                year = now.year
                month = now.month
            
            # Отримуємо ім'я користувача
            user_name = self._get_user_name()
            
            # Отримуємо статистику за місяць
            stats = get_monthly_stats(self.user_id, year, month)
            
            # Створюємо директорію для звіту
            report_date = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_dir = os.path.join(reports_dir, f"report_{self.user_id}_{report_date}")
            os.makedirs(report_dir, exist_ok=True)
            
            # Визначаємо назву місяця
            month_names = {
                1: "січень", 2: "лютий", 3: "березень", 4: "квітень",
                5: "травень", 6: "червень", 7: "липень", 8: "серпень",
                9: "вересень", 10: "жовтень", 11: "листопад", 12: "грудень"
            }
            month_name = month_names.get(month, str(month))
            
            # Генеруємо та зберігаємо діаграми
            pie_chart_path = os.path.join(report_dir, 'expense_categories.png')
            pie_chart, pie_error = self.generate_expense_pie_chart(year, month, pie_chart_path)
            
            bar_chart_path = os.path.join(report_dir, 'income_expense.png')
            bar_chart, bar_error = self.generate_income_expense_bar_chart(6, bar_chart_path)
            
            trend_chart_path = os.path.join(report_dir, 'expense_trend.png')
            trend_chart, trend_error = self.generate_expense_trend_chart(None, 6, trend_chart_path)
            
            heatmap_path = os.path.join(report_dir, 'weekly_heatmap.png')
            heatmap, heatmap_error = self.generate_weekly_expense_heatmap(4, heatmap_path)
            
            patterns_path = os.path.join(report_dir, 'spending_patterns.png')
            patterns, patterns_error = self.generate_spending_patterns_chart(30, patterns_path)
            
            # Створюємо HTML звіт
            html_report = f"""
            <!DOCTYPE html>
            <html lang="uk">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Фінансовий звіт за {month_name} {year}</title>
                <style>
                    body {{
                        font-family: 'Arial', sans-serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 20px;
                        color: #333;
                        background-color: #f9f9f9;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: #fff;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 15px rgba(0,0,0,0.1);
                    }}
                    header {{
                        background-color: #2C3E50;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        margin-bottom: 30px;
                        border-radius: 5px;
                    }}
                    h1, h2, h3 {{
                        margin-top: 0;
                    }}
                    .summary-box {{
                        background-color: #f8f9fa;
                        border-left: 4px solid #2C3E50;
                        padding: 15px;
                        margin-bottom: 20px;
                        border-radius: 5px;
                    }}
                    .chart-container {{
                        margin: 30px 0;
                        text-align: center;
                    }}
                    .stat-grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                        gap: 20px;
                        margin: 20px 0;
                    }}
                    .stat-card {{
                        background-color: #f8f9fa;
                        border-radius: 5px;
                        padding: 15px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                        text-align: center;
                    }}
                    .expense {{
                        border-top: 4px solid #e74c3c;
                    }}
                    .income {{
                        border-top: 4px solid #2ecc71;
                    }}
                    .balance {{
                        border-top: 4px solid #3498db;
                    }}
                    .amount {{
                        font-size: 24px;
                        font-weight: bold;
                        margin: 10px 0;
                    }}
                    .positive {{
                        color: #2ecc71;
                    }}
                    .negative {{
                        color: #e74c3c;
                    }}
                    .neutral {{
                        color: #3498db;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }}
                    th, td {{
                        padding: 12px 15px;
                        text-align: left;
                        border-bottom: 1px solid #ddd;
                    }}
                    th {{
                        background-color: #f2f2f2;
                        font-weight: bold;
                    }}
                    tr:hover {{
                        background-color: #f5f5f5;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 1px solid #ddd;
                        color: #777;
                    }}
                    img {{
                        max-width: 100%;
                        height: auto;
                        border-radius: 5px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    }}
                    @media (max-width: 768px) {{
                        .stat-grid {{
                            grid-template-columns: 1fr;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <header>
                        <h1>Фінансовий звіт</h1>
                        <p>{user_name} | {month_name} {year}</p>
                    </header>
                    
                    <div class="summary-box">
                        <h2>Загальна статистика за місяць</h2>
                        <div class="stat-grid">
                            <div class="stat-card expense">
                                <h3>Загальні витрати</h3>
                                <div class="amount negative">{stats["expenses"]:.2f} грн</div>
                            </div>
                            <div class="stat-card income">
                                <h3>Загальні доходи</h3>
                                <div class="amount positive">{stats["income"]:.2f} грн</div>
                            </div>
                            <div class="stat-card balance">
                                <h3>Баланс</h3>
                                <div class="amount {
                                    "positive" if stats["balance"] > 0 else 
                                    "negative" if stats["balance"] < 0 else "neutral"
                                }">{stats["balance"]:.2f} грн</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h2>Розподіл витрат за категоріями</h2>
                        <img src="expense_categories.png" alt="Розподіл витрат">
                    </div>
                    
                    <div class="chart-container">
                        <h2>Порівняння доходів і витрат за півроку</h2>
                        <img src="income_expense.png" alt="Доходи і витрати">
                    </div>
                    
                    <div class="chart-container">
                        <h2>Тренд витрат за останні 6 місяців</h2>
                        <img src="expense_trend.png" alt="Тренд витрат">
                    </div>
                    
                    <div class="chart-container">
                        <h2>Теплова карта витрат за тижнями</h2>
                        <img src="weekly_heatmap.png" alt="Теплова карта витрат">
                    </div>
                    
                    <div class="chart-container">
                        <h2>Патерни витрат за часом дня</h2>
                        <img src="spending_patterns.png" alt="Патерни витрат">
                    </div>
            
                    <div class="summary-box">
                        <h2>Топ категорій витрат</h2>
                        <table>
                            <tr>
                                <th>Категорія</th>
                                <th>Сума</th>
                                <th>% від загальних витрат</th>
                            </tr>
            """
            
            # Додаємо рядки з категоріями витрат
            for category in stats["top_categories"]:
                name, icon, amount = category
                percentage = (amount / stats["expenses"]) * 100 if stats["expenses"] > 0 else 0
                html_report += f"""
                            <tr>
                                <td>{name} {icon}</td>
                                <td>{amount:.2f} грн</td>
                                <td>{percentage:.1f}%</td>
                            </tr>
                """
            
            html_report += f"""
                        </table>
                    </div>
                    
                    <div class="footer">
                        <p>Звіт згенеровано {datetime.now().strftime('%d.%m.%Y о %H:%M')} | FinAssistAI Bot</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Зберігаємо HTML звіт
            report_html_path = os.path.join(report_dir, 'report.html')
            with open(report_html_path, 'w', encoding='utf-8') as f:
                f.write(html_report)
            
            return {
                'report_dir': report_dir,
                'html_path': report_html_path,
                'pie_chart': pie_chart_path if not pie_error else None,
                'bar_chart': bar_chart_path if not bar_error else None,
                'trend_chart': trend_chart_path if not trend_error else None,
                'heatmap': heatmap_path if not heatmap_error else None,
                'patterns': patterns_path if not patterns_error else None
            }
            
        except Exception as e:
            logger.error(f"Помилка при створенні місячного звіту: {e}")
            return None
    
    def generate_pdf_report(self, year=None, month=None):
        """Генерація PDF звіту"""
        try:
            # Цей метод вимагає додаткових бібліотек, таких як weasyprint або pdfkit
            # Для простоти демонстрації, ми можемо використати командний рядок wkhtmltopdf
            # Якщо він встановлений у системі
            
            # Спочатку генеруємо HTML звіт
            report_data = self.generate_monthly_report(year, month)
            
            if 'error' in report_data:
                return {'error': report_data['error']}
            
            html_path = report_data['html_path']
            pdf_path = html_path.replace('.html', '.pdf')
            
            try:
                # Спроба конвертувати HTML в PDF
                import subprocess
                result = subprocess.run(['wkhtmltopdf', html_path, pdf_path], capture_output=True, check=True)
                report_data['pdf_path'] = pdf_path
                
            except FileNotFoundError:
                report_data['pdf_error'] = "Утиліта wkhtmltopdf не знайдена. Встановіть її для генерації PDF."
            except subprocess.CalledProcessError as e:
                report_data['pdf_error'] = f"Помилка при конвертації у PDF: {e}"
            
            return report_data
            
        except Exception as e:
            logger.error(f"Помилка при створенні PDF звіту: {e}")
            return {'error': str(e)}
    
    def export_transactions_csv(self, year=None, month=None):
        """Експорт транзакцій в CSV файл"""
        try:
            if year is None or month is None:
                now = datetime.now()
                year = now.year
                month = now.month
            
            # Визначаємо початок і кінець місяця
            start_date = datetime(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime(year, month, last_day, 23, 59, 59)
            
            # Отримуємо транзакції
            transactions = self.session.query(
                Transaction.transaction_date,
                Transaction.description,
                Transaction.amount,
                Transaction.type,
                Category.name.label('category_name'),
                Category.icon.label('category_icon')
            ).join(Category, Transaction.category_id == Category.id
            ).filter(
                Transaction.user_id == self.user_id,
                Transaction.transaction_date.between(start_date, end_date)
            ).order_by(Transaction.transaction_date.desc()).all()
            
            if not transactions:
                return None, "Немає транзакцій за вказаний період"
            
            # Створюємо DataFrame
            data = []
            for t in transactions:
                data.append({
                    'Дата': t.transaction_date.strftime('%d.%m.%Y'),
                    'Опис': t.description,
                    'Сума': t.amount,
                    'Тип': 'Витрата' if t.type == TransactionType.EXPENSE else 'Дохід',
                    'Категорія': f"{t.category_name} {t.category_icon}"
                })
            
            df = pd.DataFrame(data)
            
            # Зберігаємо в CSV
            month_names = {
                1: "січень", 2: "лютий", 3: "березень", 4: "квітень",
                5: "травень", 6: "червень", 7: "липень", 8: "серпень",
                9: "вересень", 10: "жовтень", 11: "листопад", 12: "грудень"
            }
            month_name = month_names.get(month, str(month))
            
            csv_dir = os.path.join(reports_dir, f"export_{self.user_id}")
            os.makedirs(csv_dir, exist_ok=True)
            
            csv_path = os.path.join(csv_dir, f"transactions_{year}_{month}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            return csv_path, None
            
        except Exception as e:
            logger.error(f"Помилка при експорті транзакцій в CSV: {e}")
            return None, str(e)


# Функції для використання у інших модулях
def generate_user_report(user_id, year=None, month=None, format='html'):
    """Створює звіт для користувача"""
    report_generator = FinancialReport(user_id)
    
    if format == 'pdf':
        return report_generator.generate_pdf_report(year, month)
    else:  # html
        return report_generator.generate_monthly_report(year, month)

def export_user_transactions(user_id, year=None, month=None):
    """Експортує транзакції користувача в CSV"""
    report_generator = FinancialReport(user_id)
    return report_generator.export_transactions_csv(year, month)
