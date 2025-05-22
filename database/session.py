from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.config import DATABASE_URL

# Створюємо двигун бази даних
engine = create_engine(DATABASE_URL)

# Створюємо фабрику сесій
Session = sessionmaker(bind=engine)

def init_db():
    """Ініціалізація бази даних"""
    from database.models import Base
    from database.migrations import run_migrations
    
    # Створюємо таблиці
    Base.metadata.create_all(engine)
    
    # Запускаємо міграції
    run_migrations() 