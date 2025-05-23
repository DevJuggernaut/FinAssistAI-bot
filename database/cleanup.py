"""
Функції для очищення бази даних під час розробки
"""
from sqlalchemy.sql import text
from database.session import engine
from database.models import Base
import logging

logger = logging.getLogger(__name__)

def clear_all_tables():
    """Очищає всі таблиці в базі даних"""
    logger.info("Очищення бази даних для режиму розробки...")
    
    # Отримуємо з'єднання
    conn = engine.connect()
    
    # Транзакція для виконання всіх SQL-запитів разом
    with conn.begin() as transaction:
        try:
            # Перевіряємо, чи існують таблиці перед очищенням
            inspector = engine.dialect.inspector(engine)
            existing_tables = inspector.get_table_names()
            
            # Вимикаємо перевірку обмежень зовнішніх ключів
            conn.execute(text("BEGIN;"))
            
            # Очищаємо таблиці в порядку залежностей, якщо вони існують
            if 'financial_advices' in existing_tables:
                conn.execute(text("TRUNCATE TABLE financial_advices CASCADE;"))
            
            if 'category_budgets' in existing_tables:
                conn.execute(text("TRUNCATE TABLE category_budgets CASCADE;"))
            
            if 'budget_plans' in existing_tables:
                conn.execute(text("TRUNCATE TABLE budget_plans CASCADE;"))
            
            if 'transactions' in existing_tables:
                conn.execute(text("TRUNCATE TABLE transactions CASCADE;"))
            
            # Видаляємо користувацькі категорії, але зберігаємо стандартні
            if 'categories' in existing_tables:
                try:
                    conn.execute(text("DELETE FROM categories WHERE is_default = FALSE;"))
                except:
                    # Якщо стовпця is_default немає або виникла інша помилка
                    logger.warning("Не вдалося видалити користувацькі категорії. Видаляємо всі категорії.")
                    conn.execute(text("TRUNCATE TABLE categories CASCADE;"))
            
            if 'users' in existing_tables:
                conn.execute(text("TRUNCATE TABLE users CASCADE;"))
            
            # Скидаємо auto-increment лічильники для PostgreSQL
            tables = ['users', 'categories', 'transactions', 'budget_plans', 'category_budgets', 'financial_advices']
            for table in tables:
                if table in existing_tables:
                    conn.execute(text(f"ALTER SEQUENCE IF EXISTS {table}_id_seq RESTART WITH 1;"))
            
            conn.execute(text("COMMIT;"))
            logger.info("База даних успішно очищена.")
        except Exception as e:
            logger.error(f"Помилка при очищенні бази даних: {e}")
            conn.execute(text("ROLLBACK;"))
            raise
        finally:
            conn.close()

def reset_database():
    """
    Повне очищення і перестворення бази даних.
    Використовувати тільки в режимі розробки!
    """
    logger.info("Повне скидання бази даних для режиму розробки...")
    
    try:
        # Видалення всіх таблиць
        Base.metadata.drop_all(engine)
        logger.info("Таблиці видалено.")
        
        # Створення таблиць заново
        Base.metadata.create_all(engine)
        logger.info("Таблиці створено заново.")
        
        logger.info("База даних успішно скинута.")
    except Exception as e:
        logger.error(f"Помилка при скиданні бази даних: {e}")
        raise
