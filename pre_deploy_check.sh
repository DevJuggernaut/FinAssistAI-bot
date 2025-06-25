#!/bin/bash

# Pre-deployment test script
echo "🧪 Запуск перевірок перед деплоєм..."

# Перевірка Python версії
echo "📋 Перевірка Python версії..."
python --version

# Перевірка залежностей
echo "📦 Перевірка залежностей..."
pip install -r requirements.txt

# Перевірка синтаксису
echo "🔍 Перевірка синтаксису Python файлів..."
python -m py_compile bot.py
python -m py_compile config.py
python -m py_compile health_server.py

# Перевірка змінних середовища
echo "🔧 Перевірка змінних середовища..."
if [ -f .env ]; then
    source .env
    if [ -z "$TELEGRAM_TOKEN" ]; then
        echo "❌ TELEGRAM_TOKEN не встановлено"
        exit 1
    fi
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "❌ OPENAI_API_KEY не встановлено"
        exit 1
    fi
    echo "✅ Основні змінні середовища встановлені"
else
    echo "⚠️ .env файл не знайдено"
fi

# Перевірка структури проекту
echo "📁 Перевірка структури проекту..."
required_files=(
    "bot.py"
    "config.py" 
    "requirements.txt"
    "Dockerfile"
    "render.yaml"
    "Procfile"
    "database/config.py"
    "database/session.py"
    "handlers"
    "services"
)

for file in "${required_files[@]}"; do
    if [ -e "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file відсутній"
    fi
done

echo ""
echo "🎉 Перевірка завершена!"
echo "📚 Наступні кроки:"
echo "1. Завантажте код на GitHub"
echo "2. Створіть PostgreSQL на Render"
echo "3. Створіть Web Service на Render"
echo "4. Налаштуйте змінні середовища"
echo "5. Деплойте!"
echo ""
echo "📖 Детальні інструкції: DEPLOYMENT.md"
echo "✅ Checklist: DEPLOY_CHECKLIST.md"
