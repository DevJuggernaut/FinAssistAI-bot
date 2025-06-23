"""
Модуль для генерації персоналізованих фінансових інсайтів та рекомендацій.
Включає аналіз фінансового здоров'я, цілі та поради.
"""

import numpy as np
from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple, Optional
import logging
import calendar
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class FinancialInsightsEngine:
    """Двигун для генерації персоналізованих фінансових інсайтів"""
    
    def __init__(self):
        # Еталонні значення для порівняння
        self.benchmarks = {
            "savings_rate": {
                "excellent": 0.20,  # 20%+
                "good": 0.15,       # 15-20%
                "average": 0.10,    # 10-15%
                "poor": 0.05        # 5-10%
            },
            "emergency_fund_months": {
                "excellent": 6,
                "good": 4,
                "average": 3,
                "poor": 1
            }
        }
    
    def generate_financial_health_score(self, user_data: Dict) -> Dict:
        """Генерує оцінку фінансового здоров'я користувача"""
        try:
            score_components = {}
            total_score = 0
            max_score = 0
            
            # 1. Коефіцієнт заощаджень (30% ваги)
            savings_score = self._calculate_savings_score(user_data)
            score_components["savings"] = savings_score
            total_score += savings_score["score"] * 0.30
            max_score += 100 * 0.30
            
            # 2. Стабільність витрат (25% ваги)
            stability_score = self._calculate_spending_stability(user_data)
            score_components["stability"] = stability_score
            total_score += stability_score["score"] * 0.25
            max_score += 100 * 0.25
            
            # 3. Дотримання бюджету (25% ваги)
            budget_score = self._calculate_budget_adherence(user_data)
            score_components["budget"] = budget_score
            total_score += budget_score["score"] * 0.25
            max_score += 100 * 0.25
            
            # 4. Різноманітність доходів (20% ваги)
            income_score = self._calculate_income_diversity(user_data)
            score_components["income"] = income_score
            total_score += income_score["score"] * 0.20
            max_score += 100 * 0.20
            
            # Загальна оцінка
            final_score = (total_score / max_score) * 100 if max_score > 0 else 0
            
            # Визначаємо рівень
            if final_score >= 80:
                health_level = "Відмінний"
                emoji = "🟢"
            elif final_score >= 60:
                health_level = "Хороший"
                emoji = "🟡"
            elif final_score >= 40:
                health_level = "Середній"
                emoji = "🟠"
            else:
                health_level = "Потребує покращення"
                emoji = "🔴"
            
            return {
                "overall_score": final_score,
                "health_level": health_level,
                "emoji": emoji,
                "components": score_components,
                "recommendations": self._generate_health_recommendations(score_components)
            }
            
        except Exception as e:
            logger.error(f"Error generating financial health score: {e}")
            return {"error": "Помилка розрахунку фінансового здоров'я"}
    
    def _calculate_savings_score(self, user_data: Dict) -> Dict:
        """Розраховує оцінку заощаджень"""
        try:
            total_income = user_data.get("total_income", 0)
            total_expenses = user_data.get("total_expenses", 0)
            
            if total_income <= 0:
                return {"score": 0, "description": "Немає даних про доходи"}
            
            savings_rate = (total_income - total_expenses) / total_income
            
            if savings_rate >= self.benchmarks["savings_rate"]["excellent"]:
                score = 100
                description = f"Відмінно! Ви заощаджуєте {savings_rate*100:.1f}% доходів"
            elif savings_rate >= self.benchmarks["savings_rate"]["good"]:
                score = 80
                description = f"Добре! Заощадження {savings_rate*100:.1f}% доходів"
            elif savings_rate >= self.benchmarks["savings_rate"]["average"]:
                score = 60
                description = f"Середньо. Заощадження {savings_rate*100:.1f}% доходів"
            elif savings_rate >= self.benchmarks["savings_rate"]["poor"]:
                score = 40
                description = f"Низько. Заощадження лише {savings_rate*100:.1f}% доходів"
            else:
                score = 20
                description = "Витрати перевищують доходи"
            
            return {
                "score": score,
                "savings_rate": savings_rate,
                "description": description
            }
            
        except Exception as e:
            logger.error(f"Error calculating savings score: {e}")
            return {"score": 0, "description": "Помилка розрахунку"}
    
    def _calculate_spending_stability(self, user_data: Dict) -> Dict:
        """Розраховує стабільність витрат"""
        try:
            daily_expenses = user_data.get("daily_expenses", [])
            
            if len(daily_expenses) < 7:
                return {"score": 50, "description": "Недостатньо даних для оцінки стабільності"}
            
            # Розраховуємо коефіцієнт варіації
            expenses_array = np.array(daily_expenses)
            mean_expense = np.mean(expenses_array)
            std_expense = np.std(expenses_array)
            
            if mean_expense == 0:
                cv = 0
            else:
                cv = std_expense / mean_expense
            
            # Оцінюємо стабільність
            if cv <= 0.3:
                score = 100
                description = "Дуже стабільні витрати"
            elif cv <= 0.5:
                score = 80
                description = "Стабільні витрати"
            elif cv <= 0.8:
                score = 60
                description = "Помірно нестабільні витрати"
            elif cv <= 1.2:
                score = 40
                description = "Нестабільні витрати"
            else:
                score = 20
                description = "Дуже нестабільні витрати"
            
            return {
                "score": score,
                "coefficient_of_variation": cv,
                "description": description
            }
            
        except Exception as e:
            logger.error(f"Error calculating spending stability: {e}")
            return {"score": 50, "description": "Помилка розрахунку стабільності"}
    
    def _calculate_budget_adherence(self, user_data: Dict) -> Dict:
        """Розраховує дотримання бюджету"""
        try:
            monthly_budget = user_data.get("monthly_budget")
            total_expenses = user_data.get("total_expenses", 0)
            
            if not monthly_budget or monthly_budget <= 0:
                return {"score": 50, "description": "Бюджет не встановлено"}
            
            budget_usage = total_expenses / monthly_budget
            
            if budget_usage <= 0.8:
                score = 100
                description = f"Відмінно! Використано {budget_usage*100:.1f}% бюджету"
            elif budget_usage <= 0.95:
                score = 80
                description = f"Добре! Використано {budget_usage*100:.1f}% бюджету"
            elif budget_usage <= 1.0:
                score = 60
                description = f"Використано {budget_usage*100:.1f}% бюджету"
            elif budget_usage <= 1.1:
                score = 40
                description = f"Перевищено бюджет на {(budget_usage-1)*100:.1f}%"
            else:
                score = 20
                description = f"Значне перевищення бюджету на {(budget_usage-1)*100:.1f}%"
            
            return {
                "score": score,
                "budget_usage": budget_usage,
                "description": description
            }
            
        except Exception as e:
            logger.error(f"Error calculating budget adherence: {e}")
            return {"score": 50, "description": "Помилка розрахунку дотримання бюджету"}
    
    def _calculate_income_diversity(self, user_data: Dict) -> Dict:
        """Розраховує різноманітність джерел доходу"""
        try:
            income_sources = user_data.get("income_sources", [])
            
            if not income_sources:
                return {"score": 30, "description": "Немає даних про джерела доходу"}
            
            # Підраховуємо кількість різних джерел
            unique_sources = len(set(income_sources))
            
            if unique_sources >= 3:
                score = 100
                description = f"Відмінно! {unique_sources} джерел доходу"
            elif unique_sources == 2:
                score = 70
                description = "Добре! Два джерела доходу"
            else:
                score = 40
                description = "Одне джерело доходу - ризиковано"
            
            return {
                "score": score,
                "unique_sources": unique_sources,
                "description": description
            }
            
        except Exception as e:
            logger.error(f"Error calculating income diversity: {e}")
            return {"score": 30, "description": "Помилка розрахунку різноманітності доходів"}
    
    def _generate_health_recommendations(self, components: Dict) -> List[str]:
        """Генерує рекомендації на основі оцінок компонентів"""
        recommendations = []
        
        # Рекомендації по заощадженнях
        savings = components.get("savings", {})
        if savings.get("score", 0) < 60:
            recommendations.append("💰 Спробуйте збільшити заощадження до 15% від доходів")
        
        # Рекомендації по стабільності
        stability = components.get("stability", {})
        if stability.get("score", 0) < 60:
            recommendations.append("📊 Плануйте витрати заздалегідь для більшої стабільності")
        
        # Рекомендації по бюджету
        budget = components.get("budget", {})
        if budget.get("score", 0) < 60:
            recommendations.append("🎯 Встановіть реалістичний бюджет та дотримуйтесь його")
        
        # Рекомендації по доходах
        income = components.get("income", {})
        if income.get("score", 0) < 60:
            recommendations.append("💼 Розгляньте можливість додаткових джерел доходу")
        
        return recommendations
    
    def generate_spending_insights(self, transactions: List[Dict], period_days: int = 30) -> List[str]:
        """Генерує персоналізовані інсайти про витрати"""
        try:
            insights = []
            
            # Підготовка даних
            now = datetime.now()
            start_date = now - timedelta(days=period_days)
            
            recent_transactions = [
                t for t in transactions 
                if t['transaction_date'] >= start_date and t['type'] == 'expense'
            ]
            
            if not recent_transactions:
                return ["Немає даних про витрати за вказаний період"]
            
            # Аналіз категорій
            category_analysis = self._analyze_categories(recent_transactions)
            insights.extend(category_analysis)
            
            # Аналіз часових паттернів
            time_analysis = self._analyze_time_patterns(recent_transactions)
            insights.extend(time_analysis)
            
            # Аналіз сум
            amount_analysis = self._analyze_amounts(recent_transactions)
            insights.extend(amount_analysis)
            
            # Порівняння з попереднім періодом
            comparison_insights = self._compare_periods(transactions, period_days)
            insights.extend(comparison_insights)
            
            return insights[:8]  # Обмежуємо кількість інсайтів
            
        except Exception as e:
            logger.error(f"Error generating spending insights: {e}")
            return ["Помилка генерації інсайтів"]
    
    def _analyze_categories(self, transactions: List[Dict]) -> List[str]:
        """Аналізує витрати по категоріях"""
        insights = []
        
        # Підраховуємо суми по категоріях
        category_totals = defaultdict(float)
        for t in transactions:
            category = t.get('category_name', 'Без категорії')
            category_totals[category] += t['amount']
        
        if not category_totals:
            return []
        
        # Знаходимо топ категорію
        top_category = max(category_totals.items(), key=lambda x: x[1])
        total_expenses = sum(category_totals.values())
        top_percentage = (top_category[1] / total_expenses) * 100
        
        insights.append(f"🏆 Найбільша категорія витрат: {top_category[0]} ({top_percentage:.1f}%)")
        
        # Знаходимо категорії з великим відсотком
        if top_percentage > 40:
            insights.append(f"⚠️ {top_category[0]} займає {top_percentage:.1f}% всіх витрат - варто диверсифікувати")
        
        return insights
    
    def _analyze_time_patterns(self, transactions: List[Dict]) -> List[str]:
        """Аналізує часові паттерни витрат"""
        insights = []
        
        # Аналіз по днях тижня
        weekday_totals = defaultdict(float)
        for t in transactions:
            weekday = t['transaction_date'].weekday()
            weekday_totals[weekday] += t['amount']
        
        if weekday_totals:
            max_weekday = max(weekday_totals.items(), key=lambda x: x[1])
            weekday_names = ['понеділок', 'вівторок', 'середу', 'четвер', "п'ятницю", 'суботу', 'неділю']
            
            insights.append(f"📅 Найбільше витрачаєте в {weekday_names[max_weekday[0]]}")
        
        # Аналіз вихідних vs робочих днів
        weekend_total = weekday_totals.get(5, 0) + weekday_totals.get(6, 0)
        weekday_total = sum(weekday_totals[i] for i in range(5))
        
        if weekend_total > 0 and weekday_total > 0:
            if weekend_total > weekday_total * 0.4:  # Вихідні > 40% від робочих днів
                insights.append("🎉 Ви активно витрачаєте на вихідних")
        
        return insights
    
    def _analyze_amounts(self, transactions: List[Dict]) -> List[str]:
        """Аналізує суми транзакцій"""
        insights = []
        
        amounts = [t['amount'] for t in transactions]
        if not amounts:
            return []
        
        avg_amount = np.mean(amounts)
        median_amount = np.median(amounts)
        max_amount = max(amounts)
        
        # Аналіз великих витрат
        large_expenses = [a for a in amounts if a > avg_amount * 2]
        if large_expenses:
            insights.append(f"💸 {len(large_expenses)} великих витрат (>{avg_amount*2:.0f} грн)")
        
        # Аналіз середньої суми
        insights.append(f"📊 Середня витрата: {avg_amount:.2f} грн")
        
        return insights
    
    def _compare_periods(self, transactions: List[Dict], period_days: int) -> List[str]:
        """Порівнює поточний період з попереднім"""
        insights = []
        
        try:
            now = datetime.now()
            current_start = now - timedelta(days=period_days)
            prev_start = now - timedelta(days=period_days * 2)
            prev_end = current_start
            
            # Поточний період
            current_expenses = [
                t for t in transactions 
                if current_start <= t['transaction_date'] <= now and t['type'] == 'expense'
            ]
            
            # Попередній період
            prev_expenses = [
                t for t in transactions 
                if prev_start <= t['transaction_date'] <= prev_end and t['type'] == 'expense'
            ]
            
            if current_expenses and prev_expenses:
                current_total = sum(t['amount'] for t in current_expenses)
                prev_total = sum(t['amount'] for t in prev_expenses)
                
                change_percent = ((current_total - prev_total) / prev_total) * 100 if prev_total > 0 else 0
                
                if abs(change_percent) > 10:
                    if change_percent > 0:
                        insights.append(f"📈 Витрати зросли на {change_percent:.1f}% порівняно з попереднім періодом")
                    else:
                        insights.append(f"📉 Витрати зменшились на {abs(change_percent):.1f}% порівняно з попереднім періодом")
        
        except Exception as e:
            logger.error(f"Error comparing periods: {e}")
        
        return insights
    
    def generate_savings_goals(self, user_data: Dict) -> List[Dict]:
        """Генерує рекомендації по цілях заощаджень"""
        try:
            monthly_income = user_data.get("monthly_income", 0)
            monthly_expenses = user_data.get("monthly_expenses", 0)
            current_savings = monthly_income - monthly_expenses
            
            goals = []
            
            if monthly_income > 0:
                # Екстрений фонд
                emergency_fund = monthly_expenses * 6
                goals.append({
                    "title": "🚨 Екстрений фонд",
                    "target_amount": emergency_fund,
                    "monthly_target": emergency_fund / 12,
                    "description": "6-місячний запас на непередбачені витрати",
                    "priority": "high"
                })
                
                # Щорічна відпустка
                vacation_fund = monthly_income * 0.1 * 12
                goals.append({
                    "title": "🌴 Фонд відпустки",
                    "target_amount": vacation_fund,
                    "monthly_target": vacation_fund / 12,
                    "description": "10% річного доходу на відпочинок",
                    "priority": "medium"
                })
                
                # Великі покупки
                big_purchase = monthly_income * 2
                goals.append({
                    "title": "🛍️ Великі покупки",
                    "target_amount": big_purchase,
                    "monthly_target": big_purchase / 6,
                    "description": "Накопичення на техніку, меблі тощо",
                    "priority": "low"
                })
            
            return goals
            
        except Exception as e:
            logger.error(f"Error generating savings goals: {e}")
            return []

# Глобальний екземпляр
insights_engine = FinancialInsightsEngine()
