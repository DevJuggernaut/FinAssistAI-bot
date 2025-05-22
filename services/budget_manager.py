import logging
from datetime import datetime, date
import calendar
from database.models import Session, BudgetPlan, CategoryBudget, Transaction, Category
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
    
    def get_budget_status(self):
        """Отримує статус бюджету"""
        active_budget = self.get_active_budget()
        
        if not active_budget:
            return {
                'status': 'no_active_budget',
                'message': 'У вас немає активного бюджету'
            }
        
        # Перевіряємо перевитрати
        if active_budget['total_remaining'] < 0:
            return {
                'status': 'over_budget',
                'message': f'Перевищення бюджету на {abs(active_budget["total_remaining"]):.2f} грн',
                'data': active_budget
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
                'data': active_budget
            }
        
        return {
            'status': 'ok',
            'message': 'Бюджет в нормі',
            'data': active_budget
        }
    
    def generate_budget_recommendations(self):
        """Генерує рекомендації по складанню бюджету на основі попередніх витрат"""
        session = Session()
        
        # Отримуємо середні витрати по категоріям за останні 3 місяці
        today = datetime.utcnow()
        three_months_ago = date(today.year, max(1, today.month - 3), 1)
        
        category_expenses = session.query(
                Transaction.category_id,
                Category.name,
                Category.icon,
                func.avg(Transaction.amount).label('avg_amount'),
                func.sum(Transaction.amount).label('total_amount'),
                func.count(Transaction.id).label('transaction_count')
            ) \
            .join(Category, Transaction.category_id == Category.id) \
            .filter(Transaction.user_id == self.user_id,
                    Transaction.type == 'expense',
                    Transaction.transaction_date >= three_months_ago) \
            .group_by(Transaction.category_id, Category.name, Category.icon) \
            .order_by(func.sum(Transaction.amount).desc()) \
            .all()
        
        # Рахуємо загальні середні витрати
        total_avg_expense = session.query(func.avg(
                session.query(func.sum(Transaction.amount))
                .filter(Transaction.user_id == self.user_id,
                        Transaction.type == 'expense')
                .group_by(func.extract('month', Transaction.transaction_date))
            )) \
            .scalar() or 0
        
        # Формуємо рекомендації
        recommendations = {
            'total_recommended_budget': total_avg_expense * 1.1,  # Додаємо 10% запасу
            'category_recommendations': []
        }
        
        # Додаємо рекомендації по категоріям
        for cat_id, cat_name, cat_icon, avg_amount, total_amount, tx_count in category_expenses:
            recommendations['category_recommendations'].append({
                'category_id': cat_id,
                'name': cat_name,
                'icon': cat_icon,
                'average_expense': avg_amount,
                'recommended_budget': avg_amount * 1.1,  # Додаємо 10% запасу
                'percentage_of_total': (avg_amount / total_avg_expense) * 100 if total_avg_expense > 0 else 0
            })
        
        session.close()
        return recommendations
