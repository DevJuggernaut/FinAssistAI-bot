"""
Утилітні функції для аналітики та звітності.
Включає функції для форматування даних, обчислення KPI та інших допоміжних операцій.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import calendar
import logging

logger = logging.getLogger(__name__)

class AnalyticsUtils:
    """Утилітні функції для аналітики"""
    
    @staticmethod
    def format_currency(amount: float, currency: str = "грн") -> str:
        """Форматує суму у валюті"""
        return f"{amount:,.2f} {currency}".replace(",", " ")
    
    @staticmethod
    def format_percentage(value: float, decimal_places: int = 1) -> str:
        """Форматує відсоток"""
        return f"{value:.{decimal_places}f}%"
    
    @staticmethod
    def calculate_savings_rate(income: float, expenses: float) -> float:
        """Розраховує коефіцієнт заощаджень"""
        if income <= 0:
            return 0.0
        return ((income - expenses) / income) * 100
    
    @staticmethod
    def calculate_burn_rate(expenses: float, days: int) -> float:
        """Розраховує швидкість витрат (burn rate) на день"""
        if days <= 0:
            return 0.0
        return expenses / days
    
    @staticmethod
    def get_financial_health_level(score: float) -> Tuple[str, str]:
        """Визначає рівень фінансового здоров'я"""
        if score >= 90:
            return "Відмінне", "🟢"
        elif score >= 75:
            return "Дуже добре", "🟢"
        elif score >= 60:
            return "Добре", "🟡"
        elif score >= 45:
            return "Середнє", "🟠"
        elif score >= 30:
            return "Нижче середнього", "🔴"
        else:
            return "Критичне", "🔴"
    
    @staticmethod
    def calculate_monthly_average(transactions: List[Dict], months: int = 3) -> Dict:
        """Розраховує середні показники за кілька місяців"""
        if not transactions:
            return {"income": 0, "expenses": 0, "balance": 0}
        
        # Групуємо по місяцях
        monthly_data = defaultdict(lambda: {"income": 0, "expenses": 0})
        
        for t in transactions:
            month_key = t['transaction_date'].strftime("%Y-%m")
            if t['type'] == 'income':
                monthly_data[month_key]['income'] += t['amount']
            else:
                monthly_data[month_key]['expenses'] += t['amount']
        
        # Беремо останні N місяців
        recent_months = sorted(monthly_data.keys())[-months:]
        
        total_income = sum(monthly_data[month]['income'] for month in recent_months)
        total_expenses = sum(monthly_data[month]['expenses'] for month in recent_months)
        
        months_count = len(recent_months) if recent_months else 1
        
        return {
            "income": total_income / months_count,
            "expenses": total_expenses / months_count,
            "balance": (total_income - total_expenses) / months_count
        }
    
    @staticmethod
    def detect_spending_spikes(daily_expenses: List[float], threshold_multiplier: float = 2.0) -> List[int]:
        """Виявляє дні з різкими стрибками витрат"""
        if len(daily_expenses) < 7:
            return []
        
        expenses_array = np.array(daily_expenses)
        rolling_mean = pd.Series(expenses_array).rolling(window=7, min_periods=3).mean()
        
        spikes = []
        for i, (expense, mean_val) in enumerate(zip(expenses_array, rolling_mean)):
            if not np.isnan(mean_val) and expense > mean_val * threshold_multiplier:
                spikes.append(i)
        
        return spikes
    
    @staticmethod
    def calculate_category_concentration(category_amounts: Dict[str, float]) -> float:
        """Розраховує концентрацію витрат (Herfindahl Index)"""
        total = sum(category_amounts.values())
        if total == 0:
            return 0
        
        # Розраховуємо індекс Херфіндаля-Хіршмана
        hhi = sum((amount / total) ** 2 for amount in category_amounts.values())
        return hhi * 100  # У відсотках
    
    @staticmethod
    def get_top_categories(category_amounts: Dict[str, float], top_n: int = 5) -> List[Tuple[str, float, float]]:
        """Повертає топ категорій з відсотками"""
        total = sum(category_amounts.values())
        if total == 0:
            return []
        
        sorted_categories = sorted(category_amounts.items(), key=lambda x: x[1], reverse=True)
        
        result = []
        for category, amount in sorted_categories[:top_n]:
            percentage = (amount / total) * 100
            result.append((category, amount, percentage))
        
        return result
    
    @staticmethod
    def calculate_weekly_pattern(transactions: List[Dict]) -> Dict[int, float]:
        """Розраховує паттерн витрат по днях тижня"""
        weekday_expenses = defaultdict(float)
        
        for t in transactions:
            if t['type'] == 'expense':
                weekday = t['transaction_date'].weekday()
                weekday_expenses[weekday] += t['amount']
        
        return dict(weekday_expenses)
    
    @staticmethod
    def generate_comparison_text(current: float, previous: float, metric_name: str) -> str:
        """Генерує текст порівняння двох значень"""
        if previous == 0:
            if current > 0:
                return f"{metric_name} з'явились: {current:.2f}"
            else:
                return f"{metric_name} відсутні"
        
        change_percent = ((current - previous) / previous) * 100
        change_abs = current - previous
        
        if abs(change_percent) < 1:
            return f"{metric_name} без змін: {current:.2f}"
        elif change_percent > 0:
            return f"{metric_name} зросли на {change_percent:.1f}% (+{change_abs:.2f})"
        else:
            return f"{metric_name} зменшились на {abs(change_percent):.1f}% ({change_abs:.2f})"
    
    @staticmethod
    def get_month_name_ukrainian(month_num: int) -> str:
        """Повертає назву місяця українською"""
        months = {
            1: "Січень", 2: "Лютий", 3: "Березень", 4: "Квітень",
            5: "Травень", 6: "Червень", 7: "Липень", 8: "Серпень",
            9: "Вересень", 10: "Жовтень", 11: "Листопад", 12: "Грудень"
        }
        return months.get(month_num, f"Місяць {month_num}")
    
    @staticmethod
    def get_weekday_name_ukrainian(weekday_num: int) -> str:
        """Повертає назву дня тижня українською"""
        weekdays = {
            0: "Понеділок", 1: "Вівторок", 2: "Середа", 3: "Четвер",
            4: "П'ятниця", 5: "Субота", 6: "Неділя"
        }
        return weekdays.get(weekday_num, f"День {weekday_num}")

class FinancialKPICalculator:
    """Клас для розрахунку ключових показників ефективності (KPI)"""
    
    @staticmethod
    def calculate_all_kpis(user_data: Dict) -> Dict:
        """Розраховує всі основні KPI"""
        try:
            kpis = {}
            
            # Основні показники
            total_income = user_data.get("total_income", 0)
            total_expenses = user_data.get("total_expenses", 0)
            monthly_budget = user_data.get("monthly_budget", 0)
            
            # 1. Коефіцієнт заощаджень
            kpis["savings_rate"] = AnalyticsUtils.calculate_savings_rate(total_income, total_expenses)
            
            # 2. Швидкість витрат
            days_in_period = user_data.get("days_in_period", 30)
            kpis["burn_rate"] = AnalyticsUtils.calculate_burn_rate(total_expenses, days_in_period)
            
            # 3. Виконання бюджету
            if monthly_budget > 0:
                kpis["budget_utilization"] = (total_expenses / monthly_budget) * 100
            else:
                kpis["budget_utilization"] = 0
            
            # 4. Середній розмір транзакції
            transaction_count = user_data.get("transaction_count", 0)
            if transaction_count > 0:
                kpis["avg_transaction_size"] = total_expenses / transaction_count
            else:
                kpis["avg_transaction_size"] = 0
            
            # 5. Концентрація витрат по категоріях
            category_amounts = user_data.get("category_amounts", {})
            if category_amounts:
                kpis["category_concentration"] = AnalyticsUtils.calculate_category_concentration(category_amounts)
            else:
                kpis["category_concentration"] = 0
            
            # 6. Фінансова стійкість (місяці аварійного фонду)
            monthly_expenses = total_expenses * (30 / days_in_period)  # Нормалізуємо до місяця
            emergency_fund = user_data.get("emergency_fund", 0)
            if monthly_expenses > 0:
                kpis["emergency_fund_months"] = emergency_fund / monthly_expenses
            else:
                kpis["emergency_fund_months"] = 0
            
            return kpis
            
        except Exception as e:
            logger.error(f"Error calculating KPIs: {e}")
            return {}
    
    @staticmethod
    def interpret_kpis(kpis: Dict) -> List[str]:
        """Інтерпретує KPI та генерує рекомендації"""
        interpretations = []
        
        # Коефіцієнт заощаджень
        savings_rate = kpis.get("savings_rate", 0)
        if savings_rate >= 20:
            interpretations.append("💰 Відмінний коефіцієнт заощаджень! Ви на правильному шляху.")
        elif savings_rate >= 10:
            interpretations.append("👍 Хороший коефіцієнт заощаджень. Спробуйте збільшити до 20%.")
        elif savings_rate >= 0:
            interpretations.append("⚠️ Низький коефіцієнт заощаджень. Рекомендуємо оптимізувати витрати.")
        else:
            interpretations.append("🚨 Витрати перевищують доходи! Потрібен план економії.")
        
        # Виконання бюджету
        budget_util = kpis.get("budget_utilization", 0)
        if budget_util > 0:
            if budget_util <= 80:
                interpretations.append("🎯 Чудово! Ви тримаєтесь в межах бюджету.")
            elif budget_util <= 100:
                interpretations.append("📊 Майже вичерпали бюджет. Будьте обережні до кінця місяця.")
            else:
                interpretations.append(f"📈 Перевищили бюджет на {budget_util - 100:.1f}%. Потрібно переглянути витрати.")
        
        # Концентрація витрат
        concentration = kpis.get("category_concentration", 0)
        if concentration > 50:
            interpretations.append("🎯 Високая концентрація витрат в одній категорії. Розгляньте диверсифікацію.")
        elif concentration < 20:
            interpretations.append("📊 Рівномірний розподіл витрат по категоріях.")
        
        # Аварійний фонд
        emergency_months = kpis.get("emergency_fund_months", 0)
        if emergency_months >= 6:
            interpretations.append("🛡️ Відмінний аварійний фонд! Ви захищені від непередбачених витрат.")
        elif emergency_months >= 3:
            interpretations.append("💪 Хороший аварійний фонд. Намагайтесь збільшити до 6 місяців.")
        elif emergency_months >= 1:
            interpretations.append("⚠️ Мінімальний аварійний фонд. Рекомендуємо збільшити.")
        else:
            interpretations.append("🚨 Відсутній аварійний фонд. Це критично важливо для фінансової безпеки!")
        
        return interpretations

# Глобальні утиліти
analytics_utils = AnalyticsUtils()
kpi_calculator = FinancialKPICalculator()
