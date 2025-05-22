#!/bin/bash

# Змінні середовища для тестування
export TESTING=true

# Створюємо віртуальне середовище, якщо воно не існує
if [ ! -d "venv" ]; then
    echo "Створення віртуального середовища..."
    python3 -m venv venv
fi

# Активуємо віртуальне середовище
source venv/bin/activate

# Встановлюємо залежності
echo "Встановлення залежностей..."
pip install -r requirements.txt

# Запускаємо тести
echo "Запуск тестів..."
python -m unittest discover -s tests

# Додатково запускаємо тест для budget_manager
echo "Запуск тестів менеджера бюджету..."
python -m unittest tests/test_budget_manager.py

# Вимикаємо віртуальне середовище
deactivate

echo "Тестування завершено!"
