from database.models import Session, User, Category, Transaction, BudgetPlan, CategoryBudget, FinancialAdvice
from sqlalchemy import func
from datetime import datetime, timedelta
import calendar

def get_or_create_user(telegram_id, username=None, first_name=None, last_name=None):
    """Отримує або створює запис користувача в базі даних"""
    session = Session()
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        session.add(user)
        session.commit()
        
        # Копіюємо дефолтні категорії для нового користувача
        default_categories = session.query(Category).filter(Category.is_default == True).all()
        for default_cat in default_categories:
            user_cat = Category(
                user_id=user.id,
                name=default_cat.name,
                type=default_cat.type,
                icon=default_cat.icon,
                is_default=False
            )
            session.add(user_cat)
        session.commit()
    else:
        # Оновлюємо останню активність
        user.last_active = datetime.utcnow()
        session.commit()
        
    session.refresh(user)
    session.close()
    return user

def update_user_settings(telegram_id, **settings):
    """Оновлення налаштувань користувача"""
    session = Session()
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        session.close()
        return None
    
    # Оновлюємо доступні налаштування
    if 'initial_balance' in settings:
        user.initial_balance = settings['initial_balance']
    
    if 'currency' in settings:
        user.currency = settings['currency']
    
    if 'monthly_budget' in settings:
        user.monthly_budget = settings['monthly_budget']
    
    if 'notification_enabled' in settings:
        user.notification_enabled = settings['notification_enabled']
    
    if 'setup_step' in settings:
        user.setup_step = settings['setup_step']
    
    if 'is_setup_completed' in settings:
        user.is_setup_completed = settings['is_setup_completed']
    
    user.last_active = datetime.utcnow()
    
    session.commit()
    session.refresh(user)
    session.close()
    
    return user

def add_transaction(user_id, amount, description, category_id, transaction_type, transaction_date=None, source="manual", receipt_image=None):
    """Додає нову транзакцію до бази даних"""
    session = Session()
    
    if transaction_date is None:
        transaction_date = datetime.utcnow()
    
    transaction = Transaction(
        user_id=user_id,
        category_id=category_id,
        amount=amount,
        description=description,
        transaction_date=transaction_date,
        type=transaction_type,
        source=source,
        receipt_image=receipt_image
    )
    
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    session.close()
    
    return transaction

def get_user_categories(user_id, category_type=None):
    """Отримує список категорій користувача"""
    session = Session()
    query = session.query(Category).filter(Category.user_id == user_id)
    
    if category_type:
        query = query.filter(Category.type == category_type)
        
    categories = query.all()
    session.close()
    return categories

def get_monthly_stats(user_id, year=None, month=None):
    """Повертає статистику за місяць"""
    session = Session()
    
    if year is None or month is None:
        now = datetime.utcnow()
        year = now.year
        month = now.month
        
    # Отримуємо початок і кінець місяця
    start_date = datetime(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)
    
    # Отримуємо суму витрат за місяць
    expenses = session.query(func.sum(Transaction.amount))\
        .filter(Transaction.user_id == user_id,
                Transaction.type == 'expense',
                Transaction.transaction_date.between(start_date, end_date))\
        .scalar() or 0
    
    # Отримуємо суму доходів за місяць
    income = session.query(func.sum(Transaction.amount))\
        .filter(Transaction.user_id == user_id,
                Transaction.type == 'income',
                Transaction.transaction_date.between(start_date, end_date))\
        .scalar() or 0
    
    # Отримуємо топ категорій витрат
    top_categories = session.query(
            Category.name, 
            Category.icon,
            func.sum(Transaction.amount).label('total')
        )\
        .join(Transaction, Transaction.category_id == Category.id)\
        .filter(Transaction.user_id == user_id,
                Transaction.type == 'expense',
                Transaction.transaction_date.between(start_date, end_date))\
        .group_by(Category.name, Category.icon)\
        .order_by(func.sum(Transaction.amount).desc())\
        .limit(5)\
        .all()
    
    session.close()
    
    return {
        'expenses': expenses,
        'income': income,
        'balance': income - expenses,
        'top_categories': top_categories,
        'year': year,
        'month': month
    }

def get_transactions(user_id, limit=10, offset=0, category_id=None, transaction_type=None, start_date=None, end_date=None):
    """Отримує список транзакцій з фільтрами"""
    from sqlalchemy.orm import joinedload
    
    session = Session()
    query = session.query(Transaction)\
        .options(joinedload(Transaction.category))\
        .filter(Transaction.user_id == user_id)
    
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    
    if transaction_type:
        query = query.filter(Transaction.type == transaction_type)
    
    if start_date and end_date:
        query = query.filter(Transaction.transaction_date.between(start_date, end_date))
    
    transactions = query.order_by(Transaction.transaction_date.desc())\
        .limit(limit).offset(offset).all()
    
    # Detach objects from session to avoid lazy loading issues
    for transaction in transactions:
        session.expunge(transaction)
        if transaction.category:
            session.expunge(transaction.category)
    
    session.close()
    
    return transactions

# Alias for backward compatibility
get_user_transactions = get_transactions

def save_financial_advice(user_id, advice_text, category):
    """Зберігає надану фінансову пораду в базу даних"""
    session = Session()
    
    advice = FinancialAdvice(
        user_id=user_id,
        advice_text=advice_text,
        category=category
    )
    
    session.add(advice)
    session.commit()
    session.close()
    
    return advice

def create_or_update_budget(user_id, name, total_budget, start_date, end_date, category_budgets=None):
    """Створює або оновлює бюджетний план"""
    session = Session()
    
    # Перевіряємо чи існує бюджет з таким ім'ям для користувача
    budget = session.query(BudgetPlan)\
        .filter(BudgetPlan.user_id == user_id, BudgetPlan.name == name)\
        .first()
    
    if not budget:
        budget = BudgetPlan(
            user_id=user_id,
            name=name,
            total_budget=total_budget,
            start_date=start_date,
            end_date=end_date
        )
        session.add(budget)
        session.flush()  # Щоб отримати id нового бюджету
    else:
        budget.total_budget = total_budget
        budget.start_date = start_date
        budget.end_date = end_date
    
    # Якщо вказані бюджети для категорій
    if category_budgets:
        # Видаляємо старі записи бюджету по категоріям
        session.query(CategoryBudget)\
            .filter(CategoryBudget.budget_plan_id == budget.id)\
            .delete()
        
        # Додаємо нові бюджети по категоріям
        for cat_budget in category_budgets:
            category_budget = CategoryBudget(
                budget_plan_id=budget.id,
                category_id=cat_budget['category_id'],
                allocated_amount=cat_budget['amount']
            )
            session.add(category_budget)
    
    session.commit()
    session.refresh(budget)
    session.close()
    
    return budget

def get_user(telegram_id):
    """Отримує користувача за telegram_id"""
    session = Session()
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    session.close()
    return user

def get_category_by_id(category_id):
    """Отримує категорію за ID"""
    session = Session()
    try:
        category = session.query(Category).filter(Category.id == category_id).first()
        return category
    finally:
        session.close()
