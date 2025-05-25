import logging
from datetime import datetime, date, timedelta
import calendar
from database.models import Session, BudgetPlan, CategoryBudget, Transaction, Category, User
from database.db_operations import create_or_update_budget, get_user_categories, get_transactions
from sqlalchemy import func

logger = logging.getLogger(__name__)

class BudgetManager:
    """Клас для управління бюджетами користувача"""
    
    def __init__(self, user_id):
        self.user_id = user_id
    
    def get_active_budget(self):
        """Отримує активний бюджет користувача (що включає поточну дату)"""
        session = Session()
        today = datetime.utcnow().date()
        
        budget = session.query(BudgetPlan) \
            .filter(BudgetPlan.user_id == self.user_id,
                    BudgetPlan.start_date <= today,
                    BudgetPlan.end_date >= today) \
            .order_by(BudgetPlan.created_at.desc()) \
            .first()
        
        if budget:
            # Завантажуємо бюджети по категоріям
            category_budgets = session.query(CategoryBudget, Category.name, Category.icon) \
                .join(Category, CategoryBudget.category_id == Category.id) \
                .filter(CategoryBudget.budget_plan_id == budget.id) \
                .all()
                
            # Обчислюємо фактичні витрати по категоріям
            result = {
                'budget': budget,
                'category_budgets': []
            }
            
            for cat_budget, cat_name, cat_icon in category_budgets:
                # Отримуємо суму фактичних витрат по категорії
                actual_spending = session.query(func.sum(Transaction.amount)) \
                    .filter(Transaction.user_id == self.user_id,
                            Transaction.category_id == cat_budget.category_id,
                            Transaction.transaction_date >= budget.start_date,
                            Transaction.transaction_date <= budget.end_date,
                            Transaction.type == 'expense') \
                    .scalar() or 0
                
                # Розраховуємо відсоток використання бюджету
                if cat_budget.allocated_amount > 0:
                    usage_percent = (actual_spending / cat_budget.allocated_amount) * 100
                else:
                    usage_percent = 0
                
                result['category_budgets'].append({
                    'id': cat_budget.id,
                    'category_id': cat_budget.category_id,
                    'category_name': cat_name,
                    'category_icon': cat_icon,
                    'allocated_amount': cat_budget.allocated_amount,
                    'actual_spending': actual_spending,
                    'remaining': cat_budget.allocated_amount - actual_spending,
                    'usage_percent': usage_percent
                })
                
            # Обчислюємо загальні витрати
            total_spending = session.query(func.sum(Transaction.amount)) \
                .filter(Transaction.user_id == self.user_id,
                        Transaction.transaction_date >= budget.start_date,
                        Transaction.transaction_date <= budget.end_date,
                        Transaction.type == 'expense') \
                .scalar() or 0
                
            result['total_spending'] = total_spending
            result['total_remaining'] = budget.total_budget - total_spending
            result['usage_percent'] = (total_spending / budget.total_budget) * 100 if budget.total_budget > 0 else 0
            
            session.close()
            return result
        else:
            session.close()
            return None
    
    def get_all_budgets(self):
        """Отримує всі бюджети користувача"""
        session = Session()
        
        budgets = session.query(BudgetPlan) \
            .filter(BudgetPlan.user_id == self.user_id) \
            .order_by(BudgetPlan.start_date.desc()) \
            .all()
            
        session.close()
        return budgets
    
    def create_monthly_budget(self, name, total_budget, year=None, month=None, category_allocations=None):
        """Створює місячний бюджет"""
        if not year or not month:
            today = datetime.utcnow()
            year = today.year
            month = today.month
        
        # Визначаємо перший і останній день місяця
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        # Формуємо категорії для бюджету
        category_budgets = []
        
        if category_allocations:
            category_budgets = [
                {'category_id': cat_id, 'amount': amount}
                for cat_id, amount in category_allocations.items()
            ]
        
        # Створюємо або оновлюємо бюджет
        budget = create_or_update_budget(
            user_id=self.user_id,
            name=name,
            total_budget=total_budget,
            start_date=first_day,
            end_date=last_day,
            category_budgets=category_budgets
        )
        
        return budget
    
    def update_category_budget(self, budget_id, category_id, new_amount):
        """Оновлює бюджет для конкретної категорії"""
        session = Session()
        
        category_budget = session.query(CategoryBudget) \
            .join(BudgetPlan, CategoryBudget.budget_plan_id == BudgetPlan.id) \
            .filter(BudgetPlan.id == budget_id,
                    CategoryBudget.category_id == category_id,
                    BudgetPlan.user_id == self.user_id) \
            .first()
        
        if category_budget:
            category_budget.allocated_amount = new_amount
            session.commit()
            session.close()
            return True
        else:
            session.close()
            return False
    
    def get_previous_period_comparison(self):
        """Отримує порівняння з попереднім періодом"""
        active_budget = self.get_active_budget()
        if not active_budget:
            return None
            
        session = Session()
        
        # Визначаємо попередній період (місяць)
        current_budget = active_budget['budget']
        current_start = current_budget.start_date
        current_end = current_budget.end_date
        
        # Розраховуємо попередній період
        if current_start.month == 1:
            prev_year = current_start.year - 1
            prev_month = 12
        else:
            prev_year = current_start.year
            prev_month = current_start.month - 1
            
        prev_start = date(prev_year, prev_month, 1)
        prev_end = date(prev_year, prev_month, calendar.monthrange(prev_year, prev_month)[1])
        
        # Отримуємо витрати поточного періоду
        current_expenses = session.query(
            Transaction.category_id,
            Category.name,
            Category.icon,
            func.sum(Transaction.amount).label('amount')
        ).join(Category, Transaction.category_id == Category.id) \
         .filter(Transaction.user_id == self.user_id,
                Transaction.type == 'expense',
                Transaction.transaction_date >= current_start,
                Transaction.transaction_date <= current_end) \
         .group_by(Transaction.category_id, Category.name, Category.icon) \
         .all()
         
        # Отримуємо витрати попереднього періоду
        previous_expenses = session.query(
            Transaction.category_id,
            Category.name,
            Category.icon,
            func.sum(Transaction.amount).label('amount')
        ).join(Category, Transaction.category_id == Category.id) \
         .filter(Transaction.user_id == self.user_id,
                Transaction.type == 'expense',
                Transaction.transaction_date >= prev_start,
                Transaction.transaction_date <= prev_end) \
         .group_by(Transaction.category_id, Category.name, Category.icon) \
         .all()
         
        # Створюємо словники для зручного порівняння
        current_dict = {expense.category_id: expense.amount for expense in current_expenses}
        previous_dict = {expense.category_id: expense.amount for expense in previous_expenses}
        
        # Загальні суми
        current_total = sum(current_dict.values())
        previous_total = sum(previous_dict.values())
        
        # Розраховуємо зміни
        total_change = current_total - previous_total
        total_change_percent = ((current_total - previous_total) / previous_total * 100) if previous_total > 0 else 0
        
        # Порівняння по категоріям
        category_comparisons = []
        all_categories = set(current_dict.keys()) | set(previous_dict.keys())
        
        for category_id in all_categories:
            current_amount = current_dict.get(category_id, 0)
            previous_amount = previous_dict.get(category_id, 0)
            
            # Знаходимо назву та іконку категорії
            category_info = session.query(Category.name, Category.icon) \
                .filter(Category.id == category_id).first()
                
            if category_info:
                change = current_amount - previous_amount
                change_percent = ((current_amount - previous_amount) / previous_amount * 100) if previous_amount > 0 else 0
                
                category_comparisons.append({
                    'category_id': category_id,
                    'name': category_info.name,
                    'icon': category_info.icon,
                    'current_amount': current_amount,
                    'previous_amount': previous_amount,
                    'change': change,
                    'change_percent': change_percent
                })
        
        session.close()
        
        return {
            'current_period': {
                'start': current_start,
                'end': current_end,
                'total': current_total
            },
            'previous_period': {
                'start': prev_start,
                'end': prev_end,
                'total': previous_total
            },
            'total_change': total_change,
            'total_change_percent': total_change_percent,
            'category_comparisons': category_comparisons
        }
    
    def get_user_financial_status(self):
        """Отримує поточний фінансовий стан користувача"""
        session = Session()
        
        # Отримуємо дані користувача
        user = session.query(User).filter(User.id == self.user_id).first()
        if not user:
            session.close()
            return None
            
        # Розраховуємо поточний баланс
        # Сума всіх доходів
        total_income = session.query(func.sum(Transaction.amount)) \
            .filter(Transaction.user_id == self.user_id,
                   Transaction.type == 'income') \
            .scalar() or 0
            
        # Сума всіх витрат
        total_expenses = session.query(func.sum(Transaction.amount)) \
            .filter(Transaction.user_id == self.user_id,
                   Transaction.type == 'expense') \
            .scalar() or 0
            
        # Поточний баланс = початковий баланс + доходи - витрати
        current_balance = (user.initial_balance or 0) + total_income - total_expenses
        
        # Отримуємо баланс по категоріях (тільки витрати за поточний місяць)
        today = datetime.utcnow()
        first_day = date(today.year, today.month, 1)
        last_day = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        
        category_balances = session.query(
            Category.id,
            Category.name,
            Category.icon,
            func.sum(Transaction.amount).label('spent_amount')
        ).join(Transaction, Category.id == Transaction.category_id) \
         .filter(Transaction.user_id == self.user_id,
                Transaction.type == 'expense',
                Transaction.transaction_date >= first_day,
                Transaction.transaction_date <= last_day) \
         .group_by(Category.id, Category.name, Category.icon) \
         .order_by(func.sum(Transaction.amount).desc()) \
         .all()
        
        session.close()
        
        return {
            'current_balance': current_balance,
            'initial_balance': user.initial_balance or 0,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'monthly_budget': user.monthly_budget,
            'category_balances': [
                {
                    'category_id': cat.id,
                    'name': cat.name,
                    'icon': cat.icon,
                    'spent_amount': cat.spent_amount
                }
                for cat in category_balances
            ]
        }

    def get_budget_status(self):
        """Отримує статус бюджету"""
        active_budget = self.get_active_budget()
        
        # Отримуємо фінансовий стан користувача
        financial_status = self.get_user_financial_status()
        
        if not active_budget:
            return {
                'status': 'no_active_budget',
                'message': 'У вас немає активного бюджету',
                'financial_status': financial_status
            }
        
        # Перевіряємо перевитрати
        if active_budget['total_remaining'] < 0:
            return {
                'status': 'over_budget',
                'message': f'Перевищення бюджету на {abs(active_budget["total_remaining"]):.2f} грн',
                'data': active_budget,
                'financial_status': financial_status
            }
        
        # Перевіряємо витрати по категоріям
        problematic_categories = []
        for cat_budget in active_budget['category_budgets']:
            if cat_budget['usage_percent'] > 90:  # Якщо використано більше 90% бюджету
                problematic_categories.append({
                    'name': cat_budget['category_name'],
                    'icon': cat_budget['category_icon'],
                    'used_percent': cat_budget['usage_percent']
                })
        
        if problematic_categories:
            return {
                'status': 'warning',
                'message': 'Деякі категорії близькі до перевищення бюджету',
                'problematic_categories': problematic_categories,
                'data': active_budget,
                'financial_status': financial_status
            }
        
        return {
            'status': 'ok',
            'message': 'Бюджет в нормі',
            'data': active_budget,
            'financial_status': financial_status
        }
    
    def get_comprehensive_budget_status(self):
        """
        Основна функція для отримання повного стану бюджету
        Повертає всю інформацію необхідну для вкладки "Мій бюджет"
        """
        session = Session()
        
        # Отримуємо користувача
        user = session.query(User).filter(User.id == self.user_id).first()
        if not user:
            session.close()
            return None
        
        # Поточний період (місяць)
        today = datetime.utcnow()
        current_month_start = date(today.year, today.month, 1)
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        current_month_end = date(today.year, today.month, days_in_month)
        
        # Дні що залишились до кінця місяця
        days_remaining = (current_month_end - today.date()).days + 1
        days_passed = (today.date() - current_month_start).days + 1
        
        # Отримуємо активний бюджет
        active_budget = self.get_active_budget()
        
        # Обчислюємо доходи за поточний місяць
        monthly_income = session.query(func.sum(Transaction.amount)) \
            .filter(Transaction.user_id == self.user_id,
                   Transaction.type == 'income',
                   Transaction.transaction_date >= current_month_start,
                   Transaction.transaction_date <= current_month_end) \
            .scalar() or 0
        
        # Обчислюємо витрати за поточний місяць
        monthly_expenses = session.query(func.sum(Transaction.amount)) \
            .filter(Transaction.user_id == self.user_id,
                   Transaction.type == 'expense',
                   Transaction.transaction_date >= current_month_start,
                   Transaction.transaction_date <= current_month_end) \
            .scalar() or 0
        
        # Загальний баланс користувача
        total_income = session.query(func.sum(Transaction.amount)) \
            .filter(Transaction.user_id == self.user_id,
                   Transaction.type == 'income') \
            .scalar() or 0
            
        total_expenses = session.query(func.sum(Transaction.amount)) \
            .filter(Transaction.user_id == self.user_id,
                   Transaction.type == 'expense') \
            .scalar() or 0
            
        current_balance = (user.initial_balance or 0) + total_income - total_expenses
        
        # Залишок до кінця місяця
        budget_total = user.monthly_budget or (active_budget['budget'].total_budget if active_budget else 0)
        remaining_budget = budget_total - monthly_expenses
        
        # Прогрес використання бюджету
        if budget_total > 0:
            budget_usage_percent = (monthly_expenses / budget_total) * 100
        else:
            budget_usage_percent = 0
        
        # Рекомендований денний ліміт (що залишився)
        if days_remaining > 0 and remaining_budget > 0:
            recommended_daily_limit = remaining_budget / days_remaining
        else:
            recommended_daily_limit = 0
        
        # Середні витрати за день поточного місяця
        if days_passed > 0:
            average_daily_spending = monthly_expenses / days_passed
        else:
            average_daily_spending = 0
        
        # Прогноз витрат до кінця місяця
        projected_monthly_expenses = average_daily_spending * days_in_month
        
        session.close()
        
        return {
            # 1. Поточний стан бюджету
            'current_status': {
                'current_balance': current_balance,
                'monthly_income': monthly_income,
                'monthly_expenses': monthly_expenses,
                'remaining_budget': remaining_budget
            },
            
            # 2. Встановлення лімітів
            'budget_limits': {
                'total_monthly_budget': budget_total,
                'category_budgets': active_budget['category_budgets'] if active_budget else [],
                'recommended_daily_limit': recommended_daily_limit,
                'current_daily_limit': budget_total / days_in_month if budget_total > 0 else 0
            },
            
            # 3. Прогрес бюджету
            'budget_progress': {
                'usage_percent': budget_usage_percent,
                'days_remaining': days_remaining,
                'days_passed': days_passed,
                'days_in_month': days_in_month,
                'average_daily_spending': average_daily_spending,
                'projected_monthly_expenses': projected_monthly_expenses,
                'on_track': projected_monthly_expenses <= budget_total if budget_total > 0 else True
            },
            
            # Додаткова інформація
            'user_info': {
                'currency': user.currency,
                'has_active_budget': active_budget is not None,
                'budget_plan_id': active_budget['budget'].id if active_budget else None
            },
            
            # Активний бюджет (якщо є)
            'active_budget': active_budget
        }
    
    def set_daily_spending_limit(self, daily_limit):
        """Встановлює денний ліміт витрат для користувача"""
        session = Session()
        
        user = session.query(User).filter(User.id == self.user_id).first()
        if user:
            # Обчислюємо місячний бюджет на основі денного ліміту
            today = datetime.utcnow()
            days_in_month = calendar.monthrange(today.year, today.month)[1]
            monthly_budget = daily_limit * days_in_month
            
            user.monthly_budget = monthly_budget
            session.commit()
            session.close()
            return True
        
        session.close()
        return False
    
    def get_daily_spending_stats(self, days_count=7):
        """Отримує статистику витрат за останні N днів"""
        session = Session()
        
        today = datetime.utcnow().date()
        start_date = today - timedelta(days=days_count-1)
        
        # Отримуємо витрати по днях
        daily_expenses = session.query(
            func.date(Transaction.transaction_date).label('date'),
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.user_id == self.user_id,
            Transaction.type == 'expense',
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= today
        ).group_by(func.date(Transaction.transaction_date)) \
         .order_by(func.date(Transaction.transaction_date)) \
         .all()
        
        session.close()
        
        # Формуємо результат з заповненням пропущених днів
        result = []
        current_date = start_date
        expenses_dict = {expense.date: expense.total_amount for expense in daily_expenses}
        
        while current_date <= today:
            result.append({
                'date': current_date,
                'amount': expenses_dict.get(current_date, 0)
            })
            current_date += timedelta(days=1)
        
        return result
    
    def reset_monthly_budget(self, confirm=False):
        """Скидає поточний місячний бюджет"""
        if not confirm:
            return {'status': 'confirmation_required', 'message': 'Потрібне підтвердження для скидання бюджету'}
        
        session = Session()
        
        # Скидаємо місячний бюджет у користувача
        user = session.query(User).filter(User.id == self.user_id).first()
        if user:
            user.monthly_budget = None
            
        # Деактивуємо поточні бюджетні плани
        today = datetime.utcnow().date()
        active_budgets = session.query(BudgetPlan) \
            .filter(BudgetPlan.user_id == self.user_id,
                    BudgetPlan.start_date <= today,
                    BudgetPlan.end_date >= today) \
            .all()
        
        for budget in active_budgets:
            budget.end_date = today - timedelta(days=1)  # Завершуємо вчора
        
        session.commit()
        session.close()
        
        return {'status': 'success', 'message': 'Бюджет успішно скинуто'}
    
    def create_smart_monthly_budget(self, total_budget, distribution_strategy='balanced'):
        """
        Створює розумний місячний бюджет з автоматичним розподілом по категоріях
        
        Args:
            total_budget: Загальна сума бюджету
            distribution_strategy: Стратегія розподілу ('balanced', 'historical', 'conservative')
        """
        session = Session()
        
        # Отримуємо категорії користувача
        categories = session.query(Category).filter(
            Category.user_id == self.user_id,
            Category.type == 'expense'
        ).all()
        
        if not categories:
            session.close()
            return None
        
        category_allocations = {}
        
        if distribution_strategy == 'historical':
            # Розподіл на основі історичних витрат
            prev_month_stats = self._get_previous_month_spending()
            total_prev_spending = sum(prev_month_stats.values())
            
            if total_prev_spending > 0:
                for category in categories:
                    historical_amount = prev_month_stats.get(category.id, 0)
                    percentage = historical_amount / total_prev_spending
                    category_allocations[category.id] = total_budget * percentage
            else:
                # Якщо немає історії, використовуємо рівномірний розподіл
                amount_per_category = total_budget / len(categories)
                for category in categories:
                    category_allocations[category.id] = amount_per_category
                    
        elif distribution_strategy == 'conservative':
            # Консервативний розподіл: більше на основні потреби
            essential_categories = ['Продукти', 'Житло', 'Транспорт', 'Комунальні послуги']
            essential_percent = 0.7  # 70% на основні потреби
            other_percent = 0.3     # 30% на інше
            
            essential_cats = [cat for cat in categories if cat.name in essential_categories]
            other_cats = [cat for cat in categories if cat.name not in essential_categories]
            
            if essential_cats:
                essential_budget = total_budget * essential_percent
                amount_per_essential = essential_budget / len(essential_cats)
                for cat in essential_cats:
                    category_allocations[cat.id] = amount_per_essential
            
            if other_cats:
                other_budget = total_budget * other_percent
                amount_per_other = other_budget / len(other_cats)
                for cat in other_cats:
                    category_allocations[cat.id] = amount_per_other
                    
        else:  # balanced (default)
            # Рівномірний розподіл
            amount_per_category = total_budget / len(categories)
            for category in categories:
                category_allocations[category.id] = amount_per_category
        
        session.close()
        
        # Створюємо бюджет
        today = datetime.utcnow()
        budget_name = f"Бюджет {today.strftime('%m/%Y')}"
        
        return self.create_monthly_budget(
            name=budget_name,
            total_budget=total_budget,
            category_allocations=category_allocations
        )
    
    def _get_previous_month_spending(self):
        """Допоміжний метод для отримання витрат за попередній місяць"""
        session = Session()
        
        today = datetime.utcnow()
        if today.month == 1:
            prev_year = today.year - 1
            prev_month = 12
        else:
            prev_year = today.year
            prev_month = today.month - 1
        
        prev_start = date(prev_year, prev_month, 1)
        prev_end = date(prev_year, prev_month, calendar.monthrange(prev_year, prev_month)[1])
        
        spending_by_category = session.query(
            Transaction.category_id,
            func.sum(Transaction.amount).label('amount')
        ).filter(
            Transaction.user_id == self.user_id,
            Transaction.type == 'expense',
            Transaction.transaction_date >= prev_start,
            Transaction.transaction_date <= prev_end
        ).group_by(Transaction.category_id).all()
        
        session.close()
        
        return {spending.category_id: spending.amount for spending in spending_by_category}
    
    def get_budget_recommendations(self):
        """Генерує рекомендації щодо бюджету на основі аналізу витрат"""
        comprehensive_status = self.get_comprehensive_budget_status()
        if not comprehensive_status:
            return None
        
        recommendations = []
        progress = comprehensive_status['budget_progress']
        limits = comprehensive_status['budget_limits']
        
        # Аналіз перевитрат
        if progress['usage_percent'] > 100:
            recommendations.append({
                'type': 'warning',
                'title': 'Перевищення бюджету',
                'message': f'Ви перевищили місячний бюджет на {progress["usage_percent"] - 100:.1f}%',
                'action': 'Розгляньте можливість скорочення витрат або збільшення бюджету'
            })
        elif progress['usage_percent'] > 80 and progress['days_remaining'] > 7:
            recommendations.append({
                'type': 'caution',
                'title': 'Швидкі витрати',
                'message': 'Ви витрачаєте швидше, ніж планували',
                'action': f'Рекомендований денний ліміт: {limits["recommended_daily_limit"]:.2f} грн'
            })
        
        # Прогноз перевищення
        if not progress['on_track'] and progress['projected_monthly_expenses'] > limits['total_monthly_budget']:
            overspend = progress['projected_monthly_expenses'] - limits['total_monthly_budget']
            recommendations.append({
                'type': 'prediction',
                'title': 'Прогноз перевищення',
                'message': f'За поточним темпом ви перевищите бюджет на {overspend:.2f} грн',
                'action': 'Зменшіть середні денні витрати'
            })
        
        # Позитивні рекомендації
        if progress['usage_percent'] < 50 and progress['days_remaining'] < 10:
            remaining_budget = limits['total_monthly_budget'] - comprehensive_status['current_status']['monthly_expenses']
            recommendations.append({
                'type': 'positive',
                'title': 'Відмінне управління бюджетом!',
                'message': f'У вас залишилось {remaining_budget:.2f} грн до кінця місяця',
                'action': 'Ви можете дозволити собі додаткові витрати'
            })
        
        return recommendations
    
    def update_monthly_budget_total(self, new_budget):
        """Оновлює загальний місячний бюджет користувача"""
        session = Session()
        
        user = session.query(User).filter(User.id == self.user_id).first()
        if user:
            user.monthly_budget = new_budget
            
            # Оновлюємо також активний бюджетний план, якщо є
            today = datetime.utcnow().date()
            active_budget = session.query(BudgetPlan) \
                .filter(BudgetPlan.user_id == self.user_id,
                        BudgetPlan.start_date <= today,
                        BudgetPlan.end_date >= today) \
                .first()
            
            if active_budget:
                active_budget.total_budget = new_budget
            
            session.commit()
            session.close()
            return True
        
        session.close()
        return False
    
    def bulk_update_category_limits(self, category_limits):
        """
        Масове оновлення лімітів для категорій
        
        Args:
            category_limits: dict {category_id: amount}
        """
        session = Session()
        
        today = datetime.utcnow().date()
        active_budget = session.query(BudgetPlan) \
            .filter(BudgetPlan.user_id == self.user_id,
                    BudgetPlan.start_date <= today,
                    BudgetPlan.end_date >= today) \
            .first()
        
        if not active_budget:
            session.close()
            return False
        
        success_count = 0
        for category_id, amount in category_limits.items():
            category_budget = session.query(CategoryBudget) \
                .filter(CategoryBudget.budget_plan_id == active_budget.id,
                        CategoryBudget.category_id == category_id) \
                .first()
            
            if category_budget:
                category_budget.allocated_amount = amount
                success_count += 1
            else:
                # Створюємо новий запис, якщо не існує
                new_category_budget = CategoryBudget(
                    budget_plan_id=active_budget.id,
                    category_id=category_id,
                    allocated_amount=amount
                )
                session.add(new_category_budget)
                success_count += 1
        
        session.commit()
        session.close()
        
        return success_count
    
    def get_category_spending_alerts(self, alert_threshold=0.8):
        """
        Отримує оповіщення про наближення до лімітів категорій
        
        Args:
            alert_threshold: Поріг для оповіщення (0.8 = 80% використання)
        """
        active_budget = self.get_active_budget()
        if not active_budget:
            return []
        
        alerts = []
        for cat_budget in active_budget['category_budgets']:
            usage_percent = cat_budget['usage_percent'] / 100
            
            if usage_percent >= 1.0:  # Перевищення ліміту
                alerts.append({
                    'type': 'exceeded',
                    'category': cat_budget['category_name'],
                    'icon': cat_budget['category_icon'],
                    'usage_percent': cat_budget['usage_percent'],
                    'overspend': cat_budget['actual_spending'] - cat_budget['allocated_amount'],
                    'message': f"Перевищено ліміт категорії {cat_budget['category_name']} на {cat_budget['actual_spending'] - cat_budget['allocated_amount']:.2f} грн"
                })
            elif usage_percent >= alert_threshold:  # Наближення до ліміту
                alerts.append({
                    'type': 'warning',
                    'category': cat_budget['category_name'],
                    'icon': cat_budget['category_icon'],
                    'usage_percent': cat_budget['usage_percent'],
                    'remaining': cat_budget['remaining'],
                    'message': f"Залишилось {cat_budget['remaining']:.2f} грн в категорії {cat_budget['category_name']}"
                })
        
        return alerts
    
    def get_month_comparison(self, compare_months=3):
        """Порівняння витрат за останні N місяців"""
        session = Session()
        
        today = datetime.utcnow()
        comparisons = []
        
        for i in range(compare_months):
            # Обчислюємо місяць для порівняння
            if today.month - i <= 0:
                year = today.year - 1
                month = 12 + (today.month - i)
            else:
                year = today.year
                month = today.month - i
            
            start_date = date(year, month, 1)
            end_date = date(year, month, calendar.monthrange(year, month)[1])
            
            # Загальні витрати за місяць
            total_expenses = session.query(func.sum(Transaction.amount)) \
                .filter(Transaction.user_id == self.user_id,
                       Transaction.type == 'expense',
                       Transaction.transaction_date >= start_date,
                       Transaction.transaction_date <= end_date) \
                .scalar() or 0
            
            # Витрати по категоріях
            category_expenses = session.query(
                Category.name,
                Category.icon,
                func.sum(Transaction.amount).label('amount')
            ).join(Transaction, Category.id == Transaction.category_id) \
             .filter(Transaction.user_id == self.user_id,
                    Transaction.type == 'expense',
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date) \
             .group_by(Category.name, Category.icon) \
             .order_by(func.sum(Transaction.amount).desc()) \
             .limit(5) \
             .all()
            
            comparisons.append({
                'period': f"{month:02d}/{year}",
                'year': year,
                'month': month,
                'total_expenses': total_expenses,
                'top_categories': [
                    {
                        'name': cat.name,
                        'icon': cat.icon,
                        'amount': cat.amount
                    }
                    for cat in category_expenses
                ]
            })
        
        session.close()
        return comparisons
    
    def export_budget_data(self, format_type='dict'):
        """
        Експортує дані бюджету для аналізу або резервного копіювання
        
        Args:
            format_type: 'dict', 'json' - формат експорту
        """
        comprehensive_status = self.get_comprehensive_budget_status()
        month_comparison = self.get_month_comparison()
        daily_stats = self.get_daily_spending_stats(30)  # За 30 днів
        alerts = self.get_category_spending_alerts()
        
        export_data = {
            'export_date': datetime.utcnow().isoformat(),
            'user_id': self.user_id,
            'comprehensive_status': comprehensive_status,
            'month_comparison': month_comparison,
            'daily_spending_stats': daily_stats,
            'alerts': alerts,
            'budget_recommendations': self.get_budget_recommendations()
        }
        
        if format_type == 'json':
            import json
            return json.dumps(export_data, default=str, ensure_ascii=False, indent=2)
        
        return export_data
    
    def get_budget_performance_metrics(self):
        """Обчислює метрики ефективності бюджету"""
        comprehensive_status = self.get_comprehensive_budget_status()
        if not comprehensive_status:
            return None
        
        progress = comprehensive_status['budget_progress']
        current_status = comprehensive_status['current_status']
        limits = comprehensive_status['budget_limits']
        
        # Обчислюємо метрики
        metrics = {
            'budget_adherence_score': 0,  # Оцінка дотримання бюджету (0-100)
            'spending_consistency': 0,    # Стабільність витрат
            'category_balance_score': 0,  # Баланс витрат по категоріях
            'planning_accuracy': 0        # Точність планування
        }
        
        # 1. Оцінка дотримання бюджету
        if progress['usage_percent'] <= 100:
            metrics['budget_adherence_score'] = min(100, 120 - progress['usage_percent'])
        else:
            # Штраф за перевищення
            metrics['budget_adherence_score'] = max(0, 100 - (progress['usage_percent'] - 100) * 2)
        
        # 2. Стабільність витрат (на основі статистики за тиждень)
        daily_stats = self.get_daily_spending_stats(7)
        daily_amounts = [day['amount'] for day in daily_stats]
        
        if daily_amounts:
            avg_spending = sum(daily_amounts) / len(daily_amounts)
            variance = sum((x - avg_spending) ** 2 for x in daily_amounts) / len(daily_amounts)
            std_dev = variance ** 0.5
            
            # Чим менша варіація, тим кращий показник
            if avg_spending > 0:
                coefficient_of_variation = std_dev / avg_spending
                metrics['spending_consistency'] = max(0, 100 - coefficient_of_variation * 100)
            else:
                metrics['spending_consistency'] = 100
        
        # 3. Баланс витрат по категоріях
        if comprehensive_status['active_budget']:
            category_budgets = comprehensive_status['active_budget']['category_budgets']
            if category_budgets:
                category_scores = []
                for cat in category_budgets:
                    if cat['allocated_amount'] > 0:
                        usage = cat['actual_spending'] / cat['allocated_amount']
                        # Ідеальне використання - 80-95%
                        if 0.8 <= usage <= 0.95:
                            score = 100
                        elif usage < 0.8:
                            score = usage / 0.8 * 100
                        else:
                            score = max(0, 100 - (usage - 0.95) * 200)
                        category_scores.append(score)
                
                if category_scores:
                    metrics['category_balance_score'] = sum(category_scores) / len(category_scores)
        
        # 4. Точність планування (порівняння з попереднім місяцем)
        month_comparison = self.get_month_comparison(2)
        if len(month_comparison) >= 2:
            current_month = month_comparison[0]['total_expenses']
            prev_month = month_comparison[1]['total_expenses']
            
            if prev_month > 0:
                variance = abs(current_month - prev_month) / prev_month
                metrics['planning_accuracy'] = max(0, 100 - variance * 100)
            else:
                metrics['planning_accuracy'] = 50  # Нейтральна оцінка для нового користувача
        
        # Загальна оцінка
        metrics['overall_score'] = (
            metrics['budget_adherence_score'] * 0.4 +
            metrics['spending_consistency'] * 0.2 +
            metrics['category_balance_score'] * 0.3 +
            metrics['planning_accuracy'] * 0.1
        )
        
        return metrics
