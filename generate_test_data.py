#!/usr/bin/env python3
"""
Скрипт для генерації тестових даних для конкретного користувача
"""

import random
import datetime
from decimal import Decimal
from sqlalchemy.orm import sessionmaker
from database.config import DATABASE_URL
from database.models import (
    Base, engine, User, Category, Transaction, BudgetPlan, 
    CategoryBudget, FinancialAdvice, TransactionType
)
from sqlalchemy import create_engine

def create_session():
    """Створює сесію для бази даних"""
    engine_test = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine_test)
    return Session()

# Категорії витрат з українськими назвами
EXPENSE_CATEGORIES = [
    {"name": "Продукти харчування", "icon": "🛒"},
    {"name": "Транспорт", "icon": "🚗"},
    {"name": "Кафе і ресторани", "icon": "🍽️"},
    {"name": "Розваги", "icon": "🎭"},
    {"name": "Одяг та взуття", "icon": "👕"},
    {"name": "Комунальні послуги", "icon": "🏠"},
    {"name": "Медицина", "icon": "💊"},
    {"name": "Освіта", "icon": "📚"},
    {"name": "Спорт та фітнес", "icon": "🏋️"},
    {"name": "Краса", "icon": "💄"},
    {"name": "Подарунки", "icon": "🎁"},
    {"name": "Побутова техніка", "icon": "📱"},
    {"name": "Авто та паливо", "icon": "⛽"},
    {"name": "Підписки та сервіси", "icon": "📺"},
    {"name": "Інше", "icon": "📌"}
]

# Категорії доходів
INCOME_CATEGORIES = [
    {"name": "Зарплата", "icon": "💰"},
    {"name": "Фріланс", "icon": "💻"},
    {"name": "Подарунки", "icon": "🎁"},
    {"name": "Інвестиції", "icon": "📈"},
    {"name": "Продаж речей", "icon": "🏪"},
    {"name": "Додатковий заробіток", "icon": "💼"},
    {"name": "Повернення боргів", "icon": "💸"},
    {"name": "Інше", "icon": "📌"}
]

# Приклади транзакцій для різних категорій
TRANSACTION_EXAMPLES = {
    "Продукти харчування": [
        "АТБ", "Сільпо", "Новус", "Фора", "Метро", "Покупка овочів на ринку", 
        "М'ясо в Велмарті", "Хліб у пекарні", "Молочні продукти"
    ],
    "Транспорт": [
        "Київпастранс", "Проїзд у метро", "Таксі Uber", "Bolt", "Uklon", 
        "Заправка WOG", "OKKO", "Парковка", "Каршеринг"
    ],
    "Кафе і ресторани": [
        "McDonald's", "KFC", "Пузата хата", "Шаурма", "Кав'ярня", 
        "Піца Челентано", "Суші", "Ресторан", "Кафе Coffeeshop"
    ],
    "Розваги": [
        "Кіно Планета", "Мультиплекс", "Боулінг", "Більярд", "Квест", 
        "Парк розваг", "Концерт", "Театр", "Виставка"
    ],
    "Одяг та взуття": [
        "Zara", "H&M", "LC Waikiki", "Інтертоп", "Sportmaster", 
        "Джинси", "Кросівки", "Куртка", "Футболка"
    ],
    "Комунальні послуги": [
        "Електроенергія ДТЕК", "Газ Нафтогаз", "Вода Київводоканал", 
        "Інтернет Київстар", "Vodafone", "lifecell", "Управляюча компанія"
    ],
    "Медицина": [
        "Аптека АНЦ", "Бажаємо здоров'я", "Ліки Конекс", "Лікар", 
        "Аналізи", "Стоматолог", "Вітаміни", "Медичні послуги"
    ],
    "Освіта": [
        "Курси англійської", "IT-курси", "Книги", "Онлайн курси Udemy", 
        "Coursera", "Навчальні матеріали", "Семінар"
    ],
    "Підписки та сервіси": [
        "Netflix", "Spotify", "YouTube Premium", "Apple Music", 
        "Office 365", "Adobe Creative", "ChatGPT Plus"
    ],
    "Зарплата": [
        "Основна зарплата", "Премія", "13-а зарплата", "Надбавка"
    ],
    "Фріланс": [
        "Веб-розробка", "Дизайн логотипу", "Переклад тексту", 
        "Копірайтинг", "Консультації", "Програмування"
    ],
    "Авто та паливо": [
        "Заправка WOG", "OKKO паливо", "Shell", "Мийка авто", 
        "Техогляд", "Страховка", "Ремонт авто"
    ]
}

def generate_random_amount(category_type, category_name):
    """Генерує реалістичну суму для категорії"""
    if category_type == "expense":
        ranges = {
            "Продукти харчування": (150, 1200),
            "Транспорт": (30, 600),
            "Кафе і ресторани": (80, 800),
            "Розваги": (200, 1500),
            "Одяг та взуття": (300, 2500),
            "Комунальні послуги": (500, 2000),
            "Медицина": (80, 1200),
            "Освіта": (300, 3000),
            "Спорт та фітнес": (150, 800),
            "Краса": (100, 600),
            "Подарунки": (200, 1500),
            "Побутова техніка": (800, 8000),
            "Авто та паливо": (400, 1500),
            "Підписки та сервіси": (50, 500),
            "Інше": (50, 800)
        }
    else:  # income
        ranges = {
            "Зарплата": (20000, 60000),
            "Фріланс": (1500, 12000),
            "Подарунки": (300, 3000),
            "Інвестиції": (800, 8000),
            "Продаж речей": (150, 2000),
            "Додатковий заробіток": (800, 6000),
            "Повернення боргів": (200, 3000),
            "Інше": (100, 1500)
        }
    
    min_amount, max_amount = ranges.get(category_name, (100, 1000))
    return round(random.uniform(min_amount, max_amount), 2)

def generate_random_date(days_back=90):
    """Генерує випадкову дату за останні N днів"""
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=days_back)
    random_days = random.randint(0, days_back)
    return start_date + datetime.timedelta(days=random_days)

def add_categories_to_user(session, user):
    """Додає категорії до існуючого користувача"""
    existing_categories = session.query(Category).filter_by(user_id=user.id).all()
    existing_names = {cat.name for cat in existing_categories}
    
    categories_added = 0
    
    # Додаємо категорії витрат
    for cat_data in EXPENSE_CATEGORIES:
        if cat_data["name"] not in existing_names:
            category = Category(
                user_id=user.id,
                name=cat_data["name"],
                type="expense",
                icon=cat_data["icon"],
                is_default=False
            )
            session.add(category)
            categories_added += 1
            
    # Додаємо категорії доходів
    for cat_data in INCOME_CATEGORIES:
        if cat_data["name"] not in existing_names:
            category = Category(
                user_id=user.id,
                name=cat_data["name"],
                type="income",
                icon=cat_data["icon"],
                is_default=False
            )
            session.add(category)
            categories_added += 1
    
    session.commit()
    print(f"Додано {categories_added} нових категорій")
    return session.query(Category).filter_by(user_id=user.id).all()

def add_transactions_to_user(session, user, categories, num_transactions=100):
    """Додає транзакції до існуючого користувача"""
    transactions_added = 0
    
    for _ in range(num_transactions):
        category = random.choice(categories)
        amount = generate_random_amount(category.type, category.name)
        
        # Визначаємо тип транзакції
        transaction_type = TransactionType.EXPENSE if category.type == "expense" else TransactionType.INCOME
        
        # Генеруємо опис
        examples = TRANSACTION_EXAMPLES.get(category.name, [f"Операція {category.name}"])
        description = random.choice(examples)
        
        # Генеруємо дату
        transaction_date = generate_random_date(90)
        
        transaction = Transaction(
            user_id=user.id,
            category_id=category.id,
            amount=amount,
            description=description,
            transaction_date=datetime.datetime.combine(transaction_date, datetime.time(
                hour=random.randint(8, 22),
                minute=random.randint(0, 59)
            )),
            type=transaction_type,
            source="manual",
            is_recurring=random.choice([True, False]) if random.random() < 0.15 else False
        )
        
        session.add(transaction)
        transactions_added += 1
    
    session.commit()
    print(f"Додано {transactions_added} транзакцій")

def create_budget_for_user(session, user, categories):
    """Створює бюджетний план для користувача"""
    # Перевіряємо, чи є вже бюджетний план
    existing_budget = session.query(BudgetPlan).filter_by(user_id=user.id).first()
    if existing_budget:
        print("Бюджетний план вже існує")
        return
    
    # Створюємо місячний бюджет
    start_date = datetime.date.today().replace(day=1)
    end_date = (start_date + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    
    budget_plan = BudgetPlan(
        user_id=user.id,
        name=f"Бюджет на {start_date.strftime('%B %Y')}",
        start_date=datetime.datetime.combine(start_date, datetime.time()),
        end_date=datetime.datetime.combine(end_date, datetime.time()),
        total_budget=user.monthly_budget or 15000.0
    )
    
    session.add(budget_plan)
    session.commit()
    
    # Створюємо бюджети для категорій витрат
    expense_categories = [cat for cat in categories if cat.type == "expense"]
    total_allocated = 0
    
    budget_allocations = [
        ("Продукти харчування", 0.25),
        ("Транспорт", 0.15),
        ("Комунальні послуги", 0.20),
        ("Кафе і ресторани", 0.10),
        ("Розваги", 0.08),
        ("Одяг та взуття", 0.07),
        ("Медицина", 0.05),
        ("Інше", 0.10)
    ]
    
    for category_name, percentage in budget_allocations:
        category = next((cat for cat in expense_categories if cat.name == category_name), None)
        if category:
            allocated_amount = round(budget_plan.total_budget * percentage, 2)
            
            category_budget = CategoryBudget(
                budget_plan_id=budget_plan.id,
                category_id=category.id,
                allocated_amount=allocated_amount
            )
            session.add(category_budget)
            total_allocated += allocated_amount
    
    session.commit()
    print(f"Створено бюджетний план на {budget_plan.total_budget} UAH")

def add_financial_advice(session, user):
    """Додає фінансові поради для користувача"""
    advice_examples = [
        {
            "category": "savings",
            "text": "Рекомендую створити окрему категорію 'Накопичення' та відкладати щомісяця 15-20% від доходів. Це допоможе створити фінансову подушку безпеки на 3-6 місяців витрат."
        },
        {
            "category": "budget",
            "text": "Проаналізуйте свої витрати на кафе та ресторани. Якщо вони перевищують 10% доходу, спробуйте готувати вдома частіше або встановіть ліміт на харчування поза домом."
        },
        {
            "category": "expenses",
            "text": "Перегляньте підписки та сервіси - часто ми забуваємо про неактивні підписки. Скасуйте ті, якими не користуєтесь активно."
        },
        {
            "category": "planning",
            "text": "Створіть окремий фонд для великих покупок (техніка, відпустка, авто). Відкладайте щомісяця фіксовану суму замість імпульсивних покупок."
        },
        {
            "category": "investment",
            "text": "Розгляньте можливість інвестування частини накопичень у ОВДП або ETF для захисту від інфляції та отримання пасивного доходу."
        }
    ]
    
    # Додаємо 2-3 поради
    num_advices = random.randint(2, 3)
    user_advices = random.sample(advice_examples, num_advices)
    
    for advice_data in user_advices:
        advice = FinancialAdvice(
            user_id=user.id,
            advice_text=advice_data["text"],
            category=advice_data["category"],
            is_applied=False,
            created_at=datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 14))
        )
        session.add(advice)
    
    session.commit()
    print(f"Додано {num_advices} фінансових порад")

def create_user_if_not_exists(session, telegram_id):
    """Створює користувача, якщо його не існує"""
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        print(f"👤 Створюю нового користувача з Telegram ID: {telegram_id}")
        user = User(
            telegram_id=telegram_id,
            username="maskofmadnesss",  # Ваш username
            first_name="Антон",         # Ваше ім'я
            last_name="Бобіна",         # Ваше прізвище
            initial_balance=10000.0,
            monthly_budget=15000.0,
            currency='UAH',
            is_setup_completed=True,
            setup_step='completed',
            notification_enabled=True,
            is_active=True,
            created_at=datetime.datetime.now(),
            last_active=datetime.datetime.now()
        )
        session.add(user)
        session.commit()
        print(f"✅ Користувач створений: {user.first_name} {user.last_name} (@{user.username})")
    return user

def generate_data_for_user(telegram_id, num_transactions=100):
    """Генерує тестові дані для конкретного користувача"""
    session = create_session()
    
    try:
        # Знаходимо або створюємо користувача
        user = create_user_if_not_exists(session, telegram_id)
        
        print(f"🎯 Генерація тестових даних для користувача: {user.first_name} {user.last_name}")
        print(f"   Telegram ID: {user.telegram_id}")
        print(f"   Username: @{user.username}")
        
        # Оновлюємо базові налаштування, якщо потрібно
        updated = False
        if not user.initial_balance:
            user.initial_balance = 10000.0
            updated = True
        if not user.monthly_budget:
            user.monthly_budget = 15000.0
            updated = True
        if not user.currency:
            user.currency = 'UAH'
            updated = True
        if not user.is_setup_completed:
            user.is_setup_completed = True
            user.setup_step = 'completed'
            updated = True
        
        if updated:
            session.commit()
            print("✅ Оновлено базові налаштування користувача")
        
        # Додаємо категорії
        print("\n📂 Додавання категорій...")
        categories = add_categories_to_user(session, user)
        
        # Додаємо транзакції
        print(f"\n💰 Додавання {num_transactions} транзакцій...")
        add_transactions_to_user(session, user, categories, num_transactions)
        
        # Створюємо бюджетний план
        print("\n📊 Створення бюджетного плану...")
        create_budget_for_user(session, user, categories)
        
        # Додаємо фінансові поради
        print("\n💡 Додавання фінансових порад...")
        add_financial_advice(session, user)
        
        # Статистика
        total_transactions = session.query(Transaction).filter_by(user_id=user.id).count()
        total_categories = session.query(Category).filter_by(user_id=user.id).count()
        
        print(f"\n✅ Тестові дані успішно згенеровано!")
        print(f"   Загальна кількість транзакцій: {total_transactions}")
        print(f"   Загальна кількість категорій: {total_categories}")
        print(f"   Бюджет: {user.monthly_budget} {user.currency}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Помилка при генерації даних: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def main():
    """Основна функція"""
    print("🎯 Генератор персональних тестових даних")
    print("="*50)
    
    # Ваш Telegram ID
    your_telegram_id = 580683833
    
    print(f"Генерація даних для користувача з ID: {your_telegram_id}")
    print("⚡ Користувач буде створений автоматично, якщо не існує")
    
    # Запитуємо кількість транзакцій
    try:
        print("\nПараметри генерації:")
        num_transactions = input("Кількість транзакцій (за замовчуванням 100): ").strip()
        num_transactions = int(num_transactions) if num_transactions else 100
        
        if num_transactions < 1:
            print("❌ Кількість транзакцій повинна бути більше 0")
            return
        if num_transactions > 1000:
            print("⚠️  Велика кількість транзакцій може зайняти багато часу")
            confirm = input("Продовжити? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes', 'так', 'т']:
                print("Скасовано")
                return
                
    except ValueError:
        num_transactions = 100
    
    print(f"\n🚀 Початок генерації {num_transactions} транзакцій...")
    generate_data_for_user(your_telegram_id, num_transactions)

if __name__ == "__main__":
    main()
