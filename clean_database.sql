-- Clean script for finance_bot database
-- This script truncates all tables but keeps the database structure

-- Disable foreign key checks temporarily to allow truncating tables with relationships
BEGIN;

-- Drop all existing data while preserving default categories
-- First delete from child tables (that have foreign keys)
TRUNCATE TABLE financial_advices CASCADE;
TRUNCATE TABLE category_budgets CASCADE;
TRUNCATE TABLE budget_plans CASCADE;
TRUNCATE TABLE transactions CASCADE;

-- Delete user-specific categories but leave default categories
DELETE FROM categories WHERE is_default = FALSE;

-- Delete users
TRUNCATE TABLE users CASCADE;

-- Re-enable foreign key constraints
COMMIT;

-- Optionally reset sequences (auto-increment counters) to start from 1 again
ALTER SEQUENCE users_id_seq RESTART WITH 1;
ALTER SEQUENCE categories_id_seq RESTART WITH 1;
ALTER SEQUENCE transactions_id_seq RESTART WITH 1;
ALTER SEQUENCE budget_plans_id_seq RESTART WITH 1;
ALTER SEQUENCE category_budgets_id_seq RESTART WITH 1;
ALTER SEQUENCE financial_advices_id_seq RESTART WITH 1;

-- Display confirmation message (will only appear when running in psql client)
\echo 'All data has been cleaned from the finance_bot database, preserving only default categories';
