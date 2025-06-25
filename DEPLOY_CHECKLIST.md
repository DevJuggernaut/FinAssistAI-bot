# 🚀 Checklist для деплою FinAssistAI бота на Render

## ✅ Підготовка файлів (Виконано)

- [x] `render.yaml` - конфігурація для Render
- [x] `Procfile` - альтернативна конфігурація запуску
- [x] `requirements.txt` - оптимізовано для продакшену
- [x] `Dockerfile` - оновлено для безпечного деплою
- [x] `.env.example` - приклад змінних середовища
- [x] `DEPLOYMENT.md` - повний посібник з деплою
- [x] `health_server.py` - health check для Render
- [x] Оновлено `config.py` та `database/config.py` для підтримки DATABASE_URL
- [x] Оптимізовано `database/session.py` для продакшену

## 📝 Що потрібно зробити вам:

### 1. Підготуйте облікові записи:

- [ ] Створіть бота у @BotFather (отримайте TELEGRAM_TOKEN)
- [ ] Отримайте API ключ OpenAI
- [ ] Створіть акаунт на Render.com

### 2. Завантажте код на GitHub:

- [ ] Створіть репозиторій на GitHub
- [ ] Завантажте всі файли (крім .env)
- [ ] Переконайтеся, що .env файл в .gitignore

### 3. Створіть PostgreSQL базу на Render:

- [ ] Зайдіть на render.com
- [ ] New → PostgreSQL
- [ ] Оберіть безкоштовний план
- [ ] Скопіюйте "External Database URL"

### 4. Створіть Web Service на Render:

- [ ] New → Web Service
- [ ] Підключіть GitHub репозиторій
- [ ] Environment: Python 3
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `python bot.py`

### 5. Налаштуйте Environment Variables:

```
TELEGRAM_TOKEN=ваш_токен_від_botfather
OPENAI_API_KEY=ваш_openai_ключ
DATABASE_URL=посилання_на_postgresql_з_render
DEBUG=false
DEV_MODE=false
```

### 6. Деплой:

- [ ] Натисніть "Create Web Service"
- [ ] Дочекайтеся завершення білду
- [ ] Перевірте логи

## ⚠️ Важливі нюанси безкоштовного плану Render:

1. **Sleep після 15 хвилин бездіяльності**
   - Перший запит може тривати 30-60 секунд
2. **750 годин на місяць**
   - Після вичерпання сервіс вимкнеться до наступного місяця
3. **Обмеження ресурсів**
   - 0.5 CPU, 512MB RAM
   - Може бути повільно для складних ML операцій

## 🔧 Рекомендації для оптимізації:

1. **Мінімізуйте використання ресурсів:**
   - Вимкніть зайві логи
   - Оптимізуйте ML моделі
2. **Налаштуйте правильно:**
   - DEV_MODE=false (щоб не очищувати базу)
   - DEBUG=false (менше логів)

## 📊 Моніторинг:

1. **Render Dashboard** - перевіряйте статус та логи
2. **Database Usage** - стежте за використанням бази
3. **Service Hours** - контролюйте залишок годин

## 🚨 Troubleshooting:

**Бот не відповідає:**

- Перевірте логи в Render Dashboard
- Переконайтеся, що TELEGRAM_TOKEN правильний
- Перевірте статус сервісу

**Database помилки:**

- Перевірте DATABASE_URL
- Переконайтеся, що PostgreSQL сервіс активний

**Out of Memory:**

- Сервіс перезапускається автоматично
- Розгляньте оптимізацію коду

## 📞 Контакти для підтримки:

Якщо виникнуть проблеми:

1. Перевірте логи в Render Dashboard
2. Переглянте DEPLOYMENT.md для детальних інструкцій
3. Звертайтеся до документації Render.com
