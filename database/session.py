from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

# Створюємо двигун бази даних з оптимізацією для продакшену
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Вимикаємо SQL логування для продакшену
)

# Створюємо фабрику сесій
Session = sessionmaker(bind=engine)

def init_db():
    """Ініціалізація бази даних"""
    try:
        from database.models import Base
        from database.migrations import run_migrations
        
        logger.info("Ініціалізація бази даних...")
        
        # Створюємо таблиці
        Base.metadata.create_all(engine)
        logger.info("Таблиці створено успішно")
        
        # Запускаємо міграції
        run_migrations()
        logger.info("Міграції виконано успішно")
        
    except Exception as e:
        logger.error(f"Помилка ініціалізації бази даних: {e}")
        raise 