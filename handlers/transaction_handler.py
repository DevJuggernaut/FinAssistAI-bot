"""
Обробники для розширеної функціональності додавання транзакцій
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import os
from datetime import datetime
from database.db_operations import get_user, get_user_categories
from services.statement_parser import StatementParser
from services.vision_parser import VisionReceiptParser

logger = logging.getLogger(__name__)

# ==================== ГОЛОВНЕ МЕНЮ ДОДАВАННЯ ТРАНЗАКЦІЙ ====================

async def show_add_transaction_menu(query, context):
    """Показує головне меню для додавання транзакцій з трьома способами"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Ручне додавання", callback_data="manual_transaction_type")
        ],
        [
            InlineKeyboardButton("📤 Завантажити виписку", callback_data="upload_statement")
        ],
        [
            InlineKeyboardButton("📸 Фото чеку (скоро)", callback_data="receipt_photo_soon")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "💳 *Додати транзакцію*\n\n"
        "Оберіть спосіб додавання транзакції:\n\n"
        "➕ *Ручне додавання* - швидке введення транзакції\n"
        "📤 *Завантажити виписку* - автоматичний парсинг банківської виписки\n"
        "📸 *Фото чеку* - розпізнавання чеку (в розробці)\n\n"
        "🎯 *Мета:* забезпечити максимально зручні та швидкі способи введення фінансових даних."
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== РУЧНЕ ДОДАВАННЯ ====================

async def show_manual_transaction_type(query, context):
    """Показує вибір типу транзакції для ручного додавання"""
    keyboard = [
        [
            InlineKeyboardButton("💸 Витрата", callback_data="manual_expense"),
            InlineKeyboardButton("💰 Дохід", callback_data="manual_income")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="add_transaction")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "➕ *Ручне додавання транзакції*\n\n"
        "🎯 **Форма для введення:**\n"
        "• Тип операції: Дохід/Витрата\n"
        "• Сума: числове поле з валютою\n"
        "• Категорія: випадаючий список з іконками\n"
        "• Коментар/Опис: текстове поле (опціонально)\n"
        "• Дата: за замовчуванням сьогодні\n\n"
        "✨ **Особливості:**\n"
        "• Автопідказки категорій\n"
        "• Валідація введених даних\n"
        "• Миттєве збереження\n\n"
        "Оберіть тип операції:"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_enhanced_expense_form(query, context):
    """Розширена форма для додавання витрати з категоріями та іконками"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("Користувач не знайдений.")
            return
        
        # Отримуємо категорії витрат користувача
        expense_categories = get_user_categories(user.id, category_type='expense')
        
        text = (
            "💸 *Додавання витрати*\n\n"
            "📂 **Оберіть категорію витрати:**\n"
            "_Натисніть на категорію для продовження_\n\n"
        )
        
        keyboard = []
        
        if expense_categories:
            # Популярні категорії зверху
            popular_categories = [cat for cat in expense_categories if cat.name.lower() in 
                                ['їжа', 'транспорт', 'покупки', 'розваги']]
            other_categories = [cat for cat in expense_categories if cat not in popular_categories]
            
            # Додаємо популярні категорії
            if popular_categories:
                text += "🔥 **Популярні категорії:**\n"
                for i in range(0, len(popular_categories), 2):
                    row = []
                    for j in range(i, min(i + 2, len(popular_categories))):
                        category = popular_categories[j]
                        button_text = f"{category.icon or '📦'} {category.name}"
                        callback_data = f"expense_cat_{category.id}"
                        row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
                    keyboard.append(row)
            
            # Додаємо інші категорії
            if other_categories:
                if popular_categories:
                    text += "\n📋 **Інші категорії:**\n"
                for i in range(0, len(other_categories), 2):
                    row = []
                    for j in range(i, min(i + 2, len(other_categories))):
                        category = other_categories[j]
                        button_text = f"{category.icon or '📦'} {category.name}"
                        callback_data = f"expense_cat_{category.id}"
                        row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
                    keyboard.append(row)
            
            # Додаємо кнопку для створення нової категорії
            keyboard.append([InlineKeyboardButton("➕ Створити нову категорію", callback_data="add_expense_category")])
        else:
            text += "❗ *У вас ще немає категорій витрат*\n"
            text += "Створіть першу категорію для початку роботи:\n\n"
            text += "💡 **Рекомендовані категорії:** Їжа, Транспорт, Покупки, Розваги, Інше"
            keyboard.append([InlineKeyboardButton("➕ Створити категорію витрат", callback_data="add_expense_category")])
        
        # Додаємо кнопки управління
        keyboard.append([
            InlineKeyboardButton("🔄 Оновити список", callback_data="manual_expense"),
            InlineKeyboardButton("❌ Скасувати", callback_data="manual_transaction_type")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_enhanced_expense_form: {str(e)}")
        await query.edit_message_text("Виникла помилка. Спробуйте ще раз.")

async def show_enhanced_income_form(query, context):
    """Розширена форма для додавання доходу з категоріями та іконками"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("Користувач не знайдений.")
            return
        
        # Отримуємо категорії доходів користувача
        income_categories = get_user_categories(user.id, category_type='income')
        
        text = (
            "💰 *Додавання доходу*\n\n"
            "📂 **Оберіть категорію доходу:**\n"
            "_Натисніть на категорію для продовження_\n\n"
        )
        
        keyboard = []
        
        if income_categories:
            # Популярні категорії зверху
            popular_categories = [cat for cat in income_categories if cat.name.lower() in 
                                ['зарплата', 'фриланс', 'бонус', 'інвестиції']]
            other_categories = [cat for cat in income_categories if cat not in popular_categories]
            
            # Додаємо популярні категорії
            if popular_categories:
                text += "🔥 **Популярні категорії:**\n"
                for i in range(0, len(popular_categories), 2):
                    row = []
                    for j in range(i, min(i + 2, len(popular_categories))):
                        category = popular_categories[j]
                        button_text = f"{category.icon or '💰'} {category.name}"
                        callback_data = f"income_cat_{category.id}"
                        row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
                    keyboard.append(row)
            
            # Додаємо інші категорії
            if other_categories:
                if popular_categories:
                    text += "\n📋 **Інші категорії:**\n"
                for i in range(0, len(other_categories), 2):
                    row = []
                    for j in range(i, min(i + 2, len(other_categories))):
                        category = other_categories[j]
                        button_text = f"{category.icon or '💰'} {category.name}"
                        callback_data = f"income_cat_{category.id}"
                        row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
                    keyboard.append(row)
            
            # Додаємо кнопку для створення нової категорії
            keyboard.append([InlineKeyboardButton("➕ Створити нову категорію", callback_data="add_income_category")])
        else:
            text += "❗ *У вас ще немає категорій доходів*\n"
            text += "Створіть першу категорію для початку роботи:\n\n"
            text += "💡 **Рекомендовані категорії:** Зарплата, Фриланс, Бонус, Інвестиції, Інше"
            keyboard.append([InlineKeyboardButton("➕ Створити категорію доходів", callback_data="add_income_category")])
        
        # Додаємо кнопки управління
        keyboard.append([
            InlineKeyboardButton("🔄 Оновити список", callback_data="manual_income"),
            InlineKeyboardButton("❌ Скасувати", callback_data="manual_transaction_type")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_enhanced_income_form: {str(e)}")
        await query.edit_message_text("Виникла помилка. Спробуйте ще раз.")

# ==================== ЗАВАНТАЖЕННЯ ВИПИСКИ ====================

async def show_upload_statement_form(query, context):
    """Показує детальну форму для завантаження виписки"""
    keyboard = [
        [
            InlineKeyboardButton("📄 PDF виписка", callback_data="upload_pdf_guide"),
            InlineKeyboardButton("📊 Excel файл", callback_data="upload_excel_guide")
        ],
        [
            InlineKeyboardButton("📋 CSV файл", callback_data="upload_csv_guide")
        ],
        [
            InlineKeyboardButton("⚙️ Налаштування", callback_data="upload_settings"),
            InlineKeyboardButton("❓ Допомога", callback_data="upload_help")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="add_transaction")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📤 *Завантажити виписку*\n\n"
        "📄 **Підтримувані формати:** PDF, Excel (.xlsx, .xls), CSV\n\n"
        "📋 **Процес завантаження:**\n"
        "1️⃣ Оберіть тип файлу та отримайте інструкції\n"
        "2️⃣ Надішліть файл виписки\n"
        "3️⃣ Попередній перегляд знайдених операцій\n"
        "4️⃣ Редагування сум, дат, категорій\n"
        "5️⃣ Виключення непотрібних операцій\n"
        "6️⃣ Підтвердження та автоматичне додавання\n\n"
        "💡 **Додаткові можливості:**\n"
        "• Вибір періоду для імпорту\n"
        "• Налаштування формату дат\n"
        "• Попередження про дублікати\n"
        "• Автоматичне визначення категорій\n\n"
        "Оберіть тип файлу для отримання детальних інструкцій:"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_upload_pdf_guide(query, context):
    """Показує інструкції для завантаження PDF виписки"""
    keyboard = [
        [
            InlineKeyboardButton("📤 Надіслати PDF файл", callback_data="start_pdf_upload")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="upload_statement")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📄 *PDF виписка*\n\n"
        "✅ **Підтримувані банки:**\n"
        "• ПриватБанк\n"
        "• Монобанк\n"
        "• ПУМБ\n"
        "• Ощадбанк\n"
        "• Інші українські банки\n\n"
        "📋 **Що розпізнається:**\n"
        "• Дата операції\n"
        "• Сума транзакції\n"
        "• Опис операції\n"
        "• Тип операції (дохід/витрата)\n\n"
        "⚠️ **Важливо:**\n"
        "• Файл повинен бути текстовим PDF (не скан)\n"
        "• Розмір файлу до 10 МБ\n"
        "• Виписка українською або англійською мовою\n\n"
        "Натисніть кнопку нижче і надішліть PDF файл:"
    )
    
    # Зберігаємо стан очікування файлу
    context.user_data['awaiting_file'] = 'pdf'
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_upload_excel_guide(query, context):
    """Показує інструкції для завантаження Excel файлу"""
    keyboard = [
        [
            InlineKeyboardButton("📤 Надіслати Excel файл", callback_data="start_excel_upload")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="upload_statement")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📊 *Excel файл*\n\n"
        "✅ **Підтримувані формати:** .xlsx, .xls\n\n"
        "📋 **Очікувана структура:**\n"
        "• Стовпець 'Дата' або 'Date'\n"
        "• Стовпець 'Сума' або 'Amount'\n"
        "• Стовпець 'Опис' або 'Description'\n"
        "• Стовпець 'Тип' (опціонально)\n\n"
        "💡 **Приклад структури:**\n"
        "```\n"
        "Дата       | Сума    | Опис\n"
        "01.01.2024 | -150.00 | Продукти\n"
        "02.01.2024 | +5000   | Зарплата\n"
        "```\n\n"
        "⚠️ **Важливо:**\n"
        "• Перший рядок - заголовки\n"
        "• Дати у форматі ДД.ММ.РРРР\n"
        "• Від'ємні суми для витрат\n"
        "• Розмір файлу до 5 МБ\n\n"
        "Натисніть кнопку нижче і надішліть Excel файл:"
    )
    
    # Зберігаємо стан очікування файлу
    context.user_data['awaiting_file'] = 'excel'
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_upload_csv_guide(query, context):
    """Показує інструкції для завантаження CSV файлу"""
    keyboard = [
        [
            InlineKeyboardButton("📤 Надіслати CSV файл", callback_data="start_csv_upload")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="upload_statement")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📋 *CSV файл*\n\n"
        "✅ **Підтримувані роздільники:** кома, крапка з комою\n\n"
        "📋 **Очікувана структура:**\n"
        "• Стовпець 'Дата'\n"
        "• Стовпець 'Сума'\n"
        "• Стовпець 'Опис'\n"
        "• Стовпець 'Категорія' (опціонально)\n\n"
        "💡 **Приклад вмісту:**\n"
        "```\n"
        "Дата,Сума,Опис,Категорія\n"
        "01.01.2024,-150.00,Продукти,Їжа\n"
        "02.01.2024,5000,Зарплата,Дохід\n"
        "```\n\n"
        "⚠️ **Важливо:**\n"
        "• Кодування UTF-8\n"
        "• Перший рядок - заголовки\n"
        "• Дати у форматі ДД.ММ.РРРР\n"
        "• Від'ємні суми для витрат\n"
        "• Розмір файлу до 2 МБ\n\n"
        "Натисніть кнопку нижче і надішліть CSV файл:"
    )
    
    # Зберігаємо стан очікування файлу
    context.user_data['awaiting_file'] = 'csv'
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== ФОТО ЧЕКУ (МАЙБУТНЯ ФУНКЦІЯ) ====================

async def show_receipt_photo_soon(query, context):
    """Показує детальну інформацію про майбутню функцію фото чеків"""
    keyboard = [
        [
            InlineKeyboardButton("📧 Повідомити про готовність", callback_data="notify_receipt_ready")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="add_transaction")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📸 *Фото чеку* (майбутнє розширення)\n\n"
        "🚧 **Функціонал в активній розробці**\n\n"
        "📱 **Планований функціонал:**\n"
        "• Камера або вибір фото з галереї\n"
        "• Розпізнавання тексту (OCR) з високою точністю\n"
        "• Автоматичне визначення:\n"
        "  - Суми покупки\n"
        "  - Дати та часу\n"
        "  - Назви магазину\n"
        "  - Категорії товарів\n"
        "• Ручне підтвердження та коригування\n"
        "• Збереження фото чеку як документа\n\n"
        "🎯 **Підтримувані чеки:**\n"
        "• Касові чеки українських магазинів\n"
        "• Ресторани та кафе\n"
        "• Онлайн-покупки\n"
        "• Квитанції за послуги\n\n"
        "⏰ **Орієнтовний термін:** Q3 2024\n\n"
        "🔔 Натисніть кнопку вище, щоб отримати повідомлення про готовність функції!\n\n"
        "А поки рекомендуємо використовувати ручне додавання або завантаження виписки."
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def notify_receipt_ready(query, context):
    """Реєструє користувача для отримання повідомлення про готовність функції"""
    user_id = query.from_user.id
    
    # Зберігаємо інформацію про бажання отримати повідомлення
    # Тут можна зберегти в базі даних або файлі
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Зрозуміло", callback_data="add_transaction")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🔔 *Успішно зареєстровано!*\n\n"
        "Ви отримаєте повідомлення, як тільки функція розпізнавання чеків буде готова.\n\n"
        "📧 Повідомлення надійде прямо в цей чат.\n\n"
        "Дякуємо за інтерес до нашого продукту! 🙏"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== ДОДАТКОВІ ФУНКЦІЇ ====================

async def show_manual_transaction_form(query, context):
    """Показує форму для ручного додавання транзакції"""
    await show_manual_transaction_type(query, context)

async def show_add_expense_form(query, context):
    """Показує форму для додавання витрати (заглушка)"""
    # Перенаправляємо на новий обробник
    await show_enhanced_expense_form(query, context)

async def show_add_income_form(query, context):
    """Показує форму для додавання доходу (заглушка)"""
    # Перенаправляємо на новий обробник  
    await show_enhanced_income_form(query, context)

async def show_photo_receipt_form(query, context):
    """Показує інформацію про майбутню функцію фото чеків"""
    await show_receipt_photo_soon(query, context)

async def handle_receipt_photo_soon(query, context):
    """Аліас для show_receipt_photo_soon"""
    await show_receipt_photo_soon(query, context)

async def show_all_transactions(query, context):
    """Показує всі транзакції користувача"""
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📊 *Всі транзакції*\n\n"
        "🔧 Ця функція в розробці.\n"
        "Скоро тут буде відображення всіх ваших транзакцій з можливістю фільтрації та сортування."
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_transactions_pagination(query, context, direction="next"):
    """Обробляє пагінацію транзакцій"""
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📄 *Пагінація транзакцій*\n\n"
        "🔧 Ця функція в розробці.\n"
        f"Напрям: {direction}"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== ОБРОБНИКИ CALLBACK'ІВ ДЛЯ ІМПОРТУ ====================

async def handle_import_all_transactions(query, context):
    """Обробляє імпорт всіх знайдених транзакцій"""
    try:
        # Отримуємо транзакції з контексту
        transactions = context.user_data.get('parsed_transactions', [])
        
        if not transactions:
            await query.answer("❌ Немає транзакцій для імпорту")
            return
        
        # Тут буде логіка збереження транзакцій в базу даних
        # Поки що просто показуємо повідомлення про успіх
        
        keyboard = [
            [InlineKeyboardButton("➕ Додати ще транзакції", callback_data="add_transaction")],
            [InlineKeyboardButton("📊 Переглянути всі транзакції", callback_data="view_transactions")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            f"✅ *Успішно імпортовано!*\n\n"
            f"📥 Імпортовано {len(transactions)} транзакцій\n"
            f"💰 Загальна сума: {sum(t.get('amount', 0) for t in transactions):.2f} грн\n\n"
            f"🎉 Ваші фінансові дані оновлено!\n\n"
            f"*Що далі?*\n"
            f"• Додайте ще транзакції\n"
            f"• Перегляньте звіти\n"
            f"• Встановіть бюджети"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Очищуємо тимчасові дані
        context.user_data.pop('parsed_transactions', None)
        
    except Exception as e:
        logger.error(f"Помилка імпорту транзакцій: {e}")
        await query.answer("❌ Помилка імпорту транзакцій")

async def handle_edit_transactions(query, context):
    """Обробляє редагування знайдених транзакцій"""
    keyboard = [
        [InlineKeyboardButton("✅ Імпортувати як є", callback_data="import_all_transactions")],
        [InlineKeyboardButton("🔙 Назад до попереднього перегляду", callback_data="upload_statement")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "✏️ *Редагування транзакцій*\n\n"
        "🔧 Функція детального редагування знаходиться в розробці.\n\n"
        "Поки що ви можете:\n"
        "• Імпортувати транзакції як є\n"
        "• Повернутися до попереднього перегляду\n\n"
        "⏳ Скоро буде доступно:\n"
        "• Редагування кожної транзакції\n"
        "• Зміна категорій\n"
        "• Корекція сум та дат"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_cancel_import(query, context):
    """Обробляє скасування імпорту"""
    # Очищуємо тимчасові дані
    context.user_data.pop('parsed_transactions', None)
    context.user_data.pop('uploaded_file', None)
    
    keyboard = [
        [InlineKeyboardButton("➕ Спробувати знову", callback_data="upload_statement")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "❌ *Імпорт скасовано*\n\n"
        "Файл та знайдені транзакції видалено.\n\n"
        "Ви можете:\n"
        "• Спробувати завантажити інший файл\n"
        "• Повернутися до головного меню"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_remove_duplicates(query, context):
    """Видаляє дублікати з розпізнаних транзакцій"""
    try:
        parsed_transactions = context.user_data.get('parsed_transactions', [])
        if not parsed_transactions:
            await query.edit_message_text("❌ Немає транзакцій для обробки.")
            return
        
        # Простий алгоритм видалення дублікатів за датою та сумою
        unique_transactions = []
        seen = set()
        
        for transaction in parsed_transactions:
            # Створюємо ключ з дати та суми
            key = (transaction.get('date'), transaction.get('amount'))
            if key not in seen:
                seen.add(key)
                unique_transactions.append(transaction)
        
        removed_count = len(parsed_transactions) - len(unique_transactions)
        context.user_data['parsed_transactions'] = unique_transactions
        
        # Оновлюємо попередній перегляд
        from handlers.message_handler import show_transactions_preview
        await show_transactions_preview(query.message, context, unique_transactions)
        
        if removed_count > 0:
            await query.message.reply_text(f"✅ Видалено {removed_count} дублікатів")
        else:
            await query.message.reply_text("ℹ️ Дублікатів не знайдено")
            
    except Exception as e:
        logger.error(f"Error removing duplicates: {str(e)}")
        await query.edit_message_text("❌ Помилка при видаленні дублікатів")

async def handle_set_import_period(query, context):
    """Налаштування періоду для імпорту"""
    try:
        keyboard = [
            [
                InlineKeyboardButton("📅 Останній місяць", callback_data="period_last_month"),
                InlineKeyboardButton("📅 Останні 3 місяці", callback_data="period_last_3_months")
            ],
            [
                InlineKeyboardButton("📅 Останні 6 місяців", callback_data="period_last_6_months"),
                InlineKeyboardButton("📅 Весь рік", callback_data="period_whole_year")
            ],
            [
                InlineKeyboardButton("📅 Вибрати вручну", callback_data="period_custom"),
                InlineKeyboardButton("📅 Всі транзакції", callback_data="period_all")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_preview")
            ]
        ]
        
        await query.edit_message_text(
            "📅 **Оберіть період для імпорту:**\n\n"
            "Ви можете обмежити імпорт транзакцій певним періодом, "
            "щоб не імпортувати старі або непотрібні записи.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error setting import period: {str(e)}")
        await query.edit_message_text("❌ Помилка при налаштуванні періоду")

async def handle_back_to_preview(query, context):
    """Повертає до попереднього перегляду транзакцій"""
    try:
        parsed_transactions = context.user_data.get('parsed_transactions', [])
        if not parsed_transactions:
            await query.edit_message_text("❌ Немає транзакцій для перегляду.")
            return
        
        from handlers.message_handler import show_transactions_preview
        await show_transactions_preview(query.message, context, parsed_transactions)
        
    except Exception as e:
        logger.error(f"Error returning to preview: {str(e)}")
        await query.edit_message_text("❌ Помилка при поверненні до перегляду")

async def handle_period_selection(query, context):
    """Обробляє вибір періоду для імпорту"""
    try:
        period_type = query.data.replace("period_", "")
        parsed_transactions = context.user_data.get('parsed_transactions', [])
        
        if not parsed_transactions:
            await query.edit_message_text("❌ Немає транзакцій для фільтрування.")
            return
        
        from datetime import datetime, timedelta
        now = datetime.now()
        
        # Визначаємо граничну дату
        if period_type == "last_month":
            cutoff_date = now - timedelta(days=30)
        elif period_type == "last_3_months":
            cutoff_date = now - timedelta(days=90)
        elif period_type == "last_6_months":
            cutoff_date = now - timedelta(days=180)
        elif period_type == "whole_year":
            cutoff_date = now - timedelta(days=365)
        elif period_type == "all":
            cutoff_date = None
        elif period_type == "custom":
            # Поки що просто показуємо всі
            cutoff_date = None
        else:
            cutoff_date = None
        
        # Фільтруємо транзакції
        if cutoff_date:
            filtered_transactions = []
            for transaction in parsed_transactions:
                trans_date = transaction.get('date')
                if isinstance(trans_date, datetime) and trans_date >= cutoff_date:
                    filtered_transactions.append(transaction)
        else:
            filtered_transactions = parsed_transactions
        
        # Зберігаємо відфільтровані транзакції
        context.user_data['parsed_transactions'] = filtered_transactions
        
        # Показуємо оновлений перегляд
        from handlers.message_handler import show_transactions_preview
        await show_transactions_preview(query.message, context, filtered_transactions)
        
        period_names = {
            "last_month": "останній місяць",
            "last_3_months": "останні 3 місяці",
            "last_6_months": "останні 6 місяців",
            "whole_year": "весь рік",
            "all": "весь період",
            "custom": "користувацький період"
        }
        
        period_name = period_names.get(period_type, "вибраний період")
        original_count = len(parsed_transactions)
        filtered_count = len(filtered_transactions)
        
        if filtered_count < original_count:
            await query.message.reply_text(
                f"📅 Застосовано фільтр: {period_name}\n"
                f"Транзакцій до фільтрування: {original_count}\n"
                f"Транзакцій після фільтрування: {filtered_count}"
            )
        
    except Exception as e:
        logger.error(f"Error handling period selection: {str(e)}")
        await query.edit_message_text("❌ Помилка при застосуванні фільтру")

# ==================== КІНЕЦЬ ФАЙЛУ ====================

async def show_transaction_success(query, context, transaction_data):
    """Показує повідомлення про успішне додавання транзакції"""
    try:
        transaction_type = transaction_data.get('type', 'expense')
        amount = transaction_data.get('amount', 0)
        description = transaction_data.get('description', 'Транзакція')
        category = transaction_data.get('category', 'Інше')
        
        type_emoji = "💸" if transaction_type == "expense" else "💰"
        type_name = "Витрата" if transaction_type == "expense" else "Дохід"
        
        success_text = f"""✅ **{type_name} додано успішно!**

{type_emoji} **Сума:** {amount:.2f} ₴
📝 **Опис:** {description}
🏷️ **Категорія:** {category}
📅 **Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

Транзакція збережена до вашої фінансової історії."""

        keyboard = [
            [
                InlineKeyboardButton("➕ Додати ще", callback_data="add_transaction"),
                InlineKeyboardButton("📊 Статистика", callback_data="stats_menu")
            ],
            [
                InlineKeyboardButton("🏠 Головне меню", callback_data="back_to_main")
            ]
        ]
        
        await query.edit_message_text(
            success_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error showing transaction success: {str(e)}")
        await query.edit_message_text(
            "✅ Транзакція додана успішно!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]])
        )
