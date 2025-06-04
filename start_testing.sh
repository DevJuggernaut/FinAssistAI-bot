#!/bin/bash

# Скрипт для автоматичного запуску тестування FinAssistAI бота
# Виконує: 1) Очищення БД, 2) Генерацію тестових даних, 3) Запуск бота

set -e  # Зупинити виконання при першій помилці

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функція для виводу повідомлень
print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Перевірка змінних оточення
check_environment() {
    print_step "Перевіряю змінні оточення..."
    
    if [ ! -f ".env" ]; then
        print_error "Файл .env не знайдено!"
        echo "Створіть файл .env з необхідними налаштуваннями:"
        echo "  DB_USER=abobina"
        echo "  DB_PASSWORD=2323"
        echo "  DB_HOST=localhost"
        echo "  DB_PORT=5432"
        echo "  DB_NAME=finance_bot"
        echo "  TELEGRAM_TOKEN=your_token"
        echo "  OPENAI_API_KEY=your_key"
        exit 1
    fi
    
    # Завантаження змінних з .env
    source .env
    
    if [ -z "$DB_NAME" ]; then
        DB_NAME="finance_bot"
    fi
    
    print_success "Змінні оточення завантажено"
}

# Перевірка залежностей
check_dependencies() {
    print_step "Перевіряю залежності..."
    
    # Перевірка PostgreSQL
    if ! command -v psql &> /dev/null; then
        print_error "PostgreSQL не встановлено!"
        echo "Встановіть PostgreSQL: brew install postgresql"
        exit 1
    fi
    
    # Перевірка Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 не встановлено!"
        exit 1
    fi
    
    # Перевірка pip пакетів
    if ! python3 -c "import sqlalchemy, psycopg2, python_dotenv" 2>/dev/null; then
        print_warning "Не всі Python пакети встановлено. Встановлюю..."
        pip3 install sqlalchemy psycopg2-binary python-dotenv
    fi
    
    print_success "Всі залежності доступні"
}

# Перевірка підключення до БД
check_database_connection() {
    print_step "Перевіряю підключення до бази даних..."
    
    # Формування URL для підключення
    DB_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    
    # Тест підключення через psql
    if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" &> /dev/null; then
        print_error "Не вдається підключитися до бази даних!"
        echo "Перевірте налаштування в .env файлі"
        echo "URL: $DB_URL"
        exit 1
    fi
    
    print_success "Підключення до БД встановлено"
}

# Очищення бази даних
clean_database() {
    print_step "Очищаю базу даних..."
    
    if [ ! -f "clean_database.sql" ]; then
        print_error "Файл clean_database.sql не знайдено!"
        exit 1
    fi
    
    # Виконання SQL скрипта
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f clean_database.sql -q
    
    if [ $? -eq 0 ]; then
        print_success "База даних очищена"
    else
        print_error "Помилка при очищенні бази даних"
        exit 1
    fi
}

# Генерація тестових даних
generate_test_data() {
    print_step "Генерую тестові дані..."
    
    if [ ! -f "generate_test_data.py" ]; then
        print_error "Файл generate_test_data.py не знайдено!"
        exit 1
    fi
    
    # Запуск Python скрипта
    python3 generate_test_data.py
    
    if [ $? -eq 0 ]; then
        print_success "Тестові дані згенеровано"
    else
        print_error "Помилка при генерації тестових даних"
        exit 1
    fi
}

# Запуск бота
start_bot() {
    print_step "Запускаю бот..."
    
    if [ ! -f "bot.py" ]; then
        print_error "Файл bot.py не знайдено!"
        exit 1
    fi
    
    echo ""
    echo "=================================="
    echo "🤖 FinAssistAI Bot запущено!"
    echo "=================================="
    echo "Тестові дані готові для користувача @maskofmadnesss (ID: 580683833)"
    echo ""
    echo "Доступні команди для тестування:"
    echo "• /start - початок роботи"
    echo "• /stats - статистика"
    echo "• /budget - бюджет"
    echo "• /help - допомога"
    echo ""
    echo "Для зупинки бота натисніть Ctrl+C"
    echo "=================================="
    echo ""
    
    # Запуск бота
    python3 bot.py
}

# Функція для виводу допомоги
show_help() {
    echo "Використання: $0 [ОПЦІЯ]"
    echo ""
    echo "Опції:"
    echo "  -h, --help          Показати цю допомогу"
    echo "  -c, --clean-only    Тільки очистити базу даних"
    echo "  -g, --generate-only Тільки згенерувати тестові дані"
    echo "  -s, --start-only    Тільки запустити бота"
    echo "  --skip-clean        Пропустити очищення БД"
    echo "  --skip-generate     Пропустити генерацію даних"
    echo ""
    echo "За замовчуванням виконуються всі кроки: очищення -> генерація -> запуск"
}

# Головна функція
main() {
    echo "========================================"
    echo "🚀 FinAssistAI Bot Testing Script"
    echo "========================================"
    echo ""
    
    # Парсинг аргументів
    CLEAN_ONLY=false
    GENERATE_ONLY=false
    START_ONLY=false
    SKIP_CLEAN=false
    SKIP_GENERATE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--clean-only)
                CLEAN_ONLY=true
                shift
                ;;
            -g|--generate-only)
                GENERATE_ONLY=true
                shift
                ;;
            -s|--start-only)
                START_ONLY=true
                shift
                ;;
            --skip-clean)
                SKIP_CLEAN=true
                shift
                ;;
            --skip-generate)
                SKIP_GENERATE=true
                shift
                ;;
            *)
                print_error "Невідома опція: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Базові перевірки
    check_environment
    check_dependencies
    check_database_connection
    
    # Виконання відповідних кроків
    if [ "$CLEAN_ONLY" = true ]; then
        clean_database
        print_success "Очищення завершено!"
        exit 0
    fi
    
    if [ "$GENERATE_ONLY" = true ]; then
        generate_test_data
        print_success "Генерація даних завершена!"
        exit 0
    fi
    
    if [ "$START_ONLY" = true ]; then
        start_bot
        exit 0
    fi
    
    # Повний цикл (за замовчуванням)
    if [ "$SKIP_CLEAN" = false ]; then
        clean_database
    else
        print_warning "Очищення БД пропущено"
    fi
    
    if [ "$SKIP_GENERATE" = false ]; then
        generate_test_data
    else
        print_warning "Генерація даних пропущена"
    fi
    
    echo ""
    print_success "Підготовка завершена! Запускаю бот..."
    sleep 2
    
    start_bot
}

# Обробка сигналів для коректного завершення
trap 'echo -e "\n\n${YELLOW}[INFO]${NC} Зупинка скрипта..."; exit 0' INT TERM

# Запуск головної функції
main "$@"
