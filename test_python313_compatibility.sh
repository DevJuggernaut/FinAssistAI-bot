#!/bin/bash

echo "🔍 Перевірка сумісності з Python 3.13.4"
echo "========================================"

# Перевірка чи встановлений Python 3.13
if ! command -v python3.13 &> /dev/null; then
    echo "❌ Python 3.13 не встановлений"
    echo "💡 Для локального тестування встановіть Python 3.13:"
    echo "   brew install python@3.13  # macOS"
    echo "   або використайте pyenv"
    echo ""
    echo "✅ На Render буде використано Python 3.13.4 автоматично"
    exit 0
fi

echo "✅ Python 3.13 знайдено"
python3.13 --version

# Створюємо тимчасове віртуальне середовище
echo ""
echo "🔧 Створення тестового віртуального середовища..."
python3.13 -m venv test_env_313
source test_env_313/bin/activate

# Тестуємо встановлення основних залежностей
echo ""
echo "📦 Тестування встановлення основних залежностей..."

pip install --upgrade pip > /dev/null 2>&1

# Тестуємо кожну критичну залежність
critical_deps=(
    "python-telegram-bot==21.9"
    "python-dotenv==1.0.1"
    "SQLAlchemy==2.0.36"
    "psycopg2-binary==2.9.10"
    "openai==1.58.1"
    "numpy==2.2.1"
)

failed_deps=()

for dep in "${critical_deps[@]}"; do
    echo -n "  Тестування $dep... "
    if pip install "$dep" > /dev/null 2>&1; then
        echo "✅"
    else
        echo "❌"
        failed_deps+=("$dep")
    fi
done

echo ""

if [ ${#failed_deps[@]} -eq 0 ]; then
    echo "🎉 Всі критичні залежності успішно встановлені з Python 3.13!"
    
    # Тестуємо імпорт
    echo ""
    echo "🧪 Тестування імпорту модулів..."
    python3.13 -c "
import telegram
import sqlalchemy
import openai
import numpy
import pandas
print('✅ Всі основні модулі успішно імпортовані')
    " 2>/dev/null && echo "✅ Імпорт успішний" || echo "❌ Помилка імпорту"
    
else
    echo "❌ Помилки встановлення:"
    for dep in "${failed_deps[@]}"; do
        echo "  - $dep"
    done
fi

# Очищення
deactivate
rm -rf test_env_313

echo ""
echo "📝 Примітка: На Render всі залежності будуть встановлені автоматично"
