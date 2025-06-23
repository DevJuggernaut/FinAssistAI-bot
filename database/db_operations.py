from database.models import Session, User, Category, Transaction, BudgetPlan, CategoryBudget, FinancialAdvice, TransactionType, Account, AccountType
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
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date.between(start_date, end_date))\
        .scalar() or 0
    
    # Отримуємо суму доходів за місяць
    income = session.query(func.sum(Transaction.amount))\
        .filter(Transaction.user_id == user_id,
                Transaction.type == TransactionType.INCOME,
                Transaction.transaction_date.between(start_date, end_date))\
        .scalar() or 0
    
    # Отримуємо топ категорій витрат
    top_categories_query = session.query(
            Category.name, 
            Category.icon,
            func.sum(Transaction.amount).label('total')
        )\
        .join(Transaction, Transaction.category_id == Category.id)\
        .filter(Transaction.user_id == user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date.between(start_date, end_date))\
        .group_by(Category.name, Category.icon)\
        .order_by(func.sum(Transaction.amount).desc())\
        .limit(5)\
        .all()
    
    # Конвертуємо результати в прості кортежі, щоб уникнути проблем з сесіями
    top_categories = [(cat.name, cat.icon, cat.total) for cat in top_categories_query]
    
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
        query = query.filter(Transaction.transaction_date >= start_date)\
                    .filter(Transaction.transaction_date <= end_date)
    elif start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    elif end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    
    transactions = query.order_by(Transaction.transaction_date.desc())\
        .limit(limit).offset(offset).all()
    
    # Detach objects from session to avoid lazy loading issues
    for transaction in transactions:
        if transaction.category:
            # Зберігаємо назву категорії в окреме поле
            transaction.category_name = transaction.category.name
        else:
            transaction.category_name = None
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

def get_transaction_by_id(transaction_id, user_id):
    """Отримує транзакцію за ID (з перевіркою належності користувачу)"""
    session = Session()
    transaction = session.query(Transaction)\
        .filter(Transaction.id == transaction_id, Transaction.user_id == user_id)\
        .first()
    
    if transaction and transaction.category:
        # Зберігаємо назву категорії
        transaction.category_name = transaction.category.name
        transaction.category_icon = transaction.category.icon
    
    session.close()
    return transaction

def update_transaction(transaction_id, user_id, **updates):
    """Оновлює транзакцію"""
    session = Session()
    transaction = session.query(Transaction)\
        .filter(Transaction.id == transaction_id, Transaction.user_id == user_id)\
        .first()
    
    if not transaction:
        session.close()
        return None
    
    # Оновлюємо тільки ті поля, які передані
    if 'amount' in updates:
        transaction.amount = updates['amount']
    if 'description' in updates:
        transaction.description = updates['description']
    if 'category_id' in updates:
        transaction.category_id = updates['category_id']
    if 'transaction_date' in updates:
        transaction.transaction_date = updates['transaction_date']
    if 'type' in updates:
        transaction.type = updates['type']
    
    session.commit()
    session.refresh(transaction)
    session.close()
    
    return transaction

def delete_transaction(transaction_id, user_id):
    """Видаляє транзакцію"""
    session = Session()
    transaction = session.query(Transaction)\
        .filter(Transaction.id == transaction_id, Transaction.user_id == user_id)\
        .first()
    
    if not transaction:
        session.close()
        return False
    
    session.delete(transaction)
    session.commit()
    session.close()
    
    return True

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
        if category:
            # Detach the object from session to avoid lazy loading issues
            session.expunge(category)
        return category
    finally:
        session.close()

def get_category_by_name(user_id, category_name):
    """Отримує категорію за назвою для конкретного користувача"""
    session = Session()
    try:
        category = session.query(Category).filter(
            Category.user_id == user_id,
            func.lower(Category.name) == func.lower(category_name)
        ).first()
        if category:
            # Detach the object from session to avoid lazy loading issues
            session.expunge(category)
        return category
    finally:
        session.close()

def create_category(user_id, category_name, category_type=None, icon=None):
    """Створює нову категорію для користувача"""
    session = Session()
    try:
        # If category type not specified, guess based on name
        if not category_type:
            income_keywords = ["дохід", "доход", "зарплата", "виплата", "стипендія", 
                              "income", "salary", "payment", "dividend"]
            is_income = any(keyword in category_name.lower() for keyword in income_keywords)
            category_type = TransactionType.INCOME if is_income else TransactionType.EXPENSE
        
        # If icon not specified, use default
        if not icon:
            default_icon = "💰" if category_type == TransactionType.INCOME else "🛒"
        
        category = Category(
            user_id=user_id,
            name=category_name,
            type=category_type,
            icon=icon or default_icon,
            is_default=False
        )
        session.add(category)
        session.commit()
        session.refresh(category)
        # Detach the object from session to avoid lazy loading issues
        session.expunge(category)
        return category
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# ==================== ФУНКЦІЇ ДЛЯ РОБОТИ З РАХУНКАМИ ====================

def create_account(user_id, name, account_type, balance=0.0, currency='UAH', is_main=False, icon=None, description=None):
    """Створює новий рахунок для користувача"""
    from database.models import Account, AccountType
    
    session = Session()
    try:
        # Якщо це буде головний рахунок, скидаємо is_main для інших рахунків
        if is_main:
            existing_accounts = session.query(Account).filter(
                Account.user_id == user_id,
                Account.is_main == True
            ).all()
            for account in existing_accounts:
                account.is_main = False
        
        # Встановлюємо іконку за замовчуванням залежно від типу
        if not icon:
            type_icons = {
                AccountType.CASH: '💵',
                AccountType.BANK_CARD: '💳',
                AccountType.SAVINGS: '💰',
                AccountType.INVESTMENT: '📈',
                AccountType.CREDIT: '💎',
                AccountType.OTHER: '🏦'
            }
            icon = type_icons.get(account_type, '💳')
        
        account = Account(
            user_id=user_id,
            name=name,
            account_type=account_type,
            balance=balance,
            currency=currency,
            is_main=is_main,
            icon=icon,
            description=description
        )
        
        session.add(account)
        session.commit()
        session.refresh(account)
        session.expunge(account)
        return account
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_user_accounts(user_id, include_inactive=False):
    """Отримує список рахунків користувача"""
    from database.models import Account
    
    session = Session()
    try:
        query = session.query(Account).filter(Account.user_id == user_id)
        
        if not include_inactive:
            query = query.filter(Account.is_active == True)
        
        accounts = query.order_by(Account.is_main.desc(), Account.created_at.asc()).all()
        
        # Detach objects from session
        for account in accounts:
            session.expunge(account)
            
        return accounts
    finally:
        session.close()

def get_account_by_id(account_id):
    """Отримує рахунок за ID"""
    from database.models import Account
    
    session = Session()
    try:
        account = session.query(Account).filter(Account.id == account_id).first()
        if account:
            session.expunge(account)
        return account
    finally:
        session.close()

def get_main_account(user_id):
    """Отримує головний рахунок користувача"""
    from database.models import Account
    
    session = Session()
    try:
        account = session.query(Account).filter(
            Account.user_id == user_id,
            Account.is_main == True,
            Account.is_active == True
        ).first()
        
        if account:
            session.expunge(account)
        return account
    finally:
        session.close()

def update_account_balance(account_id, new_balance):
    """Оновлює баланс рахунку"""
    from database.models import Account
    
    session = Session()
    try:
        account = session.query(Account).filter(Account.id == account_id).first()
        if account:
            account.balance = new_balance
            account.updated_at = datetime.utcnow()
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_total_balance(user_id):
    """Отримує загальний баланс всіх активних рахунків користувача"""
    from database.models import Account
    
    session = Session()
    try:
        total = session.query(func.sum(Account.balance)).filter(
            Account.user_id == user_id,
            Account.is_active == True
        ).scalar()
        
        return total or 0.0
    finally:
        session.close()

def get_accounts_count(user_id, include_inactive=False):
    """Отримує кількість рахунків користувача"""
    from database.models import Account
    
    session = Session()
    try:
        query = session.query(Account).filter(Account.user_id == user_id)
        
        if not include_inactive:
            query = query.filter(Account.is_active == True)
        
        return query.count()
    finally:
        session.close()

def transfer_between_accounts(from_account_id, to_account_id, amount, description="Переказ між рахунками"):
    """Здійснює переказ між рахунками"""
    from database.models import Account, Transaction, TransactionType
    
    session = Session()
    try:
        # Отримуємо рахунки
        from_account = session.query(Account).filter(Account.id == from_account_id).first()
        to_account = session.query(Account).filter(Account.id == to_account_id).first()
        
        if not from_account or not to_account:
            return False, "Рахунок не знайдено"
        
        if from_account.balance < amount:
            return False, "Недостатньо коштів на рахунку"
        
        # Оновлюємо баланси
        from_account.balance -= amount
        to_account.balance += amount
        from_account.updated_at = datetime.utcnow()
        to_account.updated_at = datetime.utcnow()
        
        # Створюємо транзакції
        expense_transaction = Transaction(
            user_id=from_account.user_id,
            account_id=from_account_id,
            amount=amount,
            type=TransactionType.EXPENSE,
            description=f"{description} → {to_account.name}",
            transaction_date=datetime.utcnow()
        )
        
        income_transaction = Transaction(
            user_id=to_account.user_id,
            account_id=to_account_id,
            amount=amount,
            type=TransactionType.INCOME,
            description=f"{description} ← {from_account.name}",
            transaction_date=datetime.utcnow()
        )
        
        session.add(expense_transaction)
        session.add(income_transaction)
        session.commit()
        
        return True, "Переказ виконано успішно"
    except Exception as e:
        session.rollback()
        return False, f"Помилка переказу: {str(e)}"
    finally:
        session.close()

def get_accounts_statistics(user_id):
    """Отримує статистику по рахунках"""
    from database.models import Account, Transaction
    
    session = Session()
    try:
        accounts = session.query(Account).filter(
            Account.user_id == user_id,
            Account.is_active == True
        ).all()
        
        if not accounts:
            return {
                'total_accounts': 0,
                'active_accounts': 0,
                'total_balance': 0.0,
                'by_type': {},
                'monthly_growth': 0.0,
                'monthly_transactions': 0
            }
        
        total_balance = sum(account.balance for account in accounts)
        
        # Статистика по типах рахунків
        by_type = {}
        for account in accounts:
            account_type_name = account.account_type.value.replace('_', ' ').title()
            if account_type_name not in by_type:
                by_type[account_type_name] = {
                    'count': 0,
                    'balance': 0.0,
                    'icon': account.icon
                }
            by_type[account_type_name]['count'] += 1
            by_type[account_type_name]['balance'] += account.balance
        
        # Підрахунок транзакцій за місяць (приблизно)
        from datetime import datetime, timedelta
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        monthly_transactions = session.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= month_ago
        ).count()
        
        # Підрахунок зростання за місяць (спрощено)
        monthly_income = session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.INCOME,
            Transaction.transaction_date >= month_ago
        ).scalar() or 0.0
        
        monthly_expenses = session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= month_ago
        ).scalar() or 0.0
        
        monthly_growth = monthly_income - monthly_expenses
        
        return {
            'total_accounts': len(accounts),
            'active_accounts': len(accounts),
            'total_balance': total_balance,
            'by_type': by_type,
            'monthly_growth': monthly_growth,
            'monthly_transactions': monthly_transactions
        }
    finally:
        session.close()
