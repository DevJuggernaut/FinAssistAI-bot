from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Table, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime
import enum

from database.config import DATABASE_URL

# Ініціалізація бази даних
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class TransactionType(enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"

class User(Base):
    """Модель користувача системи"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_active = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Налаштування користувача
    initial_balance = Column(Float, default=0.0)
    currency = Column(String(10), default='UAH')
    monthly_budget = Column(Float, nullable=True)
    notification_enabled = Column(Boolean, default=True)
    
    # Стан налаштування
    setup_step = Column(String(50), default='start')  # start, balance, budget, notifications, completed
    is_setup_completed = Column(Boolean, default=False)
    
    # Зв'язки з іншими таблицями
    transactions = relationship("Transaction", back_populates="user")
    categories = relationship("Category", back_populates="user")
    budget_plans = relationship("BudgetPlan", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"

class Category(Base):
    """Модель категорії витрат/доходів"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # 'income' або 'expense'
    icon = Column(String(50), nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Зв'язки
    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, type={self.type})>"

class Transaction(Base):
    """Модель фінансової транзакції"""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    category_id = Column(Integer, ForeignKey('categories.id'))
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)
    transaction_date = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    type = Column(Enum(TransactionType), nullable=False)
    is_recurring = Column(Boolean, default=False)
    source = Column(String(50), nullable=True)  # 'manual', 'receipt', 'bank_statement'
    receipt_image = Column(String(255), nullable=True)  # шлях до зображення чека
    
    # Зв'язки
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, type={self.type})>"

class BudgetPlan(Base):
    """Модель бюджетного плану"""
    __tablename__ = 'budget_plans'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    total_budget = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Зв'язки
    user = relationship("User", back_populates="budget_plans")
    category_budgets = relationship("CategoryBudget", back_populates="budget_plan")
    
    def __repr__(self):
        return f"<BudgetPlan(id={self.id}, name={self.name}, total_budget={self.total_budget})>"

class CategoryBudget(Base):
    """Модель бюджету для конкретної категорії"""
    __tablename__ = 'category_budgets'
    
    id = Column(Integer, primary_key=True)
    budget_plan_id = Column(Integer, ForeignKey('budget_plans.id'))
    category_id = Column(Integer, ForeignKey('categories.id'))
    allocated_amount = Column(Float, nullable=False)
    
    # Зв'язки
    budget_plan = relationship("BudgetPlan", back_populates="category_budgets")
    category = relationship("Category")
    
    def __repr__(self):
        return f"<CategoryBudget(id={self.id}, category_id={self.category_id}, allocated_amount={self.allocated_amount})>"

class FinancialAdvice(Base):
    """Модель збереження наданих фінансових порад"""
    __tablename__ = 'financial_advices'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    advice_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    category = Column(String(100), nullable=True)  # тип поради: 'savings', 'investment', 'budget'
    is_applied = Column(Boolean, default=False)
    
    # Зв'язки
    user = relationship("User")
    
    def __repr__(self):
        return f"<FinancialAdvice(id={self.id}, user_id={self.user_id}, category={self.category})>"

# Створення всіх таблиць в базі даних
def init_db():
    Base.metadata.create_all(engine)
    # Створення сесії для взаємодії з БД
    session = Session()
    
    # Перевірка наявності дефолтних категорій
    default_categories = [
        # Категорії витрат
        {"name": "Продукти", "type": "expense", "icon": "🛒"},
        {"name": "Транспорт", "type": "expense", "icon": "🚗"},
        {"name": "Кафе і ресторани", "type": "expense", "icon": "🍽️"},
        {"name": "Розваги", "type": "expense", "icon": "🎭"},
        {"name": "Покупки", "type": "expense", "icon": "🛍️"},
        {"name": "Комунальні послуги", "type": "expense", "icon": "🏠"},
        {"name": "Здоров'я", "type": "expense", "icon": "💊"},
        {"name": "Освіта", "type": "expense", "icon": "📚"},
        {"name": "Інше", "type": "expense", "icon": "📌"},
        
        # Категорії доходів
        {"name": "Зарплата", "type": "income", "icon": "💰"},
        {"name": "Фріланс", "type": "income", "icon": "💻"},
        {"name": "Подарунки", "type": "income", "icon": "🎁"},
        {"name": "Інвестиції", "type": "income", "icon": "📈"},
        {"name": "Інше", "type": "income", "icon": "📌"}
    ]
    
    # Додавання дефолтних категорій, якщо їх немає
    if session.query(Category).filter_by(is_default=True).count() == 0:
        for cat in default_categories:
            category = Category(
                name=cat["name"],
                type=cat["type"],
                icon=cat["icon"],
                is_default=True
            )
            session.add(category)
    
    session.commit()
    session.close()