"""
Модуль для аналізу фінансових тенденцій та прогнозування.
Включає аналіз паттернів, сезонності та простих прогнозів.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging
from collections import defaultdict
from scipy import stats
import matplotlib.pyplot as plt
import io

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    """Клас для аналізу фінансових тенденцій та паттернів"""
    
    def __init__(self):
        self.min_data_points = 7  # Мінімум точок для аналізу
    
    def analyze_spending_trends(self, transactions: List[Dict]) -> Dict:
        """Аналізує тенденції витрат користувача"""
        try:
            # Підготовка даних
            df = pd.DataFrame([
                {
                    'date': t['transaction_date'],
                    'amount': t['amount'],
                    'type': t['type'],
                    'category': t.get('category_name', 'Без категорії')
                }
                for t in transactions
            ])
            
            if df.empty:
                return {"error": "Немає даних для аналізу"}
            
            # Фільтруємо витрати
            expenses_df = df[df['type'] == 'expense'].copy()
            
            if len(expenses_df) < self.min_data_points:
                return {"error": f"Потрібно мінімум {self.min_data_points} операцій для аналізу"}
            
            # Групуємо по датах
            daily_expenses = expenses_df.groupby(expenses_df['date'].dt.date)['amount'].sum()
            
            # Розраховуємо тренди
            trend_analysis = self._calculate_trend(daily_expenses)
            
            # Аналіз по категоріях
            category_trends = self._analyze_category_trends(expenses_df)
            
            # Аналіз сезонності
            seasonality = self._analyze_seasonality(expenses_df)
            
            # Виявлення аномалій
            anomalies = self._detect_spending_anomalies(daily_expenses)
            
            # Прогноз на наступний місяць
            forecast = self._simple_forecast(daily_expenses)
            
            return {
                "overall_trend": trend_analysis,
                "category_trends": category_trends,
                "seasonality": seasonality,
                "anomalies": anomalies,
                "forecast": forecast
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_spending_trends: {e}")
            return {"error": f"Помилка аналізу: {str(e)}"}
    
    def _calculate_trend(self, daily_data: pd.Series) -> Dict:
        """Розраховує загальний тренд витрат"""
        try:
            # Конвертуємо дати в числовий формат для регресії
            x = np.arange(len(daily_data))
            y = daily_data.values
            
            # Лінійна регресія
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Інтерпретація тренду
            if abs(slope) < 1:  # Менше 1 грн на день
                trend_direction = "стабільний"
                trend_strength = "слабкий"
            elif slope > 5:
                trend_direction = "зростаючий"
                trend_strength = "сильний"
            elif slope > 1:
                trend_direction = "зростаючий"
                trend_strength = "помірний"
            elif slope < -5:
                trend_direction = "спадний"
                trend_strength = "сильний"
            elif slope < -1:
                trend_direction = "спадний"
                trend_strength = "помірний"
            else:
                trend_direction = "стабільний"
                trend_strength = "слабкий"
            
            # Середні показники
            avg_daily = daily_data.mean()
            avg_weekly = avg_daily * 7
            avg_monthly = avg_daily * 30
            
            return {
                "direction": trend_direction,
                "strength": trend_strength,
                "slope": slope,
                "confidence": abs(r_value),
                "avg_daily": avg_daily,
                "avg_weekly": avg_weekly,
                "avg_monthly": avg_monthly,
                "growth_per_day": slope
            }
            
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return {"error": "Помилка розрахунку тренду"}
    
    def _analyze_category_trends(self, expenses_df: pd.DataFrame) -> Dict:
        """Аналізує тренди по категоріях"""
        try:
            category_trends = {}
            
            for category in expenses_df['category'].unique():
                cat_data = expenses_df[expenses_df['category'] == category]
                
                if len(cat_data) < 3:  # Мінімум для аналізу категорії
                    continue
                
                # Групуємо по тижнях для більш стабільного аналізу
                cat_data['week'] = cat_data['date'].dt.isocalendar().week
                weekly_amounts = cat_data.groupby('week')['amount'].sum()
                
                if len(weekly_amounts) >= 2:
                    # Простий аналіз: порівняння першої та другої половини
                    mid_point = len(weekly_amounts) // 2
                    first_half = weekly_amounts.iloc[:mid_point].mean()
                    second_half = weekly_amounts.iloc[mid_point:].mean()
                    
                    change_percent = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
                    
                    if change_percent > 20:
                        trend = "сильно зростає"
                    elif change_percent > 5:
                        trend = "зростає"
                    elif change_percent < -20:
                        trend = "сильно спадає"
                    elif change_percent < -5:
                        trend = "спадає"
                    else:
                        trend = "стабільний"
                    
                    category_trends[category] = {
                        "trend": trend,
                        "change_percent": change_percent,
                        "avg_amount": cat_data['amount'].mean(),
                        "total_amount": cat_data['amount'].sum(),
                        "transaction_count": len(cat_data)
                    }
            
            return category_trends
            
        except Exception as e:
            logger.error(f"Error analyzing category trends: {e}")
            return {}
    
    def _analyze_seasonality(self, expenses_df: pd.DataFrame) -> Dict:
        """Аналізує сезонні паттерни витрат"""
        try:
            seasonality = {}
            
            # Аналіз по днях тижня
            weekday_analysis = expenses_df.groupby(expenses_df['date'].dt.dayofweek)['amount'].agg(['mean', 'sum', 'count'])
            weekday_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
            
            max_weekday = weekday_analysis['mean'].idxmax()
            min_weekday = weekday_analysis['mean'].idxmin()
            
            seasonality['weekday'] = {
                "most_expensive_day": weekday_names[max_weekday],
                "cheapest_day": weekday_names[min_weekday],
                "weekend_vs_weekday": {
                    "weekend_avg": weekday_analysis.loc[[5, 6], 'mean'].mean(),
                    "weekday_avg": weekday_analysis.loc[range(5), 'mean'].mean()
                }
            }
            
            # Аналіз по годинах (якщо є достатньо даних)
            if len(expenses_df) > 20:
                hour_analysis = expenses_df.groupby(expenses_df['date'].dt.hour)['amount'].agg(['mean', 'count'])
                
                # Знаходимо найбільш активні години
                if len(hour_analysis) > 0:
                    peak_hour = hour_analysis['mean'].idxmax()
                    seasonality['hourly'] = {
                        "peak_spending_hour": f"{peak_hour}:00",
                        "morning_avg": hour_analysis.loc[range(6, 12), 'mean'].mean() if any(h in hour_analysis.index for h in range(6, 12)) else 0,
                        "evening_avg": hour_analysis.loc[range(18, 23), 'mean'].mean() if any(h in hour_analysis.index for h in range(18, 23)) else 0
                    }
            
            return seasonality
            
        except Exception as e:
            logger.error(f"Error analyzing seasonality: {e}")
            return {}
    
    def _detect_spending_anomalies(self, daily_expenses: pd.Series) -> List[Dict]:
        """Виявляє аномальні витрати"""
        try:
            if len(daily_expenses) < 7:
                return []
            
            # Використовуємо IQR метод для виявлення викидів
            Q1 = daily_expenses.quantile(0.25)
            Q3 = daily_expenses.quantile(0.75)
            IQR = Q3 - Q1
            
            # Визначаємо межі для аномалій
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            anomalies = []
            
            for date, amount in daily_expenses.items():
                if amount > upper_bound:
                    anomalies.append({
                        "date": date.strftime("%d.%m.%Y"),
                        "amount": amount,
                        "type": "висока_витрата",
                        "description": f"Витрати {amount:.2f} грн перевищують звичайний рівень ({upper_bound:.2f} грн)"
                    })
                elif amount < lower_bound and amount > 0:
                    anomalies.append({
                        "date": date.strftime("%d.%m.%Y"),
                        "amount": amount,
                        "type": "низька_витрата",
                        "description": f"Незвично низькі витрати {amount:.2f} грн"
                    })
            
            # Сортуємо за датою
            anomalies.sort(key=lambda x: x['date'])
            
            return anomalies[:10]  # Повертаємо останні 10 аномалій
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []
    
    def _simple_forecast(self, daily_expenses: pd.Series) -> Dict:
        """Створює простий прогноз витрат на наступний місяць"""
        try:
            if len(daily_expenses) < 14:
                return {"error": "Недостатньо даних для прогнозу"}
            
            # Беремо останні 14 днів для прогнозу
            recent_data = daily_expenses.tail(14)
            
            # Простий прогноз на основі середнього
            daily_avg = recent_data.mean()
            
            # Враховуємо тренд
            x = np.arange(len(recent_data))
            y = recent_data.values
            slope, intercept, _, _, _ = stats.linregress(x, y)
            
            # Прогноз на 30 днів
            forecast_days = 30
            projected_daily = daily_avg + (slope * forecast_days / 2)  # Середній тренд
            
            monthly_forecast = projected_daily * 30
            weekly_forecast = projected_daily * 7
            
            # Довірчий інтервал (простий розрахунок)
            std_dev = recent_data.std()
            confidence_margin = std_dev * 1.96  # 95% довірчий інтервал
            
            return {
                "daily_forecast": projected_daily,
                "weekly_forecast": weekly_forecast,
                "monthly_forecast": monthly_forecast,
                "confidence_interval": {
                    "lower": monthly_forecast - confidence_margin * 30,
                    "upper": monthly_forecast + confidence_margin * 30
                },
                "based_on_days": len(recent_data),
                "current_trend": "зростаючий" if slope > 0 else "спадний" if slope < 0 else "стабільний"
            }
            
        except Exception as e:
            logger.error(f"Error in simple forecast: {e}")
            return {"error": f"Помилка прогнозування: {str(e)}"}
    
    def get_spending_insights(self, transactions: List[Dict]) -> List[str]:
        """Генерує корисні інсайти про витрати користувача"""
        try:
            insights = []
            
            # Аналізуємо тренди
            trend_data = self.analyze_spending_trends(transactions)
            
            if "error" in trend_data:
                return ["Недостатньо даних для аналізу паттернів витрат"]
            
            # Інсайти про загальний тренд
            overall_trend = trend_data.get("overall_trend", {})
            if overall_trend.get("direction") == "зростаючий":
                insights.append(f"📈 Ваші витрати зростають на {overall_trend.get('growth_per_day', 0):.2f} грн/день")
            elif overall_trend.get("direction") == "спадний":
                insights.append(f"📉 Ваші витрати зменшуються на {abs(overall_trend.get('growth_per_day', 0)):.2f} грн/день")
            else:
                insights.append("📊 Ваші витрати стабільні")
            
            # Інсайти про категорії
            category_trends = trend_data.get("category_trends", {})
            growing_categories = [cat for cat, data in category_trends.items() 
                                if data.get("trend") in ["зростає", "сильно зростає"]]
            
            if growing_categories:
                insights.append(f"⚠️ Зростаючі витрати в категоріях: {', '.join(growing_categories[:3])}")
            
            # Інсайти про сезонність
            seasonality = trend_data.get("seasonality", {})
            weekday_data = seasonality.get("weekday", {})
            if weekday_data:
                most_expensive = weekday_data.get("most_expensive_day")
                if most_expensive:
                    insights.append(f"💰 Найбільше витрачаєте в {most_expensive}")
            
            # Інсайти про аномалії
            anomalies = trend_data.get("anomalies", [])
            if anomalies:
                high_spending_days = [a for a in anomalies if a.get("type") == "висока_витрата"]
                if high_spending_days:
                    insights.append(f"🔍 Виявлено {len(high_spending_days)} днів з підвищеними витратами")
            
            # Прогноз
            forecast = trend_data.get("forecast", {})
            if "monthly_forecast" in forecast:
                monthly_proj = forecast["monthly_forecast"]
                insights.append(f"🔮 Прогноз витрат на місяць: {monthly_proj:.2f} грн")
            
            return insights[:5]  # Повертаємо максимум 5 інсайтів
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return ["Помилка генерації інсайтів"]

# Глобальний екземпляр
trend_analyzer = TrendAnalyzer()
