"""
Обробники для розширеної функціональності додавання транзакцій
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import os
import calendar
from copy import copy
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
            InlineKeyboardButton("📸 Фото чеку", callback_data="start_receipt_photo_upload")
        ],
        [
            InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "💳 *Додати транзакцію*\n\n"
        "Оберіть зручний спосіб:\n\n"
        "➕ *Ручне додавання* — швидко додайте витрату або дохід\n"
        "📤 *Завантажити виписку* — імпортуйте транзакції автоматично\n"
        "📸 *Фото чеку* — зробіть фото для розпізнавання\n"
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
            InlineKeyboardButton("◀️ Назад", callback_data="add_transaction")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "➕ *Ручне додавання*\n\n"
        "Швидко додайте операцію вручну:\n\n"
        "💸 *Витрата* — покупки, оплати, витрати\n"
        "💰 *Дохід* — зарплата, бонуси, надходження\n\n"
        "Оберіть тип операції:\n"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_enhanced_expense_form(query, context):
    """Форма для введення суми та опису витрати"""
    try:
        # Зберігаємо тип транзакції
        context.user_data['transaction_type'] = 'expense'
        
        text = (
            "💸 *Додавання витрати*\n\n"
            "💰 **Введіть суму витрати:**\n"
            "_Наприклад: 450 або 1500.50_\n\n"
            "📝 **Після суми додайте опис (через пробіл):**\n"
            "_Наприклад: 450 АТБ продукти_\n\n"
            "🤖 Система автоматично визначить категорію на основі опису"
        )
        
        keyboard = [
            [InlineKeyboardButton("❌ Скасувати", callback_data="manual_transaction_type")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Встановлюємо стан очікування введення
        context.user_data['awaiting_transaction_input'] = True
        
    except Exception as e:
        logger.error(f"Error in show_enhanced_expense_form: {str(e)}")
        await query.edit_message_text("Виникла помилка. Спробуйте ще раз.")

async def show_enhanced_income_form(query, context):
    """Форма для введення суми та опису доходу"""
    try:
        # Зберігаємо тип транзакції
        context.user_data['transaction_type'] = 'income'
        
        text = (
            "💰 *Додавання доходу*\n\n"
            "💰 **Введіть суму доходу:**\n"
            "_Наприклад: 15000 або 5000.75_\n\n"
            "📝 **Після суми додайте опис (через пробіл):**\n"
            "_Наприклад: 15000 зарплата_\n\n"
            "🤖 Система автоматично визначить категорію на основі опису"
        )
        
        keyboard = [
            [InlineKeyboardButton("❌ Скасувати", callback_data="manual_transaction_type")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Встановлюємо стан очікування введення
        context.user_data['awaiting_transaction_input'] = True
        
    except Exception as e:
        logger.error(f"Error in show_enhanced_income_form: {str(e)}")
        await query.edit_message_text("Виникла помилка. Спробуйте ще раз.")

# ==================== ЗАВАНТАЖЕННЯ ВИПИСКИ ====================

async def show_upload_statement_form(query, context):
    """Показує форму вибору банку для завантаження виписки"""
    keyboard = [
        [
            InlineKeyboardButton("🏦 ПриватБанк", callback_data="select_bank_privatbank"),
            InlineKeyboardButton("🏦 МоноБанк", callback_data="select_bank_monobank")
        ],
        [
            InlineKeyboardButton("◀️ Назад", callback_data="add_transaction")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "📤 *Завантаження виписки з банку*\n\n"
        "Оберіть свій банк, щоб завантажити виписку.\n\n"
        "Кнопки нижче відкриють інструкції та дозволять надіслати файл у потрібному форматі.\n\n"
        "• ПриватБанк — лише Excel (.xlsx)\n"
        "• МоноБанк — CSV, Excel (.xls/.xlsx), PDF\n\n"
        "Після завантаження:\n"
        "1️⃣ Перевірте розпізнані операції\n"
        "2️⃣ Відредагуйте або підтвердьте імпорт\n\n"
        "Оберіть ваш банк, щоб продовжити:"
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
        ]
    ]
    
    # Визначаємо банк для кнопки "Назад"
    back_button_text = "◀️ Назад до форматів"
    if query.data == "privatbank_pdf_guide":
        back_button_callback = "select_bank_privatbank"
        context.user_data['file_source'] = 'privatbank'
    elif query.data == "monobank_pdf_guide":  
        back_button_callback = "select_bank_monobank"
        context.user_data['file_source'] = 'monobank'
    else:
        back_button_callback = "upload_statement"
    
    keyboard.append([InlineKeyboardButton(back_button_text, callback_data=back_button_callback)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📄 *ПриватБанк - PDF виписка*\n\n"
        "💡 **Як отримати PDF виписку з Приват24:**\n"
        "1️⃣ Увійдіть в Приват24\n"
        "2️⃣ Перейдіть до картки/рахунку\n"
        "3️⃣ Виберіть 'Виписка'\n"
        "4️⃣ Встановіть потрібний період\n"
        "5️⃣ Натисніть 'Отримати виписку'\n"
        "6️⃣ Виберіть формат 'PDF'\n\n"
        "📋 **Що розпізнається:**\n"
        "• Дата операції\n"
        "• Сума транзакції\n"
        "• Опис операції\n"
        "• Тип операції (дохід/витрата)\n\n"
        "⚠️ **Важливо:**\n"
        "• Файл повинен бути текстовим PDF (не скан)\n"
        "• Розмір файлу до 10 МБ\n\n"
        "Натисніть кнопку нижче і надішліть PDF файл:"
    )
    
    # Зберігаємо стан очікування файлу
    context.user_data['awaiting_file'] = 'pdf'
    # Не встановлюємо privatbank як джерело для PDF, оскільки PDF не підтримується для ПриватБанку
    if query.data == "privatbank_pdf_guide":
        context.user_data['file_source'] = 'other'  # Переадресовуємо на загальний обробник
    elif query.data == "monobank_pdf_guide":  
        context.user_data['file_source'] = 'monobank'
    else:
        context.user_data['file_source'] = 'other'
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_upload_excel_guide(query, context):
    """Сучасна інструкція для завантаження Excel виписки Monobank з чітким описом кнопки."""
    keyboard = [
        [InlineKeyboardButton("📤 Надіслати Excel файл", callback_data="start_excel_upload")],
        [InlineKeyboardButton("◀️ Назад", callback_data="select_bank_monobank")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "📊 *Monobank — Excel виписка*\n\n"
        "1️⃣ Завантажте Excel файл з додатку Monobank:\n"
        "• Відкрийте Monobank, оберіть картку\n"
        "• Натисніть іконку виписки (справа вгорі)\n"
        "• Виберіть період і формат Excel (.xls/.xlsx)\n"
        "• Надішліть файл у цей чат\n\n"
        "⚠️ Вимоги до файлу:\n"
        "• Формат: .xls або .xlsx\n"
        "• Не змінюйте структуру\n"
        "• Розмір до 10 МБ\n\n"
        "Після завантаження ви зможете переглянути та підтвердити транзакції.\n\n"
        "Натисніть кнопку нижче, щоб завантажити файл."
    )

    context.user_data['awaiting_file'] = 'excel'
    context.user_data['file_source'] = 'monobank'

    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
async def show_privatbank_excel_guide(query, context):
    """Показує деталі інструкції для завантаження виписки з Приватбанку"""
    # Встановлюємо джерело файлу
    context.user_data['file_source'] = 'privatbank'
    
    keyboard = [
        [
            InlineKeyboardButton("📤 Надіслати Excel файл", callback_data="start_excel_upload")
        ],
        [
            InlineKeyboardButton("◀️ Назад до форматів", callback_data="select_bank_privatbank")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📊 *Експорт виписки з ПриватБанку (Excel)*\n\n"
        "1️⃣ Увійдіть у Приват24 (веб або мобільний додаток)\n"
        "2️⃣ Виберіть картку або рахунок\n"
        "3️⃣ Оберіть період\n"
        "4️⃣ Натисніть 'Виписка' → 'Excel'\n"
        "5️⃣ Збережіть файл та надішліть його боту\n\n"
        "Бот автоматично розпізнає всі операції, суми, дати та категорії.\n\n"
        "Натисніть кнопку нижче, щоб завантажити Excel файл."
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_upload_csv_guide(query, context):
    """Сучасна, лаконічна інструкція для завантаження CSV виписки Monobank з чітким описом кнопок."""
    keyboard = [
        [InlineKeyboardButton("📤 Надіслати CSV файл", callback_data="start_csv_upload")],
        [InlineKeyboardButton("◀️ Назад", callback_data="select_bank_monobank")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "📋 *Monobank — CSV виписка*\n\n"
        "1️⃣ Завантажте CSV файл з додатку Monobank:\n"
        "• Відкрийте Monobank, оберіть картку\n"
        "• Натисніть іконку виписки (справа вгорі)\n"
        "• Виберіть період і формат CSV\n"
        "• Надішліть файл у цей чат\n\n"
        "⚠️ Вимоги до файлу:\n"
        "• Формат: .csv\n"
        "• Не змінюйте структуру\n"
        "• Розмір до 10 МБ\n\n"
        "Натисніть кнопку нижче, щоб завантажити файл."
    )

    context.user_data['awaiting_file'] = 'csv'

    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_monobank_pdf_guide(query, context):
    """Показує інструкції для завантаження PDF виписки з МоноБанку"""
    keyboard = [
        [
            InlineKeyboardButton("📤 Надіслати PDF файл", callback_data="start_pdf_upload")
        ],
        [
            InlineKeyboardButton("◀️ Назад до форматів", callback_data="select_bank_monobank")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "📄 *Monobank — PDF виписка*\n\n"
        "1️⃣ Відкрийте додаток Monobank та оберіть картку\n"
        "2️⃣ Натисніть іконку виписки (угорі)\n"
        "3️⃣ Виберіть період і формат PDF\n"
        "4️⃣ Збережіть файл та надішліть його боту\n\n"
        "⚡ *Що далі?*\n"
        "• Бот автоматично розпізнає всі операції\n"
        "• Ви зможете переглянути та підтвердити імпорт\n\n"
        "⚠️ *Вимоги:*\n"
        "• Формат: PDF (не скан, а текстовий файл)\n"
        "• Розмір до 10 МБ\n\n"
        "Натисніть кнопку нижче, щоб завантажити PDF виписку."
    )

    context.user_data['awaiting_file'] = 'pdf'
    context.user_data['file_source'] = 'monobank'

    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_other_bank_statement_form(query, context):
    """Показує опції для завантаження виписки з інших банків"""
    # Зберігаємо обраний банк в контексті
    context.user_data['selected_bank'] = 'other'
    
    keyboard = [
        [
            InlineKeyboardButton("📋 CSV виписка", callback_data="upload_csv_guide")
        ],
        [
            InlineKeyboardButton("📊 Excel виписка", callback_data="upload_excel_guide")
        ],
        [
            InlineKeyboardButton("📄 PDF виписка", callback_data="upload_pdf_guide")
        ],
        [
            InlineKeyboardButton("◀️ Назад до вибору банку", callback_data="upload_statement")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🏛️ *Інший банк - завантаження виписки*\n\n"
        "📋 **Доступні формати:**\n"
        "• CSV файл (.csv)\n"
        "• Excel файл (.xlsx, .xls)\n"
        "• PDF файл (.pdf)\n\n"
        "💡 **Рекомендації щодо виписки:**\n"
        "• Вибирайте максимально детальний формат виписки\n"
        "• Оберіть структурований формат (CSV або Excel)\n"
        "• Перевірте, що виписка містить дати, суми та описи операцій\n"
        "• Якщо можливо, включіть категорії транзакцій у виписку\n\n"
        "⚠️ **Увага:**\n"
        "• У випадку складних форматів бот може розпізнати не всі транзакції\n"
        "• Ви завжди зможете перевірити та підкоригувати результат\n\n"
        "Оберіть формат вашої виписки:"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== РЕДАГУВАННЯ ТРАНЗАКЦІЙ ====================

async def show_edit_transaction_menu(query, context):
    """Показує меню редагування транзакцій"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Редагувати транзакцію", callback_data="edit_transaction")
        ],
        [
            InlineKeyboardButton("🗑️ Видалити транзакцію", callback_data="delete_transaction")
        ],
        [
            InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🛠️ *Редагування транзакцій*\n\n"
        "Оберіть дію, яку ви хочете виконати з транзакцією:\n\n"
        "✏️ *Редагувати транзакцію* - змініть деталі транзакції\n"
        "🗑️ *Видалити транзакцію* - видаліть транзакцію з історії\n\n"
        "◀️ *Назад* - повернення до головного меню"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_edit_transaction_form(query, context, transaction_data):
    """Показує форму редагування транзакції"""
    try:
        # Зберігаємо дані транзакції в контексті
        context.user_data['editing_transaction'] = transaction_data
        
        text = (
            "✏️ *Редагування транзакції*\n\n"
            "Ви можете змінити деталі транзакції та зберегти зміни.\n\n"
            "🗓️ *Дата:* {date}\n"
            "💰 *Сума:* {amount} ₴\n"
            "🏷️ *Категорія:* {category}\n"
            "📝 *Опис:* {description}\n\n"
            "Оберіть, що ви хочете змінити:"
        ).format(
            date=transaction_data['date'].strftime("%d.%m.%Y"),
            amount=f"{transaction_data['amount']:.2f}",
            category=transaction_data.get('category', 'Інше'),
            description=transaction_data.get('description', '')
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🖊️ Змінити суму", callback_data="edit_amount"),
                InlineKeyboardButton("📅 Змінити дату", callback_data="edit_date")
            ],
            [
                InlineKeyboardButton("🏷️ Змінити категорію", callback_data="edit_category"),
                InlineKeyboardButton("📝 Змінити опис", callback_data="edit_description")
            ],
            [
                InlineKeyboardButton("✅ Зберегти зміни", callback_data="save_transaction"),
                InlineKeyboardButton("❌ Скасувати", callback_data="cancel_edit")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_edit_transaction_form: {str(e)}")
        await query.edit_message_text("Виникла помилка. Спробуйте ще раз.")

async def handle_edit_single_transaction(query, context):
    """Показує меню редагування конкретної транзакції"""
    from database.db_operations import get_user, get_transaction_by_id
    
    try:
        # Витягуємо ID транзакції з callback_data
        transaction_id = int(query.data.split('_')[-1])
        
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("Користувач не знайдений.")
            return
        
        transaction = get_transaction_by_id(transaction_id, user.id)
        if not transaction:
            await query.answer("Транзакція не знайдена.", show_alert=True)
            return
        
        # Формуємо інформацію про транзакцію
        date_str = transaction.transaction_date.strftime("%d.%m.%Y %H:%M")
        type_icon = "💸" if transaction.type.value == "expense" else "💰"
        type_name = "Витрата" if transaction.type.value == "expense" else "Дохід"
        category_name = transaction.category_name if hasattr(transaction, 'category_name') and transaction.category_name else "Без категорії"
        description = transaction.description or "Без опису"
        
        text = (
            f"✏️ *Редагування транзакції*\n\n"
            f"{type_icon} *{type_name}*\n"
            f"💰 **Сума:** {transaction.amount:.2f} ₴\n"
            f"📂 **Категорія:** {category_name}\n"
            f"📅 **Дата:** {date_str}\n"
            f"📝 **Опис:** {description}\n\n"
            f"Що ви хочете змінити?"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("💰 Сума", callback_data=f"edit_amount_{transaction_id}"),
                InlineKeyboardButton("📂 Категорія", callback_data=f"change_category_{transaction_id}")
            ],
            [
                InlineKeyboardButton("📝 Опис", callback_data=f"edit_description_{transaction_id}"),
                InlineKeyboardButton("📅 Дата", callback_data=f"edit_date_{transaction_id}")
            ],
            [
                InlineKeyboardButton("🔄 Тип операції", callback_data=f"edit_type_{transaction_id}")
            ],
            [
                InlineKeyboardButton("🗑 Видалити", callback_data=f"delete_transaction_{transaction_id}"),
            ],
            [
                InlineKeyboardButton("◀️ Назад", callback_data="view_all_transactions")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Зберігаємо ID транзакції для подальшого редагування
        context.user_data['editing_transaction_id'] = transaction_id
        
    except Exception as e:
        logger.error(f"Error in handle_edit_single_transaction: {e}")
        await query.answer("Виникла помилка при завантаженні транзакції.", show_alert=True)

async def handle_edit_amount(query, context):
    """Обробляє редагування суми транзакції"""
    try:
        transaction_id = int(query.data.split('_')[-1])
        context.user_data['editing_transaction_id'] = transaction_id
        context.user_data['editing_field'] = 'amount'
        
        keyboard = [
            [InlineKeyboardButton("❌ Скасувати", callback_data=f"edit_transaction_{transaction_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "💰 *Редагування суми*\n\n"
            "Введіть нову суму транзакції (тільки числа):\n\n"
            "Приклад: 150.50 або 1500",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_edit_amount: {e}")
        await query.answer("Виникла помилка.", show_alert=True)

async def handle_edit_description(query, context):
    """Обробляє редагування опису транзакції"""
    try:
        transaction_id = int(query.data.split('_')[-1])
        context.user_data['editing_transaction_id'] = transaction_id
        context.user_data['editing_field'] = 'description'
        
        keyboard = [
            [InlineKeyboardButton("❌ Скасувати", callback_data=f"edit_transaction_{transaction_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📝 *Редагування опису*\n\n"
            "Введіть новий опис транзакції:\n\n"
            "Приклад: Покупка продуктів у супермаркеті",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_edit_description: {e}")
        await query.answer("Виникла помилка.", show_alert=True)

async def handle_edit_category(query, context):
    """Показує список категорій для вибору нової категорії"""
    from database.db_operations import get_user, get_user_categories, get_transaction_by_id
    
    try:
        # Парсимо transaction_id з нового формату change_category_{id}
        transaction_id = int(query.data.replace("change_category_", ""))
        
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("Користувач не знайдений.")
            return
        
        transaction = get_transaction_by_id(transaction_id, user.id)
        if not transaction:
            await query.answer("Транзакція не знайдена.", show_alert=True)
            return
        
        # Отримуємо категорії відповідного типу
        transaction_type_str = transaction.type.value if hasattr(transaction.type, 'value') else str(transaction.type)
        logger.info(f"Looking for categories with type: {transaction_type_str} for user: {user.id}")
        categories = get_user_categories(user.id, category_type=transaction_type_str)
        logger.info(f"Found {len(categories)} categories")
        
        if not categories:
            # Спробуємо отримати всі категорії користувача для діагностики
            all_categories = get_user_categories(user.id)
            logger.info(f"User has {len(all_categories)} total categories: {[f'{cat.name}({cat.type})' for cat in all_categories]}")
            
            # Якщо у користувача є категорії, але не цього типу, показуємо всі
            if all_categories:
                categories = all_categories
                text = f"📂 *Вибір категорії*\n\n⚠️ Категорій типу '{transaction_type_str}' не знайдено.\nОберіть з усіх доступних категорій:"
            else:
                await query.answer("❌ У вас немає жодних категорій. Спочатку створіть категорії в налаштуваннях.", show_alert=True)
                return
        else:
            text = "📂 *Вибір категорії*\n\nОберіть нову категорію для транзакції:"
        
        
        keyboard = []
        for category in categories:
            icon = category.icon if category.icon else "📂"
            button_text = f"{icon} {category.name}"
            keyboard.append([
                InlineKeyboardButton(
                    button_text, 
                    callback_data=f"set_category_{transaction_id}_{category.id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("◀️ Назад", callback_data=f"edit_transaction_{transaction_id}")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_edit_category: {e}")
        await query.answer("Виникла помилка.", show_alert=True)

async def handle_set_category(query, context):
    """Зберігає нову категорію для транзакції"""
    from database.db_operations import update_transaction, get_user
    
    try:
        parts = query.data.split('_')
        if len(parts) < 4:
            logger.error(f"Invalid callback data format: {query.data}")
            await query.answer("❌ Помилка формату даних.", show_alert=True)
            return
            
        transaction_id = int(parts[2])
        category_id = int(parts[3])
        
        # Отримуємо користувача по Telegram ID
        user = get_user(query.from_user.id)
        if not user:
            await query.answer("❌ Користувач не знайдений.", show_alert=True)
            return
        
        logger.info(f"Setting category {category_id} for transaction {transaction_id}, user_id={user.id}")
        
        # Використовуємо внутрішній user_id з бази даних
        result = update_transaction(transaction_id, user.id, category_id=category_id)
        
        if result:
            await query.answer("✅ Категорія оновлена!", show_alert=False)
            # Повертаємося до меню редагування транзакції
            # Створюємо фейковий query object з правильним callback_data
            class FakeQuery:
                def __init__(self, data, from_user, edit_message_text, answer):
                    self.data = data
                    self.from_user = from_user
                    self.edit_message_text = edit_message_text
                    self.answer = answer
            
            fake_query = FakeQuery(
                data=f"edit_transaction_{transaction_id}",
                from_user=query.from_user,
                edit_message_text=query.edit_message_text,
                answer=query.answer
            )
            
            await handle_edit_single_transaction(fake_query, context)
        else:
            logger.error(f"Failed to update transaction {transaction_id} with category {category_id}")
            await query.answer("❌ Помилка при оновленні категорії.", show_alert=True)
            
    except ValueError as e:
        logger.error(f"Invalid ID format in handle_set_category: {e}")
        await query.answer("❌ Невірний формат ідентифікатора.", show_alert=True)
    except Exception as e:
        logger.error(f"Error in handle_set_category: {e}")
        await query.answer("❌ Виникла помилка.", show_alert=True)

async def handle_delete_transaction(query, context):
    """Обробляє видалення транзакції"""
    from database.db_operations import delete_transaction
    
    try:
        transaction_id = int(query.data.split('_')[-1])
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Так, видалити", callback_data=f"confirm_delete_{transaction_id}"),
                InlineKeyboardButton("❌ Ні, залишити", callback_data=f"edit_transaction_{transaction_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗑 *Видалення транзакції*\n\n"
            "Ви впевнені, що хочете видалити цю транзакцію?\n\n"
            "⚠️ **Увага!** Цю дію неможливо буде скасувати.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_delete_transaction: {e}")
        await query.answer("Виникла помилка.", show_alert=True)

async def handle_confirm_delete(query, context):
    """Підтверджує видалення транзакції"""
    from database.db_operations import get_user, delete_transaction
    
    try:
        transaction_id = int(query.data.split('_')[-1])
        
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("Користувач не знайдений.")
            return
        
        success = delete_transaction(transaction_id, user.id)
        
        if success:
            await query.answer("✅ Транзакція видалена!", show_alert=True)
            # Повертаємося до списку всіх транзакцій
            await show_all_transactions(query, context)
        else:
            await query.answer("❌ Помилка при видаленні транзакції.", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error in handle_confirm_delete: {e}")
        await query.answer("Виникла помилка.", show_alert=True)

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
    """Показує форму для фото чеку - тепер готова до використання"""
    await handle_start_receipt_photo_upload(query, context)

async def handle_receipt_photo_soon(query, context):
    """Аліас для обробки фото чеку"""
    await handle_start_receipt_photo_upload(query, context)

async def show_all_transactions(query, context):
    """Показує всі транзакції користувача з пагінацією та фільтрацією"""
    from database.db_operations import get_transactions, get_user_categories
    from database.models import TransactionType
    
    # Отримуємо параметри пагінації з контексту користувача
    if 'transactions_view' not in context.user_data:
        context.user_data['transactions_view'] = {
            'page': 1,
            'per_page': 5,
            'category_id': None,
            'type': None,
            'period': 'month'  # Може бути 'all', 'month', 'week', 'day', 'year'
        }
    
    # Ініціалізуємо фільтри, якщо вони ще не існують
    if 'transaction_filters' not in context.user_data:
        context.user_data['transaction_filters'] = {
            'period': 'month',
            'type': 'all',
            'category': 'all'
        }
    # Синхронізуємо фільтри з параметрами відображення
    filters = context.user_data['transaction_filters']
    view_params = context.user_data['transactions_view']
    
    # Оновлюємо параметри перегляду на основі фільтрів
    view_params['period'] = filters.get('period', 'month')
    view_params['type'] = filters.get('type', 'all') if filters.get('type', 'all') != 'all' else None
    view_params['category_id'] = filters.get('category', 'all') if filters.get('category', 'all') != 'all' else None
    
    # Зберігаємо оновлені параметри
    context.user_data['transactions_view'] = view_params
    
    # Отримуємо параметри з оновлених view_params
    page = view_params.get('page', 1)
    per_page = view_params.get('per_page', 5)
    
    # Convert category_id from string to int if needed
    category_id = view_params.get('category_id', None)
    if category_id and category_id != 'all' and isinstance(category_id, str):
        try:
            category_id = int(category_id)
        except ValueError:
            category_id = None
    elif category_id == 'all':
        category_id = None
        
    # Handle transaction_type properly
    transaction_type = view_params.get('type', None)
    from database.models import TransactionType
    if transaction_type == 'income':
        transaction_type = TransactionType.INCOME
    elif transaction_type == 'expense':
        transaction_type = TransactionType.EXPENSE
    elif transaction_type == 'all' or not transaction_type:
        transaction_type = None
        
    period = view_params.get('period', 'month')
    
    # Визначаємо фільтри дати
    from datetime import datetime, timedelta
    import calendar
    today = datetime.now()
    
    start_date = None
    end_date = None
    
    if period == 'day':
        # Фільтрація за сьогодні
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        period_text = "за сьогодні"
    elif period == 'week':
        # Фільтрація за поточний тиждень (понеділок - неділя)
        start_date = today - timedelta(days=today.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
        period_text = "за тиждень"
    elif period == 'month':
        # Фільтрація за поточний місяць
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Отримуємо останній день місяця
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = today.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
        period_text = "за місяць"
    elif period == 'year':
        # Фільтрація за поточний рік
        start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        period_text = "за рік"
    elif period == 'all':
        # Без фільтрації за датою
        start_date = None
        end_date = None
        period_text = "всі"
    
    # Отримуємо користувача
    telegram_id = query.from_user.id
    from database.db_operations import get_or_create_user
    user = get_or_create_user(telegram_id)
    
    # Визначаємо валюту
    currency = user.currency or "UAH"
    currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
    
    # Отримуємо загальну кількість транзакцій (для пагінації)
    offset = (page - 1) * per_page
    
    # Отримуємо транзакції з бази даних з урахуванням фільтрів
    try:
        # Додаємо логування для діагностики
        logger.info(f"Getting transactions with filters: user_id={user.id}, category_id={category_id}, type={transaction_type}, period={period}")
        if start_date and end_date:
            logger.info(f"Date range: {start_date} to {end_date}")
        
        transactions = get_transactions(
            user_id=user.id,
            limit=per_page,
            offset=offset,
            category_id=category_id,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"Got {len(transactions)} transactions with filters: category_id={category_id}, type={transaction_type}, period={period}")
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
        transactions = []
    
    # Отримуємо загальну кількість транзакцій для пагінації
    # Для цього виконуємо додатковий запит без ліміту, але з тими ж фільтрами
    try:
        total_transactions = len(get_transactions(
            user_id=user.id,
            limit=1000,  # Високе значення, щоб отримати всі
            category_id=category_id,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date
        ))
        
        # Додаємо також загальну кількість транзакцій без фільтрів для діагностики
        total_all_transactions = len(get_transactions(
            user_id=user.id,
            limit=1000
        ))
        logger.info(f"Total transactions with filters: {total_transactions}, Total all transactions: {total_all_transactions}")
    except Exception as e:
        logger.error(f"Error getting total transaction count: {str(e)}")
        total_transactions = 0
    
    total_pages = max(1, (total_transactions + per_page - 1) // per_page)
    
    # Формуємо заголовок
    filter_info = []
    if category_id:
        categories = get_user_categories(user.id)
        category_name = next((c.name for c in categories if c.id == category_id), "Невідома")
        filter_info.append(f"категорія: {category_name}")
        
    if transaction_type:
        type_text = "доходи" if transaction_type == TransactionType.INCOME else "витрати"
        filter_info.append(f"тип: {type_text}")
    
    filter_text = ""
    if filter_info:
        filter_text = f" ({', '.join(filter_info)})"
    
    # Додаємо інформацію про кількість фільтрів
    filters = context.user_data.get('transaction_filters', {})
    active_filters = []
    if filters.get('period', 'month') != 'month':
        active_filters.append('період')
    if filters.get('type', 'all') != 'all':
        active_filters.append('тип')
    if filters.get('category', 'all') != 'all':
        active_filters.append('категорія')
    
    # Формуємо заголовок з окремими рядками для статусу фільтрів
    header = f"📊 *Транзакції {period_text}{filter_text}*\n"
    header += f"📄 Сторінка {page} з {total_pages} | Всього: {total_transactions}\n"
    
    if active_filters:
        header += f"🔍 Активні фільтри: {', '.join(active_filters)}\n"
    
    header += "\n"
    
    # Якщо немає транзакцій
    if not transactions:
        text = header + "\n❌ Транзакції не знайдені."
        
        # Створюємо клавіатуру з кнопками навігації
        keyboard = [
            [
                InlineKeyboardButton("🔄 Скинути фільтри", callback_data="reset_transactions_filters"),
                InlineKeyboardButton("🔍 Налаштувати фільтри", callback_data="transaction_filters")
            ],
            [
                InlineKeyboardButton("◀️ Назад до огляду", callback_data="my_budget_overview")
            ]
        ]
    else:
        # Формуємо список транзакцій з кнопами редагування
        text = header
        
        # Створюємо клавіатуру з кнопками навігації
        keyboard = []
        
        # Додаємо кожну транзакцію як окрему кнопку
        for i, transaction in enumerate(transactions):
            date_str = transaction.transaction_date.strftime("%d.%m")
            
            # Визначаємо категорію та її іконку
            category_name = "Інше"
            category_icon = "📋"
            if transaction.category:
                category_name = transaction.category.name
                category_icon = transaction.category.icon or "📋"
            
            # Визначаємо тип транзакції (дохід/витрата)
            if transaction.type.value == 'income':
                amount_str = f"+{transaction.amount:,.0f} {currency_symbol}"
                type_emoji = "🟢"
            else:
                amount_str = f"{transaction.amount:,.0f} {currency_symbol}"
                type_emoji = "🔴"
            
            # Обмежуємо довжину опису для кнопки
            description = transaction.description or category_name
            if len(description) > 15:
                description = description[:12] + "..."
            
            # Сучасний формат кнопки: емодзі типу, сума, опис, дата
            button_text = f"{type_emoji} {amount_str} • {description} • {date_str}"
            
            # Додаємо кнопку з транзакцією
            keyboard.append([
                InlineKeyboardButton(
                    button_text, 
                    callback_data=f"view_transaction_{transaction.id}"
                )
            ])
        
        # Додаємо кнопи пагінації, якщо потрібно
        pagination_row = []
        if page > 1:
            pagination_row.append(InlineKeyboardButton("◀️ Попередня", callback_data="prev_transactions_page"))
        if page < total_pages:
            pagination_row.append(InlineKeyboardButton("Наступна ▶️", callback_data="next_transactions_page"))
            
        if pagination_row:
            keyboard.append(pagination_row)
        
        # Додаємо кнопку фільтрів (без кнопки "Скинути")
        keyboard.append([InlineKeyboardButton("🔍 Фільтри", callback_data="transaction_filters")])
        
        # Кнопка повернення
        keyboard.append([InlineKeyboardButton("◀️ Назад до огляду", callback_data="my_budget_overview")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Перевірка: якщо текст і розмітка не змінилися, не оновлюємо повідомлення
    try:
        current_message = query.message
        current_text = current_message.text or current_message.caption or ""
        current_reply_markup = current_message.reply_markup
        # Порівнюємо текст і розмітку
        if text.strip() == current_text.strip() and (current_reply_markup == reply_markup or (current_reply_markup and reply_markup and current_reply_markup.to_dict() == reply_markup.to_dict())):
            await query.answer("Ви вже на цій сторінці.")
            return
    except Exception:
        pass  # Якщо щось пішло не так, просто оновлюємо повідомлення

    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== ОБРОБНИКИ CALLBACK'ІВ ДЛЯ ІМПОРТУ ====================

async def handle_import_all_transactions(query, context):
    """Обробляє імпорт всіх знайдених транзакцій та зберігає їх у базу даних"""
    try:
        # Отримуємо транзакції з контексту
        transactions = context.user_data.get('parsed_transactions', [])
        
        if not transactions:
            await query.answer("❌ Немає транзакцій для імпорту")
            return
        
        # Отримуємо користувача
        telegram_id = query.from_user.id
        from database.db_operations import get_or_create_user
        user = get_or_create_user(telegram_id)
        
        # Імпортуємо потрібні класи та функції для збереження транзакцій
        from database.models import Transaction, TransactionType
        from database.session import Session
        from database.db_operations import get_category_by_name, create_category
        from datetime import datetime
        import uuid
        
        session = Session()
        imported_count = 0
        total_amount = 0
        
        # Отримуємо категорії користувача для автоматичної категоризації
        from database.db_operations import get_user_categories
        from services.ml_categorizer import TransactionCategorizer
        user_categories = get_user_categories(user.id)
        categorizer = TransactionCategorizer()
        
        # Готуємо категорії для ML категоризатора
        formatted_categories = []
        for category in user_categories:
            formatted_categories.append({
                'id': category.id,
                'name': category.name,
                'icon': category.icon or ('💸' if category.type == 'expense' else '💰'),
                'type': category.type
            })
        
        # Зберігаємо кожну транзакцію в базу даних
        for trans in transactions:
            try:
                # Отримуємо дані транзакції
                amount = abs(float(trans.get('amount', 0)))  # Завжди позитивна сума
                description = trans.get('description', '').strip() or "Імпортована транзакція"
                trans_type = trans.get('type', 'expense')  # Тип вже має бути визначений в preview
                
                # Визначаємо тип транзакції
                if isinstance(trans_type, str):
                    transaction_type = TransactionType.EXPENSE if trans_type == 'expense' else TransactionType.INCOME
                else:
                    transaction_type = trans_type
                
                logger.info(f"Importing transaction: type={trans_type}, final_enum={transaction_type}, amount={amount}, description={description[:30]}")
                
                total_amount += amount
                
                # Визначаємо дату
                date = trans.get('date')
                if isinstance(date, str):
                    try:
                        # Спробуємо різні формати дати
                        formats = ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y']
                        for fmt in formats:
                            try:
                                date = datetime.strptime(date, fmt).date()
                                break
                            except ValueError:
                                continue
                    except Exception:
                        date = datetime.now().date()
                elif not date:
                    date = datetime.now().date()
                
                # Визначаємо опис
                description = trans.get('description', '').strip() or "Імпортована транзакція"
                if len(description) > 500:  # Обмежуємо довжину опису
                    description = description[:497] + "..."
                
                # Автоматична категоризація на основі категорій користувача
                category_id = None
                category_name = ''
                category_info = trans.get('category', '')
                
                # Перевіряємо, чи category - це словник (результат suggest_category_for_bank_statement)
                if isinstance(category_info, dict):
                    category_name = category_info.get('name', '')
                    logger.info(f"Category is dict: {category_info}")
                elif isinstance(category_info, str):
                    category_name = category_info
                    logger.info(f"Category is string: {category_name}")
                
                logger.info(f"Categorizing transaction: description='{description[:30]}', type={transaction_type.value}, category_name='{category_name}'")
                
                if category_name and formatted_categories:
                    # Спочатку перевіряємо, чи є точне співпадіння з категорією користувача
                    matching_category = next((cat for cat in formatted_categories 
                                            if cat['name'].lower() == category_name.lower() 
                                            and cat['type'] == transaction_type.value), None)
                    
                    if matching_category:
                        category_id = matching_category['id']
                        logger.info(f"Found exact category match: {matching_category['name']} (ID: {category_id})")
                
                # Якщо категорію не знайдено через точне співпадіння, використовуємо ML категоризатор
                if not category_id and formatted_categories:
                    try:
                        transaction_type_str = transaction_type.value if hasattr(transaction_type, 'value') else str(transaction_type)
                        user_categories_by_type = [cat for cat in formatted_categories if cat['type'] == transaction_type_str]
                        
                        logger.info(f"Using ML categorizer: found {len(user_categories_by_type)} categories of type {transaction_type_str}")
                        
                        if user_categories_by_type:
                            suggested_category = categorizer.get_best_category_for_user(
                                description=description,
                                amount=amount,
                                transaction_type=transaction_type_str,
                                user_categories=user_categories_by_type
                            )
                            if suggested_category:
                                category_id = suggested_category['id']
                                logger.info(f"ML categorizer suggested: {suggested_category['name']} (ID: {category_id})")
                            else:
                                logger.warning(f"ML categorizer returned no suggestion")
                    except Exception as e:
                        logger.warning(f"Error in auto-categorization: {e}")
                
                # Якщо категорію не знайдено, використовуємо найбільш загальну категорію відповідного типу
                if not category_id and formatted_categories:
                    # Використовуємо найбільш загальну категорію відповідного типу
                    transaction_type_str = transaction_type.value if hasattr(transaction_type, 'value') else str(transaction_type)
                    default_categories = [cat for cat in formatted_categories if cat['type'] == transaction_type_str]
                    
                    if default_categories:
                        # Шукаємо категорію "Інше" або першу доступну
                        other_category = next((cat for cat in default_categories if 'інше' in cat['name'].lower()), None)
                        category_id = (other_category or default_categories[0])['id']
                        logger.info(f"Using fallback category: {(other_category or default_categories[0])['name']} (ID: {category_id})")
                
                logger.info(f"Final category_id: {category_id}")
                
                # Визначаємо рахунок для транзакції
                account_id = None
                from database.db_operations import get_user_accounts
                user_accounts = get_user_accounts(user.id)
                if user_accounts:
                    # Використовуємо перший доступний рахунок або основний рахунок
                    default_account = next((acc for acc in user_accounts if 'основн' in acc.name.lower() or 'карт' in acc.name.lower()), user_accounts[0])
                    account_id = default_account.id
                
                # Створюємо транзакцію
                transaction = Transaction(
                    user_id=user.id,
                    amount=amount,
                    type=transaction_type,
                    description=description,
                    transaction_date=date,
                    category_id=category_id,
                    account_id=account_id,  # Додаємо рахунок
                    created_at=datetime.now(),
                    source='import'
                )
                
                logger.info(f"Created transaction object: amount={amount}, type={transaction_type}, description={description[:30]}")
                
                # Зберігаємо в базу даних
                session.add(transaction)
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Помилка імпорту окремої транзакції: {e}")
                continue
        
        # Застосовуємо всі зміни
        session.commit()
        session.close()
        
        # Показуємо повідомлення про успіх
        keyboard = [
            [InlineKeyboardButton("➕ Додати ще транзакції", callback_data="add_transaction")],
            [InlineKeyboardButton("📊 Переглянути всі транзакції", callback_data="view_all_transactions")],
            [InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Визначаємо валюту
        currency = user.currency or "UAH"
        currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
        
        text = (
            f"✅ *Успішно імпортовано!*\n\n"
            f"📥 Імпортовано {imported_count} транзакцій\n"
            f"💰 Загальна сума: {total_amount:,.2f} {currency_symbol}\n\n"
            f"🎉 Ваші фінансові дані оновлено!\n\n"
            f"*Що далі?*\n"
            f"• Додайте ще транзакції\n"
            f"• Перегляньте всі транзакції\n"
            f"• Створіть бюджет"
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
    """Обробляє показ списку транзакцій для редагування"""
    from database.db_operations import get_user, get_transactions
    
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("Користувач не знайдений.")
            return
        
        # Отримуємо останні 10 транзакцій користувача
        transactions = get_transactions(user.id, limit=10, offset=0)
        
        if not transactions:
            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="view_all_transactions")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📝 *Редагування транзакцій*\n\n"
                "У вас поки що немає транзакцій для редагування.\n\n"
                "Спочатку додайте транзакції через меню 'Додати транзакцію'.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        # Формуємо список транзакцій з кнопами редагування
        text = "✏️ *Редагування транзакцій*\n\n"
        text += "Оберіть транзакцію для редагування:\n\n"
        
        keyboard = []
        for transaction in transactions:
            date_str = transaction.transaction_date.strftime("%d.%m.%Y")
            type_icon = "🔴" if transaction.type.value == "expense" else "🟢"
            category_name = transaction.category_name if hasattr(transaction, 'category_name') and transaction.category_name else "Без категорії"
            
            # Обмежуємо довжину опису
            description = transaction.description or "Без опису"
            if len(description) > 25:
                description = description[:22] + "..."
            
            # Формуємо текст кнопки без джерела
            button_text = f"{type_icon} {transaction.amount:.0f} ₴ | {category_name} | {date_str}"
            keyboard.append([
                InlineKeyboardButton(
                    button_text, 
                    callback_data=f"edit_transaction_{transaction.id}"
                )
            ])
        
        # Додаємо кнопи навігації
        keyboard.append([
            InlineKeyboardButton("⬅️ Попередні", callback_data="edit_transactions_prev"),
            InlineKeyboardButton("Наступні ➡️", callback_data="edit_transactions_next")
        ])
        keyboard.append([
            InlineKeyboardButton("◀️ Назад", callback_data="view_all_transactions")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Зберігаємо поточну сторінку для навігації
        context.user_data['edit_transactions_page'] = 0
        
    except Exception as e:
        logger.error(f"Error in handle_edit_transactions: {e}")
        await query.answer("Виникла помилка при завантаженні транзакцій.", show_alert=True)

async def handle_cancel_import(query, context):
    """Обробляє скасування імпорту"""
    # Очищуємо тимчасові дані
    context.user_data.pop('parsed_transactions', None)
    context.user_data.pop('uploaded_file', None)
    
    keyboard = [
        [InlineKeyboardButton("➕ Спробувати знову", callback_data="upload_statement")],
        [InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")]
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
                InlineKeyboardButton("◀️ Назад", callback_data="back_to_preview")
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

async def show_receipt_photo_soon(query, context):
    """Показує повідомлення про те, що функція фото чеку вже реалізована"""
    keyboard = [
        [
            InlineKeyboardButton("📷 Сфотографувати чек", callback_data="start_receipt_photo_upload")
        ],
        [
            InlineKeyboardButton("➕ Додати вручну", callback_data="manual_transaction_type"),
            InlineKeyboardButton("📤 Завантажити виписку", callback_data="upload_statement")
        ],
        [
            InlineKeyboardButton("◀️ Назад", callback_data="add_transaction")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📸 *Фото чеку — автоматичне додавання*\n\n"
        "1️⃣ Зробіть чітке фото чеку або завантажте з галереї\n"
        "2️⃣ Бот автоматично розпізнає суму та товари\n"
        "3️⃣ Підтвердьте дані та збережіть транзакцію\n\n"
        "⚡ *Що далі?*\n"
        "• Швидке розпізнавання всіх позицій\n"
        "• Автоматичне визначення категорії\n"
        "• Миттєве збереження у ваш бюджет\n\n"
        "💡 *Для кращого результату:*\n"
        "• Хороше освітлення, чіткий текст\n"
        "• Весь чек в кадрі, без відблисків\n\n"
        "Натисніть кнопку нижче, щоб сфотографувати чек."
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def notify_receipt_ready(query, context):
    """Обробляє запит на повідомлення про готовність функції фото чеку"""
    from database.db_operations import update_user_settings
    
    user_id = query.from_user.id
    update_user_settings(user_id, {"notify_receipt_ready": True})
    
    await query.answer("✅ Ми повідомимо вас, коли ця функція буде готова!")
    await show_receipt_photo_soon(query, context)

async def handle_enhanced_add_transaction(query, context):
    """Обробник для додавання транзакції через розширений інтерфейс"""
    # Повідомляємо користувача про успішне додавання транзакції
    await query.answer("✅ Транзакцію успішно додано!")
    # Повертаємося до головного меню
    await show_add_transaction_menu(query, context)

async def handle_quick_amount_selection(query, context):
    """Обробляє вибір швидкої суми для транзакції"""
    # Отримуємо обрану суму
    amount_str = query.data.split('_')[2]
    amount = float(amount_str)
    # Встановлюємо суму в контексті
    context.user_data['transaction_amount'] = amount
    # Зберігаємо транзакцію
    await handle_enhanced_add_transaction(query, context)

async def show_quick_amount_buttons(query, context, transaction_type):
    """Показує кнопки швидкого вибору суми"""
    keyboard = []
    
    # Типові суми залежно від типу транзакції
    if transaction_type == "expense":
        amounts = [50, 100, 200, 500, 1000]
    else:  # income
        amounts = [1000, 5000, 10000, 15000, 20000]
    
    # Створюємо кнопки для швидкого вибору суми
    for i in range(0, len(amounts), 3):
        row = []
        for j in range(i, min(i + 3, len(amounts))):
            amount = amounts[j]
            button_text = f"{amount} грн"
            callback_data = f"quick_amount_{amount}"
            row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        keyboard.append(row)
    
    # Додаємо кнопку для введення вручну
    keyboard.append([InlineKeyboardButton("➕ Ввести іншу суму", callback_data="manual_amount")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="manual_transaction_type")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"{'💸' if transaction_type == 'expense' else '💰'} *"
        f"{'Додавання витрати' if transaction_type == 'expense' else 'Додавання доходу'}*\n\n"
        "💲 **Вкажіть суму:**\n"
        "Оберіть готову суму або введіть вручну"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_transaction_success(query, context):
    """Показує повідомлення про успішне додавання транзакції"""
    # Отримуємо дані про транзакцію
    transaction_data = context.user_data.get('transaction_data', {})
    
    # Визначаємо тип транзакції та іконку
    transaction_type = transaction_data.get('type', 'expense')
    icon = '💸' if transaction_type == 'expense' else '💰'
    type_text = 'витрати' if transaction_type == 'expense' else 'доходу'
    
    # Форматуємо суму
    amount = transaction_data.get('amount', 0)
    currency = transaction_data.get('currency', '₴')
    amount_text = f"{amount} {currency}"
    
    # Отримуємо категорію
   
    category = transaction_data.get('category_name', 'Невідомо')
    category_icon = transaction_data.get('category_icon', '📁')
    
    # Отримуємо опис (якщо є)
    description = transaction_data.get('description', 'Немає опису')
    
    # Отримуємо дату
    date_str = transaction_data.get('date_str', 'Сьогодні')
    
    # Формуємо текст повідомлення
    text = (
        f"✅ *Транзакція успішно додана!*\n\n"
        f"{icon} **Тип:** {type_text.capitalize()}\n"
        f"💰 **Сума:** {amount_text}\n"
        f"📂 **Категорія:** {category}\n"
        f"📝 **Опис:** {description}\n"
        f"📅 **Дата:** {date_str}\n\n"
        f"Транзакцію збережено у вашій історії."
    )
    
    # Створюємо клавіатуру з кнопками
    keyboard = [
        [InlineKeyboardButton("➕ Додати ще", callback_data="add_transaction")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Очищаємо дані транзакції з контексту
    if 'transaction_data' in context.user_data:
        del context.user_data['transaction_data']
    
    # Відправляємо повідомлення
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_transactions_pagination(query, context, direction=None):
    """Обробка пагінації списку транзакцій"""
    try:
        # Отримуємо поточну сторінку та напрямок
        if direction is None:
            data = query.data.split('_')
            direction = data[2] if len(data) > 2 else 'next'
        # --- Виправлено: працюємо з transactions_view ---
        if 'transactions_view' not in context.user_data:
            context.user_data['transactions_view'] = {
                'page': 1,
                'per_page': 5,
                'category_id': None,
                'type': None,
                'period': 'month'  # Може бути 'all', 'month', 'week', 'day', 'year'
            }
        view_params = context.user_data['transactions_view']
        current_page = view_params.get('page', 1)
        # Розраховуємо нову сторінку
        if direction == 'next':
            view_params['page'] = current_page + 1
        else:  # prev
            view_params['page'] = max(1, current_page - 1)
        context.user_data['transactions_view'] = view_params
        # Оновлюємо список транзакцій з новою сторінкою
        await show_all_transactions(query, context)
    except Exception as e:
        logger.error(f"Error handling pagination: {str(e)}")
        await query.answer("Помилка при пагінації списку транзакцій.")

async def show_transaction_filters(query, context):
    """Показує меню з фільтрами для транзакцій"""
    try:
        # Отримуємо поточні фільтри
        filters = context.user_data.get('transaction_filters', {})
        period = filters.get('period', 'month')
        transaction_type = filters.get('type', 'all')
        category = filters.get('category', 'all')
        
        # Формуємо текст поточних фільтрів
        period_text = {
            'day': 'Сьогодні',
            'week': 'Цей тиждень',
            'month': 'Цей місяць',
            'year': 'Цей рік',
            'all': 'Весь час'
        }.get(period, 'Цей місяць')
        
        type_text = {
            'income': 'Доходи',
            'expense': 'Витрати',
            'all': 'Усі операції'
        }.get(transaction_type, 'Усі операції')
        
        # Отримуємо назву категорії
        if category != 'all' and isinstance(category, int):
            from database.db_operations import get_user, get_user_categories
            user = get_user(query.from_user.id)
            categories = get_user_categories(user.id)
            category_obj = next((c for c in categories if c.id == category), None)
            category_text = category_obj.name if category_obj else 'Невідома категорія'
        else:
            category_text = 'Усі категорії'
        
        # Створюємо клавіатуру з фільтрами
        keyboard = [
            [InlineKeyboardButton(f"📅 Період: {period_text}", callback_data="filter_period")],
            [InlineKeyboardButton(f"💼 Тип: {type_text}", callback_data="filter_type")],
            [InlineKeyboardButton(f"📂 Категорія: {category_text}", callback_data="filter_category")],
            [
                InlineKeyboardButton("🔄 Скинути фільтри", callback_data="reset_transactions_filters"),
                InlineKeyboardButton("🔍 Показати відфільтровані", callback_data="apply_filters")
            ],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_transactions")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "🔍 *Фільтри транзакцій*\n\n"
            "Налаштуйте фільтри для перегляду транзакцій:\n\n"
            f"📅 **Період:** {period_text}\n"
            f"💼 **Тип:** {type_text}\n"
            f"📂 **Категорія:** {category_text}\n\n"
            "➡️ Оберіть параметр для зміни\n"
            "➡️ Натисніть '🔍 Показати відфільтровані' для перегляду результатів"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    except Exception as e:
        logger.error(f"Error showing filters: {str(e)}")
        await query.answer("Помилка при відображенні фільтрів.")

async def reset_transactions_filters(query, context):
    """Скидає всі фільтри транзакцій"""
    try:
        # Скидаємо фільтри
        context.user_data['transaction_filters'] = {
            'period': 'month',
            'type': 'all',
            'category': 'all'
              
       
       
        }
        
        # Скидаємо параметри відображення
       

        context.user_data['transactions_view'] = {
            'page': 1,
            'per_page': 5,
            'category_id': None,
            'type': None,
            'period': 'month'  # Може бути 'all', 'month', 'week', 'day', 'year'
        }
        
        # Повідомляємо про скидання
        await query.answer("✅ Фільтри скинуто")
        
        # Відображаємо транзакції з оновленими фільтрами
        await show_all_transactions(query, context)
    
    except Exception as e:
        logger.error(f"Error resetting filters: {str(e)}")
        await query.answer("Помилка при скиданні фільтрів.")

async def handle_period_filter(query, context, period=None):
    """Обробляє зміну фільтра періоду"""
    try:
        # Якщо period не вказано або він дорівнює 'next', показуємо меню вибору періоду

        if period is None or period == 'next':
            await show_period_filter_menu(query, context)
            return
        
        # Отримуємо поточні фільтри
        filters = context.user_data.get('transaction_filters', {})
        
        # Встановлюємо конкретний період
        filters['period'] = period
        
        # Зберігаємо оновлені фільтри
        context.user_data['transaction_filters'] = filters
        
        # Оновлюємо параметри для відображення транзакцій
        view_params = context.user_data.get('transactions_view', {})
        view_params['period'] = filters['period']
        view_params['page'] = 1   # Скидаємо сторінку
        context.user_data['transactions_view'] = view_params
        
        # Повідомляємо про успішне застосування фільтра
        await query.answer(f"✅ Період змінено на: {period}")
        
        # Показуємо оновлений екран фільтрів
        await show_transaction_filters(query, context)
    
    except Exception as e:
        logger.error(f"Error handling period filter: {str(e)}")
        await query.answer("Помилка при зміні фільтра періоду.")

async def handle_type_filter(query, context, preset_type=None):
    """Обробляє зміну фільтра типу транзакції"""
    try:
        # Якщо preset_type не вказано або він дорівнює 'next', показуємо меню вибору типу
        if preset_type is None or preset_type == 'next':
            await show_type_filter_menu(query, context)
            return
        
        # Отримуємо поточні фільтри
        filters = context.user_data.get('transaction_filters', {})
        
        # Встановлюємо конкретний тип
        filters['type'] = preset_type
        
        # Зберігаємо оновлені фільтри
        context.user_data['transaction_filters'] = filters
        
        # Оновлюємо параметри для відображення транзакцій
        view_params = context.user_data.get('transactions_view', {})
        view_params['type'] = filters['type'] if filters['type'] != 'all' else None
        view_params['page'] = 1  # Скидаємо сторінку
        context.user_data['transactions_view'] = view_params
        
        # Повідомляємо про успішне застосування фільтра
        type_text = "Доходи" if preset_type == "income" else "Витрати" if preset_type == "expense" else "Всі транзакції"
        await query.answer(f"✅ Тип змінено на: {type_text}")
        
        # Показуємо оновлений екран фільтрів
        await show_transaction_filters(query, context)
    
    except Exception as e:
        logger.error(f"Error handling type filter: {str(e)}")
        await query.answer("Помилка при зміні фільтра типу.")

async def handle_category_filter(query, context, preset_category=None):
    """Обробляє зміну фільтра категорії"""
    try:
        # Отримуємо поточні фільтри
        filters = context.user_data.get('transaction_filters', {})
        
        if preset_category is not None:
            # Встановлюємо конкретну категорію, якщо вона передана
            filters['category'] = preset_category
            
            # Оновлюємо фільтри
            context.user_data['transaction_filters'] = filters
            
            # Оновлюємо параметри для відображення транзакцій
            view_params = context.user_data.get('transactions_view', {})
            view_params['category_id'] = preset_category if preset_category != 'all' else None
            view_params['page'] = 1  # Скидаємо сторінку
            context.user_data['transactions_view'] = view_params
            
            # Показуємо оновлений екран фільтрів
            await show_transaction_filters(query, context)
        else:
            # Показуємо меню категорій з пагінацією
            await show_category_filter_menu(query, context, page=1)
    
    except Exception as e:
        logger.error(f"Error handling category filter: {str(e)}")
        await query.answer("Помилка при зміні фільтра категорії.")

async def show_privatbank_statement_form(query, context):
    """Показує сучасне, лаконічне меню для завантаження виписки з ПриватБанку з чітким описом кнопки."""
    context.user_data['selected_bank'] = 'privatbank'

    keyboard = [
        [InlineKeyboardButton("📊 Завантажити Excel виписку (.xlsx)", callback_data="privatbank_excel_guide")],
        [InlineKeyboardButton("◀️ Назад", callback_data="upload_statement")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "🏦 *ПриватБанк — імпорт виписки*\n\n"
        "Доступний лише формат Excel (.xlsx).\n\n"
        "Натисніть кнопку нижче, щоб отримати інструкцію та завантажити файл.\n\n"
        "Переваги Excel виписки:\n"
        "• Максимальна точність розпізнавання\n"
        "• Збереження категорій та типу операції\n"
        "• Автоматичний імпорт усіх даних\n\n"
        "Натисніть кнопку нижче, щоб продовжити:"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_monobank_statement_form(query, context):
    """Показує сучасне, лаконічне меню для завантаження виписки з МоноБанку з чітким описом кнопок."""
    context.user_data['selected_bank'] = 'monobank'

    keyboard = [
        [InlineKeyboardButton("📋 CSV виписка", callback_data="monobank_csv_guide")],
        [InlineKeyboardButton("📊 Excel (.xls/.xlsx)", callback_data="monobank_excel_guide")],
        [InlineKeyboardButton("📄 PDF виписка", callback_data="monobank_pdf_guide")],
        [InlineKeyboardButton("◀️ Назад", callback_data="upload_statement")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "🏦 *Виписка з Monobank*\n\n"
        "Оберіть формат виписки для завантаження:\n"
        "• 📋 CSV — швидко, детально, рекомендовано\n"
        "• 📊 Excel — зручно для перегляду\n"
        "• 📄 PDF — базова підтримка\n\n"
        "Як отримати файл у додатку Monobank:\n"
        "1️⃣ Відкрийте Monobank та оберіть картку\n"
        "2️⃣ Натисніть іконку виписки (справа вгорі)\n"
        "3️⃣ Виберіть період та формат (CSV, Excel або PDF)\n"
        "4️⃣ Надішліть файл у цей чат\n\n"
        "ℹ️ Не змінюйте структуру файлу. Максимальний розмір — 5 МБ."
    )

    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_period_filter_menu(query, context):
    """Показує меню вибору періоду для фільтрації транзакцій"""
    try:
        # Отримуємо поточні фільтри
        filters = context.user_data.get('transaction_filters', {})
        current_period = filters.get('period', 'month')
        
        # Створюємо кнопки для різних періодів
        keyboard = [
            [InlineKeyboardButton("📅 Сьогодні", callback_data="period_day")],
            [InlineKeyboardButton("📆 Поточний тиждень", callback_data="period_week")],
            [InlineKeyboardButton("📆 Поточний місяць", callback_data="period_month")],
            [InlineKeyboardButton("📅 Поточний рік", callback_data="period_year")],
            [InlineKeyboardButton("📊 Весь час", callback_data="period_all")],
            [InlineKeyboardButton("◀️ Назад до фільтрів", callback_data="transaction_filters")]
        ]
        
        # Відмічаємо поточний вибраний період
        period_texts = {
            'day': "Сьогодні",
            'week': "Цей тиждень",
            'month': "Цей місяць",
            'year': "Цей рік",
            'all': "Весь час"
        }
        
        # Відправляємо повідомлення з кнопками
        await query.edit_message_text(
            f"📅 *Виберіть період для фільтрації*\n\n"
            f"Поточний вибір: *{period_texts.get(current_period, 'Не вибрано')}*\n\n"
            f"Оберіть період з меню нижче:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    except Exception as e:
        logger.error(f"Error showing period filter menu: {str(e)}")
        await query.answer("Помилка при відображенні меню періодів.", show_alert=True)

async def show_type_filter_menu(query, context):
    """Показує меню вибору типу транзакції для фільтрації"""
    try:
        # Отримуємо поточні фільтри
        filters = context.user_data.get('transaction_filters', {})
        current_type = filters.get('type', 'all')
        
        # Створюємо кнопки для різних типів
        keyboard = [
            [InlineKeyboardButton("💰 Тільки доходи", callback_data="type_income")],
            [InlineKeyboardButton("💸 Тільки витрати", callback_data="type_expense")],
            [InlineKeyboardButton("📊 Всі транзакції", callback_data="type_all")],
            [InlineKeyboardButton("◀️ Назад до фільтрів", callback_data="transaction_filters")]
        ]
        
        # Відмічаємо поточний вибраний тип
        type_texts = {
            'income': "Тільки доходи",
            'expense': "Тільки витрати",
            'all': "Всі транзакції"
        }
        
        # Відправляємо повідомлення з кнопками
        await query.edit_message_text(
            f"💼 *Виберіть тип транзакцій для фільтрації*\n\n"
            f"Поточний вибір: *{type_texts.get(current_type, 'Не вибрано')}*\n\n"
            f"Оберіть тип з меню нижче:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    except Exception as e:
        logger.error(f"Error showing type filter menu: {str(e)}")
        await query.answer("Помилка при відображенні меню типів.", show_alert=True)

async def handle_view_single_transaction(query, context):
    """Показує детальну інформацію про транзакцію"""
    from database.db_operations import get_user, get_transaction_by_id
    
    try:
        # Витягуємо ID транзакції з callback_data
        transaction_id = int(query.data.split('_')[-1])
        
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("Користувач не знайдений.")
            return
        
        transaction = get_transaction_by_id(transaction_id, user.id)
        if not transaction:
            await query.answer("Транзакція не знайдена.", show_alert=True)
            return
        
        # Формуємо детальну інформацію про транзакцію
        date_str = transaction.transaction_date.strftime("%d.%m.%Y")
        type_icon = "🟢" if transaction.type.value == "income" else "🔴"
        type_name = "Дохід" if transaction.type.value == "income" else "Витрата"
        category_name = transaction.category_name if hasattr(transaction, 'category_name') and transaction.category_name else "Без категорії"
        category_icon = transaction.category_icon if hasattr(transaction, 'category_icon') and transaction.category_icon else "📋"
        description = transaction.description or "Без опису"
        
        # Визначаємо валюту користувача
        currency = user.currency or "UAH"
        currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
        
        # Форматуємо суму з правильним знаком
        amount_sign = "+" if transaction.type.value == "income" else ""
        amount_display = f"{amount_sign}{transaction.amount:,.0f} {currency_symbol}"
        
        text = (
            f"{type_icon} *{type_name}*\n\n"
            f"💰 **{amount_display}**\n"
            f"{category_icon} {category_name}\n"
            f"📅 {date_str}\n\n"
            f"📝 {description}"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✏️ Редагувати", callback_data=f"edit_transaction_{transaction_id}"),
                InlineKeyboardButton("🗑️ Видалити", callback_data=f"delete_transaction_{transaction_id}")
            ],
            [
                InlineKeyboardButton("◀️ Назад до списку", callback_data="view_all_transactions")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_view_single_transaction: {e}")
        await query.answer("Виникла помилка при завантаженні транзакції.", show_alert=True)

async def handle_monobank_excel_upload(query, context):
    """Обробляє завантаження Excel файлу від Monobank"""
    from database.db_operations import import_monobank_excel
    
    try:
        user_id = query.from_user.id
        
        # Перевіряємо, чи є файл для завантаження
        if 'uploaded_file' not in context.user_data:
            await query.answer("❌ Будь ласка, спочатку надішліть файл виписки.")
            return
        
        file_info = context.user_data['uploaded_file']
        file_id = file_info['file_id']
        file_name = file_info['file_name']
        file_size = file_info['file_size']
        
        # Підтверджуємо завантаження файлу
        await query.answer("📥 Завантаження файлу...")
        
        # Імпортуємо дані з Excel файлу
        result = import_monobank_excel(user_id, file_id, file_name, file_size)
        
        if result['success']:
            await query.answer("✅ Файл успішно завантажено та оброблено!")
            # Показуємо підсумок імпорту
            summary = result.get('summary', {})
            imported_count = summary.get('imported_count', 0)
            total_amount = summary.get('total_amount', 0)
            
            # Визначаємо валюту
            user = get_user(user_id)
            currency = user.currency or "UAH"
            currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
            
            text = (
                f"📊 *Імпорт з Monobank - Excel виписка*\n\n"
                f"✅ Успішно імпортовано транзакцій: {imported_count}\n"
                f"💰 Загальна сума: {total_amount:,.2f} {currency_symbol}\n\n"
                "Ви можете переглянути імпортовані транзакції у своєму списку транзакцій."
            )
            
            keyboard = [
                [InlineKeyboardButton("📊 Переглянути транзакції", callback_data="view_all_transactions")],
                [InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await query.answer("❌ Помилка при імпорті файлу.")
    
    except Exception as e:
        logger.error(f"Error in handle_monobank_excel_upload: {e}")
        await query.answer("Виникла помилка при обробці файлу.", show_alert=True)

async def show_monobank_excel_guide(query, context):
    """Сучасна інструкція для завантаження Excel виписки Monobank з чітким описом кнопки."""
    # Встановлюємо джерело файлу
    context.user_data['file_source'] = 'monobank'
    
    keyboard = [
        [InlineKeyboardButton("📤 Надіслати Excel файл", callback_data="start_excel_upload")],
        [InlineKeyboardButton("◀️ Назад", callback_data="select_bank_monobank")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "📊 *Monobank — Excel виписка*\n\n"
        "1️⃣ Завантажте Excel файл з додатку Monobank:\n"
        "• Відкрийте Monobank, оберіть картку\n"
        "• Натисніть іконку виписки (справа вгорі)\n"
        "• Виберіть період і формат Excel (.xls/.xlsx)\n"
        "• Надішліть файл у цей чат\n\n"
        "⚠️ Вимоги до файлу:\n"
        "• Формат: .xls або .xlsx\n"
        "• Не змінюйте структуру\n"
        "• Розмір до 10 МБ\n\n"
        "Після завантаження ви зможете переглянути та підтвердити транзакції.\n\n"
        "Натисніть кнопку нижче, щоб завантажити файл."
    )

    context.user_data['awaiting_file'] = 'excel'
    context.user_data['file_source'] = 'monobank'

    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_start_receipt_photo_upload(query, context):
    """Обробляє початок завантаження фото чеку"""
    # Встановлюємо стан очікування фото чеку
    context.user_data['awaiting_file'] = 'receipt_photo'
    context.user_data['receipt_step'] = 'waiting_photo'
    
    keyboard = [
        [InlineKeyboardButton("❌ Скасувати", callback_data="add_transaction")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📷 *Фото чеку — автоматичне розпізнавання*\n\n"
        "1️⃣ Сфотографуйте чек або завантажте з галереї\n"
        "2️⃣ Бот розпізнає суму, магазин та товари\n"
        "3️⃣ Підтвердьте дані та збережіть транзакцію\n\n"
        "⚡ *Що розпізнається:*\n"
        "• Загальна сума та дата покупки\n"
        "• Назва магазину\n"
        "• Список товарів (якщо можливо)\n\n"
        "💡 *Для кращого результату:*\n"
        "• Чіткий текст, хороше освітлення\n"
        "• Весь чек в кадрі, без відблисків\n\n"
        "Надішліть фото чеку зараз."
    )
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== АВТОМАТИЧНА КАТЕГОРИЗАЦІЯ ====================

async def process_transaction_input(update, context):
    """Обробляє введення суми та опису транзакції"""
    try:
        # Перевіряємо, чи очікуємо введення транзакції
        if not context.user_data.get('awaiting_transaction_input'):
            return
        
        user_input = update.message.text.strip()
        transaction_type = context.user_data.get('transaction_type')
        
        # Парсимо введення: сума + опис
        parts = user_input.split(' ', 1)
        if len(parts) < 1:
            await update.message.reply_text(
                "❌ Будь ласка, введіть суму.\n"
                "Приклад: 450 АТБ продукти"
            )
            return
        
        # Перевіряємо суму
        try:
            amount = float(parts[0].replace(',', '.'))
            if amount <= 0:
                await update.message.reply_text(
                    "❌ Сума повинна бути більше нуля.\n"
                    "Спробуйте ще раз:"
                )
                return
        except ValueError:
            await update.message.reply_text(
                "❌ Невірний формат суми.\n"
                "Приклад: 450 або 1500.50"
            )
            return
        
        # Отримуємо опис
        description = parts[1] if len(parts) > 1 else "Без опису"
        
        # Зберігаємо дані транзакції
        context.user_data['pending_transaction'] = {
            'amount': amount,
            'description': description,
            'type': transaction_type
        }
        
        # Очищуємо стан очікування
        context.user_data.pop('awaiting_transaction_input', None)
        
        # Виконуємо автоматичну категоризацію
        await perform_auto_categorization(update, context)
        
    except Exception as e:
        logger.error(f"Error in process_transaction_input: {e}")
        await update.message.reply_text("❌ Виникла помилка. Спробуйте ще раз.")

async def perform_auto_categorization(update, context):
    """Виконує автоматичну категоризацію транзакції використовуючи тільки існуючі категорії користувача"""
    try:
        from database.db_operations import get_user, get_user_categories, get_category_by_id
        from services.ml_categorizer import TransactionCategorizer
        
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Користувач не знайдений.")
            return
        
        transaction_data = context.user_data.get('pending_transaction')
        if not transaction_data:
            await update.message.reply_text("Дані транзакції не знайдені.")
            return
        
        # Отримуємо категорії користувача відповідного типу
        user_categories = get_user_categories(user.id, category_type=transaction_data['type'])
        
        if not user_categories:
            # Якщо у користувача немає категорій відповідного типу, пропонуємо створити їх
            type_text = "витрат" if transaction_data['type'] == 'expense' else "доходів"
            await update.message.reply_text(
                f"❌ *У вас немає категорій для {type_text}*\n\n"
                f"Спочатку створіть категорії через:\n"
                f"Головне меню → Налаштування → Категорії\n\n"
                f"Або скасуйте додавання транзакції командою /cancel",
                parse_mode="Markdown"
            )
            return
        
        # Конвертуємо категорії в потрібний формат
        formatted_categories = []
        for category in user_categories:
            formatted_categories.append({
                'id': category.id,
                'name': category.name,
                'icon': category.icon or ('💸' if transaction_data['type'] == 'expense' else '💰'),
                'type': transaction_data['type']
            })
        
        # Використовуємо ML категоризатор
        categorizer = TransactionCategorizer()
        
        # Тренуємо категоризатор на історії транзакцій користувача (якщо є)
        try:
            from database.db_operations import get_transactions
            user_transactions = get_transactions(user.id, limit=100)  # Останні 100 транзакцій
            if user_transactions:
                formatted_transactions = []
                for trans in user_transactions:
                    formatted_transactions.append({
                        'description': trans.description or '',
                        'category_id': trans.category_id,
                        'amount': float(trans.amount),
                        'type': trans.type.value if hasattr(trans.type, 'value') else str(trans.type)
                    })
                categorizer.train_on_user_transactions(formatted_transactions, formatted_categories)
        except Exception as e:
            logger.error(f"Error training categorizer on user history: {e}")
            # Продовжуємо без тренування
        
        # Отримуємо найкращу категорію для цієї транзакції
        suggested_category = categorizer.get_best_category_for_user(
            description=transaction_data['description'],
            amount=transaction_data['amount'],
            transaction_type=transaction_data['type'],
            user_categories=formatted_categories
        )
        
        if not suggested_category:
            # Fallback: використовуємо першу доступну категорію
            suggested_category = formatted_categories[0]
        
        # Визначаємо валюту користувача
        currency = user.currency or "UAH"
        currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
        
        # Формуємо повідомлення з результатом категоризації
        type_icon = "💸" if transaction_data['type'] == "expense" else "💰"
        amount_str = f"-{transaction_data['amount']:.0f}{currency_symbol}" if transaction_data['type'] == "expense" else f"+{transaction_data['amount']:.0f}{currency_symbol}"
        
        text = (
            f"🤖 *Я проаналізував вашу операцію:*\n\n"
            f"{type_icon} {amount_str} • {transaction_data['description']}\n"
            f"📍 *Автоматично віднесено до:* {suggested_category['icon']} {suggested_category['name']}\n\n"
            f"Це правильно?"
        )
        
        # Зберігаємо запропоновану категорію
        context.user_data['suggested_category'] = suggested_category
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Так", callback_data="confirm_auto_category"),
                InlineKeyboardButton("❌ Ні, змінити", callback_data="change_category")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in perform_auto_categorization: {e}")
        # Якщо автокатегоризація не працює, показуємо помилку та пропонуємо ручний ввід
        await update.message.reply_text(
            "❌ Не вдалося автоматично визначити категорію.\n"
            "Спробуйте ще раз або оберіть категорію вручну через головне меню."
        )

async def handle_confirm_auto_category(query, context):
    """Обробляє підтвердження автоматично обраної категорії"""
    try:
        transaction_data = context.user_data.get('pending_transaction')
        suggested_category = context.user_data.get('suggested_category')
        
        if not transaction_data or not suggested_category:
            await query.answer("Дані транзакції втрачено.", show_alert=True)
            return
        
        # Зберігаємо транзакцію в базу даних
        await save_transaction_to_db(query, context, suggested_category['id'])
        
    except Exception as e:
        logger.error(f"Error in handle_confirm_auto_category: {e}")
        await query.answer("Виникла помилка при збереженні.", show_alert=True)

async def handle_change_category(query, context):
    """Показує меню ручного вибору категорії"""
    try:
        transaction_data = context.user_data.get('pending_transaction')
        if not transaction_data:
            await query.answer("Дані транзакції втрачено.", show_alert=True)
            return
        
        from database.db_operations import get_user, get_user_categories
        
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("Користувач не знайдений.")
            return
        
        # Отримуємо категорії відповідного типу
        categories = get_user_categories(user.id, category_type=transaction_data['type'])
        
        if not categories:
            await query.edit_message_text(
                "📂 *У вас немає категорій*\n\n"
                "Спочатку створіть категорії через меню налаштувань.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="transaction_filters")]
                ]),
                parse_mode="Markdown"
            )
            return
        
        text = (
            f"🔄 *Оберіть правильну категорію:*\n\n"
            f"{'💸' if transaction_data['type'] == 'expense' else '💰'} "
            f"{transaction_data['amount']:.0f}₴ • {transaction_data['description']}"
        )
        
        keyboard = []
        current_category = None  # Поки що категорія не вибрана
        
        # Групуємо категорії по 2 в ряд для зручності
        for i in range(0, len(categories), 2):
            row = []
            for j in range(i, min(i + 2, len(categories))):
                category = categories[j]
                icon = category.icon or "📂"
                is_selected = current_category == category.id
                button_text = f"✅ {icon} {category.name}" if is_selected else f"{icon} {category.name}"
                row.append(InlineKeyboardButton(button_text, callback_data=f"select_manual_category_{category.id}"))
            keyboard.append(row)
        
        # Додаємо кнопку для скасування
        keyboard.append([
            InlineKeyboardButton("❌ Скасувати", callback_data="cancel_transaction")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_change_category: {e}")
        await query.answer("Виникла помилка.", show_alert=True)

async def handle_manual_category_selection(query, context):
    """Обробляє ручний вибір категорії та навчає ML категоризатор"""
    try:
        # Витягуємо ID категорії з callback_data
        category_id = int(query.data.split('_')[-1])
        
        # Навчаємо ML категоризатор на виправленій категоризації
        transaction_data = context.user_data.get('pending_transaction')
        if transaction_data:
            await improve_categorization_on_feedback(
                user_id=query.from_user.id,
                description=transaction_data['description'],
                correct_category_id=category_id,
                transaction_type=transaction_data['type']
            )
        
        # Зберігаємо транзакцію в базу даних
        await save_transaction_to_db(query, context, category_id)
        
    except Exception as e:
        logger.error(f"Error in handle_manual_category_selection: {e}")
        await query.answer("Виникла помилка при збереженні.", show_alert=True)

async def save_transaction_to_db(query, context, category_id):
    """Зберігає транзакцію в базу даних та навчає ML категоризатор"""
    try:
        from database.db_operations import get_user, add_transaction, get_category_by_id
        from database.models import TransactionType
        from services.ml_categorizer import TransactionCategorizer
        
        user = get_user(query.from_user.id)
        transaction_data = context.user_data.get('pending_transaction')
        
        if not user or not transaction_data:
            await query.answer("Дані не знайдені.", show_alert=True)
            return
        
        # Додамо логування для діагностики
        logger.info(f"Saving transaction: user_id={user.id}, category_id={category_id}, amount={transaction_data['amount']}, description={transaction_data['description']}")
        
        # Визначаємо тип транзакції
        transaction_type = TransactionType.EXPENSE if transaction_data['type'] == 'expense' else TransactionType.INCOME
        
        # Отримуємо ID вибраного рахунку
        selected_account_id = context.user_data.get('selected_account_id')
        
        # Зберігаємо транзакцію
        transaction = add_transaction(
            user_id=user.id,
            amount=transaction_data['amount'],
            description=transaction_data['description'],
            category_id=category_id,
            transaction_type=transaction_type,
            account_id=selected_account_id,
            source="manual"
        )
        
        if transaction:
            # Навчаємо ML категоризатор на цій транзакції
            try:
                category = get_category_by_id(category_id)
                if category:
                    categorizer = TransactionCategorizer()
                    
                    # Створюємо навчальні дані
                    training_transaction = [{
                        'description': transaction_data['description'],
                        'category_id': category_id,
                        'amount': transaction_data['amount'],
                        'type': transaction_data['type']
                    }]
                    
                    training_category = [{
                        'id': category.id,
                        'name': category.name,
                        'icon': category.icon or ('💸' if transaction_data['type'] == 'expense' else '💰'),
                        'type': transaction_data['type']
                    }]
                    
                    # Навчаємо категоризатор
                    categorizer.train_on_user_transactions(training_transaction, training_category)
                    logger.info(f"ML categorizer trained on new transaction: {transaction_data['description']} -> {category.name}")
            except Exception as e:
                logger.error(f"Error training ML categorizer: {e}")
                # Не критична помилка, продовжуємо
            
            # Отримуємо інформацію про категорію та рахунок для відображення
            category = get_category_by_id(category_id)
            
            # Отримуємо інформацію про рахунок
            account_info = ""
            if selected_account_id:
                from database.db_operations import get_user_accounts
                accounts = get_user_accounts(user.id)
                selected_account = next((acc for acc in accounts if acc.id == selected_account_id), None)
                if selected_account:
                    account_info = f"\n💳 {selected_account.icon or '💳'} {selected_account.name}"
            
            # Додамо логування для перевірки категорії
            logger.info(f"Retrieved category: id={category.id if category else None}, name={category.name if category else None}")
            
            # Визначаємо валюту
            currency = user.currency or "UAH"
            currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
            
            text = (
                f"✅ *Транзакцію додано!*\n\n"
                f"{'💸' if transaction_data['type'] == 'expense' else '💰'} {transaction_data['amount']:.0f}₴ • {transaction_data['description']}\n"
                f"📂 {category.icon or '📂'} {category.name}{account_info}\n\n"
                f"🤖 *ML категоризатор навчився!*\n"
                f"Наступного разу він краще розпізнаватиме схожі транзакції.\n\n"
                f"Що далі?"
            )
            
            keyboard = [
                [InlineKeyboardButton("➕ Додати ще", callback_data="add_transaction")],
                [
                    InlineKeyboardButton("📊 Мій бюджет", callback_data="my_budget_overview"),
                    InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            # Очищаємо тимчасові дані
            context.user_data.pop('pending_transaction', None)
            context.user_data.pop('suggested_category', None)
            context.user_data.pop('transaction_type', None)
            context.user_data.pop('selected_account_id', None)
            
        else:
            await query.answer("❌ Помилка при збереженні транзакції.", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error in save_transaction_to_db: {e}")
        await query.answer("Виникла помилка при збереженні.", show_alert=True)

async def handle_cancel_transaction(query, context):
    """Скасовує додавання транзакції"""
    try:
        # Очищуємо всі тимчасові дані
        context.user_data.pop('pending_transaction', None)
        context.user_data.pop('suggested_category', None)
        context.user_data.pop('transaction_type', None)
        context.user_data.pop('selected_account_id', None)
        context.user_data.pop('awaiting_transaction_input', None)
        
        keyboard = [
            [InlineKeyboardButton("➕ Спробувати знову", callback_data="add_transaction")],
            [InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ *Додавання транзакції скасовано*\n\n"
            "Ви можете спробувати ще раз або повернутися до головного меню.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_cancel_transaction: {e}")
        await query.answer("Виникла помилка.", show_alert=True)

async def show_category_filter_menu(query, context, page=1):
    """Показує меню вибору категорії з пагінацією"""
    try:
        from database.db_operations import get_user, get_user_categories
        
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("Користувач не знайдений.")
            return
        
        # Отримуємо поточні фільтри
        filters = context.user_data.get('transaction_filters', {})
        current_category = filters.get('category', 'all')
        
        # Отримуємо категорії користувача
        categories = get_user_categories(user.id)
        
        if not categories:
            await query.edit_message_text(
                "📂 *У вас немає категорій*\n\n"
                "Спочатку створіть категорії через меню налаштувань.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="transaction_filters")]
                ]),
                parse_mode="Markdown"
            )
            return
        
        # Розділяємо категорії на витрати та доходи
        from database.models import TransactionType
        expense_categories = [c for c in categories if c.type == TransactionType.EXPENSE.value]
        income_categories = [c for c in categories if c.type == TransactionType.INCOME.value]
        
        # Налаштування пагінації - використовуємо всі категорії для підрахунку
        per_page = 8  # Кількість категорій на сторінку
        total_categories = len(categories)
        total_pages = max(1, (total_categories + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        
        # Створюємо загальний список для пагінації (витрати + доходи)
        all_categories_for_pagination = expense_categories + income_categories
        
        # Отримуємо категорії для поточної сторінки
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_categories = all_categories_for_pagination[start_idx:end_idx]
        
        # Формуємо клавіатуру
        keyboard = []
        
        # Додаємо опцію "Всі категорії" тільки на першій сторінці
        if page == 1:
            all_button_text = "✅ Всі категорії" if current_category == 'all' else "📂 Всі категорії"
            keyboard.append([InlineKeyboardButton(all_button_text, callback_data="category_all")])
        
        # Розділяємо категорії на поточній сторінці за типом
        page_expense_categories = [c for c in page_categories if c.type == TransactionType.EXPENSE.value]
        page_income_categories = [c for c in page_categories if c.type == TransactionType.INCOME.value]
        
        # Додаємо категорії витрат
        if page_expense_categories:
            # Додаємо заголовок секції витрат
            keyboard.append([InlineKeyboardButton("💸 ── ВИТРАТИ ──", callback_data="noop_header")])
            
            # Додаємо кнопки витрат по 2 в ряд
            current_section_expenses = []
            for category in page_expense_categories:
                icon = category.icon or "💸"
                is_selected = current_category == category.id
                button_text = f"✅ {icon} {category.name}" if is_selected else f"{icon} {category.name}"
                current_section_expenses.append((button_text, f"category_{category.id}"))
            
            for i in range(0, len(current_section_expenses), 2):
                row = []
                for j in range(i, min(i + 2, len(current_section_expenses))):
                    button_text, callback_data = current_section_expenses[j]
                    row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
                keyboard.append(row)
        
        # Додаємо категорії доходів
        if page_income_categories:
            # Додаємо заголовок секції доходів (тільки якщо є витрати, інакше це перша секція)
            if page_expense_categories:
                keyboard.append([InlineKeyboardButton("💰 ── ДОХОДИ ──", callback_data="noop_header")])
            else:
                keyboard.append([InlineKeyboardButton("💰 ── ДОХОДИ ──", callback_data="noop_header")])
            
            # Додаємо кнопки доходів по 2 в ряд
            current_section_incomes = []
            for category in page_income_categories:
                icon = category.icon or "💰"
                is_selected = current_category == category.id
                button_text = f"✅ {icon} {category.name}" if is_selected else f"{icon} {category.name}"
                current_section_incomes.append((button_text, f"category_{category.id}"))
            
            for i in range(0, len(current_section_incomes), 2):
                row = []
                for j in range(i, min(i + 2, len(current_section_incomes))):
                    button_text, callback_data = current_section_incomes[j]
                    row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
                keyboard.append(row)
        
        # Додаємо кнопи навігації, якщо потрібно
        if total_pages > 1:
            nav_buttons = []
            
            if page > 1:
                nav_buttons.append(InlineKeyboardButton("⬅️ Попередні", callback_data=f"category_page_{page-1}"))
            
            if page < total_pages:
                nav_buttons.append(InlineKeyboardButton("Наступні ➡️", callback_data=f"category_page_{page+1}"))
            
            if nav_buttons:  # Додаємо кнопи тільки якщо вони є
                keyboard.append(nav_buttons)
        
        # Додаємо кнопку назад
        keyboard.append([InlineKeyboardButton("◀️ Назад до фільтрів", callback_data="transaction_filters")])
        
        # Визначаємо назву поточної категорії для відображення
        current_category_name = "Всі категорії"
        if current_category != 'all' and isinstance(current_category, int):
            category_obj = next((c for c in categories if c.id == current_category), None)
            if category_obj:
                current_category_name = f"{category_obj.icon or '📂'} {category_obj.name}"
        
        # Формуємо текст повідомлення
        text = (
            f"📂 *Оберіть категорію для фільтра*\n\n"
            f"Поточний вибір: *{current_category_name}*\n\n"
        )
        
        if total_pages > 1:
            text += f"Сторінка {page} з {total_pages} | Всього категорій: {total_categories}\n"
        
        # Додаємо інформацію про кількість категорій за типами
        expenses_count = len(expense_categories)
        incomes_count = len(income_categories)
        text += f"💸 Витрати: {expenses_count} | 💰 Доходи: {incomes_count}\n\n"
        
        text += "Оберіть категорію зі списку:"
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Зберігаємо поточну сторінку
        context.user_data['category_filter_page'] = page
        
    except Exception as e:
        logger.error(f"Error showing category filter menu: {str(e)}")
        await query.answer("Помилка при відображенні меню категорій.")

async def handle_category_page_navigation(query, context):
    """Обробляє навігацію по сторінках категорій"""
    try:
        # Витягуємо номер сторінки з callback_data
        page = int(query.data.split('_')[-1])
        
        # Показуємо меню категорій з відповідною сторінкою
        await show_category_filter_menu(query, context, page=page)
        
    except Exception as e:
        logger.error(f"Error handling category page navigation: {str(e)}")
        await query.answer("Помилка при навігації по категоріях.")

async def handle_category_selection_for_filter(query, context):
    """Обробляє вибір категорії для фільтра"""
    try:
        # Витягуємо ID категорії з callback_data
        if query.data == "category_all":
            category_id = 'all'
        else:
            category_id = int(query.data.split('_')[1])
        
        # Використовуємо існуючу функцію для встановлення фільтра
        await handle_category_filter(query, context, preset_category=category_id)
        
    except Exception as e:
        logger.error(f"Error handling category selection: {str(e)}")
        await query.answer("Помилка при виборі категорії.")

async def handle_edit_date(query, context):
    """Обробляє редагування дати транзакції"""
    try:
        # Витягуємо ID транзакції з callback_data
        transaction_id = int(query.data.split('_')[2])
        
        # Зберігаємо ID транзакції та поле для редагування
        context.user_data['editing_transaction_id'] = transaction_id
        context.user_data['editing_field'] = 'date_manual'
        
        keyboard = [
            [InlineKeyboardButton("❌ Скасувати", callback_data=f"edit_transaction_{transaction_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📅 *Редагування дати транзакції*\n\n"
            "Введіть нову дату у форматі:\n"
            "• ДД.ММ.РРРР (наприклад: 25.06.2025)\n"
            "• ДД.ММ (для 2025 року)\n"
            "• ДД (для поточного місяця)\n\n"
            "Або напишіть /cancel для скасування.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_edit_date: {e}")
        await query.answer("Помилка при редагуванні дати.", show_alert=True)

async def handle_set_date(query, context):
    """Обробляє встановлення нової дати для транзакції (залишається для сумісності)"""
    # Ця функція більше не використовується, оскільки користувач одразу вводить дату вручну
    # Залишена для сумісності з існуючими callback'ами
    try:
        await query.answer("Будь ласка, введіть дату у чаті.", show_alert=True)
    except Exception as e:
        logger.error(f"Error in handle_set_date: {e}")
        await query.answer("Помилка.", show_alert=True)

async def handle_edit_type(query, context):
    """Обробляє редагування типу транзакції"""
    try:
        # Витягуємо ID транзакції
        transaction_id = int(query.data.split('_')[2])
        
        # Зберігаємо ID транзакції для подальшого використання
        context.user_data['editing_transaction_id'] = transaction_id
        
        keyboard = [
            [InlineKeyboardButton("💰 Змінити на дохід", callback_data=f"set_type_{transaction_id}_income")],
            [InlineKeyboardButton("💸 Змінити на витрату", callback_data=f"set_type_{transaction_id}_expense")],
            [InlineKeyboardButton("◀️ Назад", callback_data=f"edit_transaction_{transaction_id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔄 *Редагування типу операції*\n\n"
            "Оберіть новий тип для цієї транзакції:\n\n"
            "💰 **Дохід** — зарплата, премії, повернення коштів\n"
            "💸 **Витрата** — покупки, оплати, послуги\n\n"
            "⚠️ **Увага:** При зміні типу операції буде потрібно також вибрати нову категорію.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_edit_type: {e}")
        await query.answer("Помилка при редагуванні типу операції.", show_alert=True)

async def handle_set_type(query, context):
    """Обробляє встановлення нового типу для транзакції"""
    from database.db_operations import get_user, get_transaction_by_id, update_transaction, get_user_categories
    from database.models import TransactionType
    
    try:
        # Парсимо callback_data
        parts = query.data.split('_')
        
        transaction_id = int(parts[2])
        new_type = parts[3]  # 'income' або 'expense'
        
        # Отримуємо транзакцію
        user = get_user(query.from_user.id)
        if not user:
            await query.answer("Користувач не знайдений.", show_alert=True)
            return
            
        transaction = get_transaction_by_id(transaction_id, user.id)
        if not transaction:
            await query.answer("Транзакція не знайдена.", show_alert=True)
            return
        
        # Конвертуємо тип
        new_transaction_type = TransactionType.INCOME if new_type == 'income' else TransactionType.EXPENSE
        
        # Перевіряємо, чи змінився тип
        current_type_value = transaction.type.value if hasattr(transaction.type, 'value') else str(transaction.type)
        if current_type_value == new_type:
            logger.info(f"Тип операції {current_type_value} вже встановлено правильно для транзакції {transaction_id}")
            await query.answer("Тип операції вже встановлено правильно.", show_alert=True)
            
            # Повертаємося до меню редагування транзакції напряму
            date_str = transaction.transaction_date.strftime("%d.%m.%Y %H:%M")
            type_icon = "💸" if transaction.type.value == "expense" else "💰"
            type_name = "Витрата" if transaction.type.value == "expense" else "Дохід"
            category_name = transaction.category_name if hasattr(transaction, 'category_name') and transaction.category_name else "Без категорії"
            description = transaction.description or "Без опису"
            
            text = f"🔧 <b>Редагування транзакції</b>\n\n"
            text += f"📅 <b>Дата:</b> {date_str}\n"
            text += f"{type_icon} <b>Тип:</b> {type_name}\n"
            text += f"📂 <b>Категорія:</b> {category_name}\n"
            text += f"💰 <b>Сума:</b> {transaction.amount:.2f} грн\n"
            text += f"📝 <b>Опис:</b> {description}\n\n"
            text += "Що ви хочете змінити?"
            
            keyboard = [
                [InlineKeyboardButton("📅 Дата", callback_data=f"edit_date_{transaction.id}")],
                [InlineKeyboardButton("📂 Категорія", callback_data=f"change_category_{transaction.id}")],
                [InlineKeyboardButton(f"{type_icon} Тип", callback_data=f"edit_type_{transaction.id}")],
                [InlineKeyboardButton("💰 Сума", callback_data=f"edit_amount_{transaction.id}")],
                [InlineKeyboardButton("📝 Опис", callback_data=f"edit_description_{transaction.id}")],
                [InlineKeyboardButton("🗑️ Видалити", callback_data=f"delete_transaction_{transaction.id}")],
                [InlineKeyboardButton("🔙 Назад", callback_data=f"view_transaction_{transaction.id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
            logger.info(f"Повернулися до меню редагування транзакції {transaction_id}")
            return
            return
        
        # Отримуємо категорії нового типу
        categories = get_user_categories(user.id, category_type=new_type)
        
        if not categories:
            # Якщо немає категорій відповідного типу, попереджаємо користувача
            type_text = "доходів" if new_type == "income" else "витрат"
            await query.edit_message_text(
                f"❌ *Немає категорій для {type_text}*\n\n"
                f"Спочатку створіть категорії для {type_text} у розділі 'Налаштування' → 'Категорії'.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data=f"edit_transaction_{transaction_id}")]
                ]),
                parse_mode="Markdown"
            )
            return
        
        # Зберігаємо новий тип та ID транзакції для вибору категорії
        context.user_data['editing_transaction_id'] = transaction_id
        context.user_data['new_transaction_type'] = new_type
        
        # Показуємо категорії для вибору
        type_text = "доходу" if new_type == "income" else "витрати"
        type_icon = "💰" if new_type == "income" else "💸"
        
        text = (
            f"🔄 *Зміна типу на {type_text}*\n\n"
            f"{type_icon} Тип операції буде змінено на **{type_text}**.\n\n"
            f"📂 Оберіть категорію для цього типу операції:"
        )
        
        keyboard = []
        for category in categories:
            icon = category.icon or "💰"
            keyboard.append([
                InlineKeyboardButton(
                    f"{icon} {category.name}", 
                    callback_data=f"confirm_type_change_{transaction_id}_{new_type}_{category.id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("◀️ Назад", callback_data=f"edit_type_{transaction_id}")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_set_type: {e}")
        await query.answer("Помилка при встановленні типу операції.", show_alert=True)

async def handle_confirm_type_change(query, context):
    """Підтверджує зміну типу та категорії транзакції"""
    from database.db_operations import update_transaction, get_transaction_by_id, get_user
    from database.models import TransactionType
    
    try:
        logger.info(f"handle_confirm_type_change called with callback_data: {query.data}")
        
        # Парсимо callback_data: confirm_type_change_{transaction_id}_{new_type}_{category_id}
        parts = query.data.split('_')
        logger.info(f"Parsed parts: {parts}")
        
        transaction_id = int(parts[3])
        new_type = parts[4]
        category_id = int(parts[5]);
        
        logger.info(f"Transaction ID: {transaction_id}, New type: {new_type}, Category ID: {category_id}")
        
        # Отримуємо поточну транзакцію для перевірки типу
        user = get_user(query.from_user.id)
        if not user:
            logger.error("User not found")
            await query.answer("Користувач не знайдений.", show_alert=True)
            return
            
        transaction = get_transaction_by_id(transaction_id, user.id)
        if not transaction:
            logger.error("Transaction not found")
            await query.answer("Транзакція не знайдена.", show_alert=True)
            return
        
        logger.info(f"Current transaction: ID={transaction.id}, type={transaction.type}, amount={transaction.amount}")
        
        # Конвертуємо тип
        new_transaction_type = TransactionType.INCOME if new_type == 'income' else TransactionType.EXPENSE
        current_type = transaction.type.value if hasattr(transaction.type, 'value') else str(transaction.type)
        
        logger.info(f"Current type: {current_type}, New type: {new_transaction_type}")
        
        # Визначаємо нову суму (змінюємо знак при зміні типу)
        current_amount = transaction.amount
        new_amount = current_amount
        
        # Логіка зміни знаку суми при зміні типу
        if current_type != new_type:
            if new_type == 'income' and current_amount < 0:
                # Змінюємо з витрати на дохід: робимо суму позитивною
                new_amount = abs(current_amount)
                logger.info(f"Changed amount from {current_amount} to {new_amount} (expense to income)")
            elif new_type == 'expense' and current_amount > 0:
                # Змінюємо з доходу на витрату: робимо суму негативною
                new_amount = -abs(current_amount)
                logger.info(f"Changed amount from {current_amount} to {new_amount} (income to expense)")
        
        # Оновлюємо транзакцію з новим типом, категорією та сумою
        logger.info(f"Calling update_transaction with params: transaction_id={transaction_id}, user_id={user.id}, type={new_transaction_type}, category_id={category_id}, amount={new_amount}")
        
        success = update_transaction(
            transaction_id, 
            user.id,  # Використовуємо внутрішній ID користувача
            type=new_transaction_type,
            category_id=category_id,
            amount=new_amount
        )
        
        logger.info(f"Update result: {success}")
        
        if success:
            type_text = "дохід" if new_type == "income" else "витрата"
            await query.answer(f"✅ Тип операції змінено на '{type_text}'", show_alert=True)
            
            # Очищуємо тимчасові дані
            context.user_data.pop('editing_transaction_id', None)
            context.user_data.pop('new_transaction_type', None)
            
            logger.info("Calling handle_edit_single_transaction...")
            
            # Створюємо фейковий query object з правильним callback_data
            class FakeQuery:
                def __init__(self, data, from_user, edit_message_text, answer):
                    self.data = data
                    self.from_user = from_user
                    self.edit_message_text = edit_message_text
                    self.answer = answer
            
            fake_query = FakeQuery(
                data=f"edit_transaction_{transaction_id}",
                from_user=query.from_user,
                edit_message_text=query.edit_message_text,
                answer=query.answer
            )
            
            # Повертаємося до меню редагування транзакції
            await handle_edit_single_transaction(fake_query, context)
        else:
            logger.error("Failed to update transaction")
            await query.answer("❌ Помилка при оновленні типу операції.", show_alert=True)
        
    except Exception as e:
        logger.error(f"Error in handle_confirm_type_change: {e}")
        await query.answer("Помилка при підтвердженні зміни типу.", show_alert=True)

async def improve_categorization_on_feedback(user_id: int, description: str, correct_category_id: int, transaction_type: str):
    """
    Покращує категоризацію на основі зворотного зв'язку користувача
    """
    try:
        from database.db_operations import get_user, get_user_categories, get_category_by_id
        from services.ml_categorizer import TransactionCategorizer
        
        user = get_user(user_id)
        if not user:
            return False
        
        # Отримуємо правильну категорію
        correct_category = get_category_by_id(correct_category_id)
        if not correct_category:
            return False
        
        # Отримуємо всі категорії користувача цього типу
        user_categories = get_user_categories(user.id, category_type=transaction_type)
        formatted_categories = []
        for category in user_categories:
            formatted_categories.append({
                'id': category.id,
                'name': category.name,
                'icon': category.icon or ('💸' if transaction_type == 'expense' else '💰'),
                'type': transaction_type
            })
        
        # Створюємо навчальні дані з виправленої категоризації
        training_data = [{
            'description': description,
            'category_id': correct_category_id,
            'amount': 0,  # Сума не важлива для навчання на тексті
            'type': transaction_type
        }]
        
        # Навчаємо категоризатор
        categorizer = TransactionCategorizer()
        success = categorizer.train_on_user_transactions(training_data, formatted_categories)
        
        logger.info(f"Improved categorization for user {user_id}: '{description}' -> '{correct_category.name}' (success: {success})")
        return success
        
    except Exception as e:
        logger.error(f"Error improving categorization on feedback: {e}")
        return False

# ==================== ОБРОБНИКИ ДЛЯ РОЗШИРЕНОГО ІНТЕРФЕЙСУ ДОДАВАННЯ ТРАНЗАКЦІЙ ====================

async def handle_account_selection(query, context):
    """Обробляє вибір рахунку та переходить до введення суми та опису"""
    try:
        # Витягуємо ID рахунку з callback_data
        account_id = int(query.data.split('_')[-1])
        
        # Зберігаємо ID рахунку
        context.user_data['selected_account_id'] = account_id
        
        # Отримуємо тип транзакції
        transaction_type = context.user_data.get('transaction_type')
        if not transaction_type:
            await query.answer("Помилка: тип транзакції не встановлено.", show_alert=True)
            return
        
        # Встановлюємо стан очікування введення транзакції
        context.user_data['awaiting_transaction_input'] = True
        
        # Отримуємо інформацію про рахунок для відображення
        from database.db_operations import get_user, get_user_accounts
        user = get_user(query.from_user.id)
        if user:
            accounts = get_user_accounts(user.id)
            selected_account = next((acc for acc in accounts if acc.id == account_id), None)
            
            if selected_account:
                account_info = f"{selected_account.icon or '💳'} {selected_account.name}"
            else:
                account_info = "Обраний рахунок"
        else:
            account_info = "Обраний рахунок"
        
        type_icon = "💸" if transaction_type == "expense" else "💰"
        type_text = "витрати" if transaction_type == "expense" else "доходу"
        
        keyboard = [
            [InlineKeyboardButton("❌ Скасувати", callback_data="cancel_transaction")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            f"{type_icon} *Додавання {type_text}*\n\n"
            f"💳 **Рахунок:** {account_info}\n\n"
            f"💰 **Введіть суму та опис:**\n"
            f"Напишіть повідомлення у форматі:\n"
            f"`450 АТБ продукти`\n"
            f"`1500 зарплата`\n"
            f"`200 кафе з друзями`\n\n"
            f"Перше число — сума, далі — опис операції."
        )
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_account_selection: {e}")
        await query.answer("Помилка при виборі рахунку.", show_alert=True)

async def show_account_selection(query, context, transaction_type):
    """Показує список рахунків для вибору перед додаванням транзакції"""
    try:
        from database.db_operations import get_user, get_user_accounts
        
        user = get_user(query.from_user.id)
        if not user:
            await query.answer("Користувач не знайдений.", show_alert=True)
            return
        
        # Зберігаємо тип транзакції
        context.user_data['transaction_type'] = transaction_type
        
        # Отримуємо рахунки користувача
        accounts = get_user_accounts(user.id)
        
        if not accounts:
            # Якщо рахунків немає, пропонуємо створити
            keyboard = [
                [InlineKeyboardButton("➕ Створити рахунок", callback_data="create_account")],
                [InlineKeyboardButton("◀️ Назад", callback_data="manual_transaction_type")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ *У вас немає створених рахунків*\n\n"
                "Для додавання транзакцій потрібно створити хоча б один рахунок.\n\n"
                "Створіть рахунок або поверніться назад.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        # Створюємо кнопки для кожного рахунку
        keyboard = []
        for account in accounts:
            icon = account.icon or '💳'
            balance_text = f"{account.balance:.0f} {account.currency}"
            main_text = " ⭐" if account.is_main else ""
            
            button_text = f"{icon} {account.name} - {balance_text}{main_text}"
            callback_data = f"select_account_{account.id}"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Додаємо кнопку "Назад"
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="manual_transaction_type")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        type_icon = "💸" if transaction_type == "expense" else "💰"
        type_text = "витрати" if transaction_type == "expense" else "доходу"
        
        text = (
            f"{type_icon} *Додавання {type_text}*\n\n"
            f"💳 **Оберіть рахунок:**\n"
            f"Виберіть рахунок, з якого буде списана сума або на який буде зарахований дохід."
        )
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_account_selection: {e}")
        await query.answer("Помилка при показі рахунків.", show_alert=True)
