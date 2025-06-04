#!/bin/bash

# Швидкий скрипт для аналізу тестових даних після тестування

set -e

# Кольори
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Аналіз тестових даних FinAssistAI${NC}"
echo "=================================="

# Завантаження змінних оточення
if [ -f ".env" ]; then
    source .env
    if [ -z "$DB_NAME" ]; then
        DB_NAME="finance_bot"
    fi
else
    echo "❌ Файл .env не знайдено!"
    exit 1
fi

# Запуск аналізу
if [ -f "test_data_analysis.py" ]; then
    echo -e "${GREEN}📊 Запускаю детальний аналіз...${NC}"
    echo ""
    python3 test_data_analysis.py
else
    echo "❌ Файл test_data_analysis.py не знайдено!"
    echo "💡 Виконую базовий аналіз через SQL..."
    
    # Базовий аналіз через SQL
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << EOF
\echo '📈 СТАТИСТИКА КОРИСТУВАЧІВ:'
SELECT 
    COUNT(*) as total_users,
    COUNT(CASE WHEN created_at >= CURRENT_DATE THEN 1 END) as new_today
FROM users;

\echo ''
\echo '💰 СТАТИСТИКА ТРАНЗАКЦІЙ:'
SELECT 
    transaction_type,
    COUNT(*) as count,
    ROUND(AVG(amount::numeric), 2) as avg_amount,
    ROUND(SUM(amount::numeric), 2) as total_amount
FROM transactions 
GROUP BY transaction_type
ORDER BY transaction_type;

\echo ''
\echo '📊 ТОП-5 КАТЕГОРІЙ ЗА КІЛЬКІСТЮ ТРАНЗАКЦІЙ:'
SELECT 
    c.name,
    c.emoji,
    COUNT(t.id) as transaction_count,
    ROUND(SUM(t.amount::numeric), 2) as total_amount
FROM categories c
LEFT JOIN transactions t ON c.id = t.category_id
WHERE t.id IS NOT NULL
GROUP BY c.id, c.name, c.emoji
ORDER BY transaction_count DESC
LIMIT 5;

\echo ''
\echo '💡 ОСТАННІ 5 ТРАНЗАКЦІЙ:'
SELECT 
    t.transaction_type,
    c.emoji || ' ' || c.name as category,
    t.amount,
    t.description,
    TO_CHAR(t.created_at, 'DD.MM.YYYY HH24:MI') as created
FROM transactions t
JOIN categories c ON t.category_id = c.id
ORDER BY t.created_at DESC
LIMIT 5;

\echo ''
\echo '🎯 СТАТУС БЮДЖЕТІВ:'
SELECT 
    bp.name as budget_name,
    bp.total_budget,
    COUNT(cb.id) as categories_count,
    ROUND(SUM(cb.allocated_amount::numeric), 2) as allocated_total
FROM budget_plans bp
LEFT JOIN category_budgets cb ON bp.id = cb.budget_plan_id
GROUP BY bp.id, bp.name, bp.total_budget
ORDER BY bp.created_at;
EOF
fi

echo ""
echo -e "${GREEN}✅ Аналіз завершено!${NC}"
