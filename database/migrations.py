from sqlalchemy import create_engine, Column, Float, String, Boolean
from sqlalchemy.sql import text
from database.config import DATABASE_URL

def run_migrations():
    """Запуск міграцій бази даних"""
    engine = create_engine(DATABASE_URL)
    
    # Створюємо з'єднання
    with engine.connect() as connection:
        columns = [
            "ADD COLUMN IF NOT EXISTS initial_balance FLOAT DEFAULT 0.0",
            "ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'UAH'",
            "ADD COLUMN IF NOT EXISTS is_setup_completed BOOLEAN DEFAULT FALSE",
            "ADD COLUMN IF NOT EXISTS monthly_budget FLOAT",
            "ADD COLUMN IF NOT EXISTS notification_enabled BOOLEAN DEFAULT TRUE",
            "ADD COLUMN IF NOT EXISTS setup_step VARCHAR(50) DEFAULT 'start'"
        ]
        for col in columns:
            try:
                connection.execute(text(f"ALTER TABLE users {col}"))
                connection.commit()
                print(f"✅ {col} додано")
            except Exception as e:
                print(f"❌ Помилка при {col}: {str(e)}")
                connection.rollback()

if __name__ == "__main__":
    run_migrations() 