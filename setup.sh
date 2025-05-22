#!/bin/bash

# Скрипт для ініціалізації проекту FinAssistAI

echo "🚀 Ініціалізація FinAssistAI Telegram бота..."

# Перевірка наявності Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Помилка: Python 3 не встановлено. Будь ласка, встановіть Python 3."
    exit 1
fi

# Перевірка версії Python
PYTHON_VERSION=$(python3 -c 'import sys; v=sys.version_info[:2]; print(f"{v[0]}.{v[1]}")')
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]); then
    echo "❌ Помилка: Потрібен Python 3.8 або вище. Наразі використовується $PYTHON_VERSION"
    exit 1
fi

# Створення віртуального середовища
echo "🔧 Створюємо віртуальне середовище..."
if [ -d "venv" ]; then
    echo "⚠️ Віртуальне середовище вже існує. Видаляємо та створюємо нове..."
    rm -rf venv
fi

python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Помилка при створенні віртуального середовища."
    exit 1
fi

# Активація віртуального середовища
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Помилка при активації віртуального середовища."
    exit 1
fi

# Встановлення залежностей
echo "📦 Встановлюємо залежності..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Помилка при встановленні залежностей."
    exit 1
fi

# Створення файлу конфігурації .env, якщо його не існує
if [ ! -f ".env" ]; then
    echo "📝 Створюємо файл .env..."
    echo "TELEGRAM_TOKEN=ваш_токен_бота" > .env
    echo "OPENAI_API_KEY=ваш_ключ_openai_api" >> .env
    echo "DATABASE_URL=sqlite:///data/finassist.db" >> .env
    echo "DEBUG=true" >> .env
    echo "⚠️ Створено файл .env. Будь ласка, відредагуйте його та додайте ваші токени."
else
    echo "✅ Файл .env вже існує."
fi

# Створення необхідних директорій
echo "📁 Створюємо необхідні директорії..."
mkdir -p data
mkdir -p uploads/receipts
mkdir -p uploads/statements
mkdir -p reports
mkdir -p logs

# Ініціалізація бази даних
echo "🗄️ Ініціалізуємо базу даних..."
python -c "from database.models import init_db; init_db()"
if [ $? -ne 0 ]; then
    echo "❌ Помилка при ініціалізації бази даних."
    exit 1
fi

# Створення базових категорій
echo "📊 Створюємо базові категорії..."
python -c "from utils.database_setup import create_default_categories; create_default_categories()"
if [ $? -ne 0 ]; then
    echo "⚠️ Помилка при створенні базових категорій."
fi

# Завершення
echo ""
echo "✅ Ініціалізацію завершено успішно!"
echo ""
echo "📌 Що далі:"
echo "1. Відредагуйте файл .env та додайте ваші токени"
echo "2. Запустіть бота командою: python bot.py"
echo "3. Або запустіть тести: ./run_tests.sh"
echo ""
echo "Дякуємо за використання FinAssistAI! 🤖💰"

# Деактивуємо віртуальне середовище
deactivate
