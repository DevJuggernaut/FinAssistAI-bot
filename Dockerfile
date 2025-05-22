FROM python:3.12-slim

WORKDIR /app

# Копіюємо файли проєкту
COPY . /app/

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Встановлюємо wkhtmltopdf для генерації PDF
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wkhtmltopdf \
    tesseract-ocr \
    tesseract-ocr-ukr \
    tesseract-ocr-eng \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Ініціалізуємо базу даних
RUN python -c "from database.models import init_db; init_db()"

# Запускаємо бота
CMD ["python", "bot.py"]
