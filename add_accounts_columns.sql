-- Міграція для додавання підтримки рахунків в FinAssist
-- Виконати цей скрипт перед запуском migrate_accounts.py

-- 1. Додаємо колонку account_id до таблиці transactions
ALTER TABLE transactions 
ADD COLUMN account_id INTEGER REFERENCES accounts(id);

-- 2. Створюємо індекс для швидкого пошуку транзакцій по рахунках
CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id);

-- 3. Створюємо індекс для пошуку головних рахунків
CREATE INDEX IF NOT EXISTS idx_accounts_is_main ON accounts(user_id, is_main);

-- 4. Створюємо індекс для пошуку активних рахунків
CREATE INDEX IF NOT EXISTS idx_accounts_active ON accounts(user_id, is_active);

-- Підтвердження успішного виконання
SELECT 'Міграція схеми завершена успішно!' as result;
