"""
Модуль налаштувань для бота FinAssist.
MVP версія з базовими функціями: управління категоріями, валюта, експорт даних, очищення.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import csv
import io
import tempfile
import os
import logging

from database.db_operations import (
    get_user, get_user_categories, get_user_transactions,
    update_user_settings
)
from database.models import Session, User, Category, Transaction, TransactionType

logger = logging.getLogger(__name__)

# ==================== ГОЛОВНЕ МЕНЮ НАЛАШТУВАНЬ ====================

async def show_settings_menu(query, context):
    """Показує головне меню налаштувань"""
    try:
        keyboard = [
            [
                InlineKeyboardButton("🏷️ Категорії", callback_data="settings_categories"),
                InlineKeyboardButton("💱 Основна валюта", callback_data="settings_currency")
            ],
            [
                InlineKeyboardButton("📤 Експорт даних", callback_data="settings_export"),
                InlineKeyboardButton("🗑️ Очистити дані", callback_data="settings_clear_data")
            ],
            [
                InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")
            ]
        ]
        
        text = (
            "⚙️ **Налаштування FinAssist**\n\n"
            "Керуйте своїм профілем та даними:\n\n"
            "🏷️ *Категорії* — управління вашими категоріями транзакцій\n"
            "💱 *Основна валюта* — вибір валюти для відображення\n"
            "📤 *Експорт даних* — завантаження ваших транзакцій\n"
            "🗑️ *Очистити дані* — видалення всіх транзакцій\n\n"
            "💡 *Підказка:* Всі зміни зберігаються автоматично"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_settings_menu: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні налаштувань",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")]])
        )

# ==================== УПРАВЛІННЯ КАТЕГОРІЯМИ ====================

async def show_categories_management(query, context):
    """Показує меню управління категоріями"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Отримуємо категорії користувача
        expense_categories = get_user_categories(user.id, TransactionType.EXPENSE)
        income_categories = get_user_categories(user.id, TransactionType.INCOME)
        
        text = "🏷️ **Категорії**\n\n"
        
        # Показуємо категорії витрат
        if expense_categories:
            text += "💸 *Категорії витрат:*\n"
            for cat in expense_categories[:8]:  # Показуємо перші 8
                icon = getattr(cat, 'icon', '💸')
                text += f"• {icon} {cat.name}\n"
            if len(expense_categories) > 8:
                text += f"... та ще {len(expense_categories) - 8}\n"
        else:
            text += "💸 *Категорії витрат:* відсутні\n"
        
        text += "\n"
        
        # Показуємо категорії доходів
        if income_categories:
            text += "💰 *Категорії доходів:*\n"
            for cat in income_categories[:5]:  # Показуємо перші 5
                icon = getattr(cat, 'icon', '💰')
                text += f"• {icon} {cat.name}\n"
            if len(income_categories) > 5:
                text += f"... та ще {len(income_categories) - 5}\n"
        else:
            text += "💰 *Категорії доходів:* відсутні\n"
        
        keyboard = [
            [
                InlineKeyboardButton("➕ Додати категорію", callback_data="add_category"),
                InlineKeyboardButton("📋 Всі категорії", callback_data="view_all_categories")
            ],
            [
                InlineKeyboardButton("🗑️ Видалити категорію", callback_data="delete_category_select"),
                InlineKeyboardButton("✏️ Редагувати", callback_data="edit_category_select")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="settings")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_categories_management: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні категорій",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings")]])
        )

async def show_add_category_menu(query, context):
    """Показує меню додавання категорії"""
    keyboard = [
        [
            InlineKeyboardButton("💸 Категорія витрат", callback_data="add_category_expense"),
            InlineKeyboardButton("💰 Категорія доходів", callback_data="add_category_income")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="settings_categories")
        ]
    ]
    
    text = (
        "➕ **Додати нову категорію**\n\n"
        "Виберіть тип категорії:\n\n"
        "💸 *Категорія витрат* — для класифікації ваших трат\n"
        "💰 *Категорія доходів* — для типів надходжень\n\n"
        "💡 *Підказка:* Після вибору типу введіть назву категорії"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_delete_category_select(query, context):
    """Показує список категорій для видалення"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Отримуємо всі категорії користувача
        all_categories = get_user_categories(user.id)
        user_categories = [cat for cat in all_categories if not cat.is_default]
        
        if not user_categories:
            text = (
                "🗑️ **Видалення категорій**\n\n"
                "У вас немає категорій, які можна видалити.\n"
                "Системні категорії видаляти не можна."
            )
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="settings_categories")]]
        else:
            text = "🗑️ **Оберіть категорію для видалення:**\n\n"
            
            keyboard = []
            for cat in user_categories[:10]:  # Показуємо максимум 10
                icon = getattr(cat, 'icon', '🏷️')
                type_emoji = "💸" if cat.type == TransactionType.EXPENSE else "💰"
                button_text = f"{type_emoji} {icon} {cat.name}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"confirm_delete_cat_{cat.id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="settings_categories")])
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_delete_category_select: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні категорій",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings_categories")]])
        )

async def confirm_delete_category(query, context, category_id):
    """Підтвердження видалення категорії"""
    try:
        session = Session()
        category = session.query(Category).filter(Category.id == category_id).first()
        
        if not category:
            await query.edit_message_text("❌ Категорія не знайдена")
            session.close()
            return
        
        # Перевіряємо, чи є транзакції з цією категорією
        transactions_count = session.query(Transaction).filter(Transaction.category_id == category_id).count()
        
        text = (
            f"⚠️ **Підтвердження видалення**\n\n"
            f"Ви дійсно хочете видалити категорію:\n"
            f"**{category.name}**?\n\n"
        )
        
        if transactions_count > 0:
            text += f"⚠️ *Увага:* З цією категорією пов'язано {transactions_count} транзакцій.\n"
            text += "Після видалення категорії транзакції залишаться, але без категорії.\n\n"
        
        text += "❗ *Ця дія незворотна!*"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Так, видалити", callback_data=f"delete_cat_confirmed_{category_id}"),
                InlineKeyboardButton("❌ Скасувати", callback_data="delete_category_select")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        session.close()
        
    except Exception as e:
        logger.error(f"Error in confirm_delete_category: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при підтвердженні видалення",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings_categories")]])
        )

async def delete_category_confirmed(query, context, category_id):
    """Виконує видалення категорії"""
    try:
        session = Session()
        category = session.query(Category).filter(Category.id == category_id).first()
        
        if not category:
            await query.edit_message_text("❌ Категорія не знайдена")
            session.close()
            return
        
        category_name = category.name
        
        # Видаляємо категорію
        session.delete(category)
        session.commit()
        session.close()
        
        text = (
            f"✅ **Категорія видалена**\n\n"
            f"Категорія **{category_name}** успішно видалена."
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔙 До категорій", callback_data="settings_categories"),
                InlineKeyboardButton("🏠 Головне меню", callback_data="back_to_main")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in delete_category_confirmed: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при видаленні категорії",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings_categories")]])
        )

# ==================== НАЛАШТУВАННЯ ВАЛЮТИ ====================

async def show_currency_settings(query, context):
    """Показує налаштування валюти"""
    try:
        user = get_user(query.from_user.id)
        current_currency = getattr(user, 'currency', 'UAH') if user else 'UAH'
        
        currencies = [
            ('UAH', '🇺🇦', 'Українська гривня'),
            ('USD', '🇺🇸', 'Долар США'),
            ('EUR', '🇪🇺', 'Євро'),
            ('PLN', '🇵🇱', 'Польський злотий'),
            ('GBP', '🇬🇧', 'Британський фунт')
        ]
        
        text = (
            f"💱 **Налаштування валюти**\n\n"
            f"Поточна валюта: **{current_currency}**\n\n"
            "Оберіть основну валюту для відображення сум:"
        )
        
        keyboard = []
        for code, flag, name in currencies:
            status = " ✅" if code == current_currency else ""
            button_text = f"{flag} {code} - {name}{status}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"set_currency_{code}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="settings")])
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_currency_settings: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні налаштувань валюти",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings")]])
        )

async def set_currency(query, context, currency_code):
    """Встановлює нову валюту"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Оновлюємо валюту користувача
        update_user_settings(query.from_user.id, currency=currency_code)
        
        currencies_map = {
            'UAH': ('🇺🇦', 'Українська гривня'),
            'USD': ('🇺🇸', 'Долар США'),
            'EUR': ('🇪🇺', 'Євро'),
            'PLN': ('🇵🇱', 'Польський злотий'),
            'GBP': ('🇬🇧', 'Британський фунт')
        }
        
        flag, name = currencies_map.get(currency_code, ('💱', currency_code))
        
        text = (
            f"✅ **Валюта змінена**\n\n"
            f"Тепер основна валюта: {flag} **{currency_code}** ({name})\n\n"
            f"Всі суми будуть відображатися у {currency_code}."
        )
        
        keyboard = [
            [
                InlineKeyboardButton("💱 Змінити валюту", callback_data="settings_currency"),
                InlineKeyboardButton("⚙️ Налаштування", callback_data="settings")
            ],
            [
                InlineKeyboardButton("🏠 Головне меню", callback_data="back_to_main")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in set_currency: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при зміні валюти",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings_currency")]])
        )

# ==================== ЕКСПОРТ ДАНИХ ====================

async def show_export_menu(query, context):
    """Показує меню експорту даних"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Підраховуємо кількість транзакцій
        transactions = get_user_transactions(user.id, limit=None)
        transactions_count = len(transactions) if transactions else 0
        
        text = (
            f"📤 **Експорт даних**\n\n"
            f"У вас є **{transactions_count}** транзакцій для експорту.\n\n"
            "Доступні формати:\n"
            "📊 *CSV* — таблиця для Excel/Google Sheets\n\n"
            "📋 *Що включається в експорт:*\n"
            "• Дата та час транзакції\n"
            "• Тип (дохід/витрата)\n"
            "• Сума та валюта\n"
            "• Категорія\n"
            "• Опис\n"
            "• Джерело (ручне/імпорт)\n\n"
            "💡 *Підказка:* Файл буде надісланий у цей чат"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Завантажити CSV", callback_data="export_csv"),
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="settings")
            ]
        ]
        
        if transactions_count == 0:
            keyboard[0] = [InlineKeyboardButton("📊 Немає даних для експорту", callback_data="no_data")]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_export_menu: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні експорту",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings")]])
        )

async def export_csv(query, context):
    """Експортує дані в CSV формат"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Показуємо повідомлення про обробку
        await query.edit_message_text("⏳ Підготовка файлу для завантаження...")
        
        # Отримуємо всі транзакції
        transactions = get_user_transactions(user.id, limit=None)
        
        if not transactions:
            await query.edit_message_text(
                "📭 **Немає даних для експорту**\n\nУ вас поки що немає транзакцій.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings_export")]])
            )
            return
        
        # Створюємо CSV файл в пам'яті
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow([
            'Дата', 'Час', 'Тип', 'Сума', 'Валюта', 'Категорія', 'Опис', 'Джерело'
        ])
        
        # Додаємо дані
        for transaction in transactions:
            date_str = transaction.transaction_date.strftime('%Y-%m-%d')
            time_str = transaction.transaction_date.strftime('%H:%M:%S')
            type_str = 'Дохід' if transaction.type == TransactionType.INCOME else 'Витрата'
            currency = getattr(user, 'currency', 'UAH')
            category_name = transaction.category.name if transaction.category else 'Без категорії'
            source = transaction.source or 'manual'
            
            writer.writerow([
                date_str,
                time_str,
                type_str,
                transaction.amount,
                currency,
                category_name,
                transaction.description,
                source
            ])
        
        # Підготовлюємо файл для відправки
        csv_content = output.getvalue()
        output.close()
        
        # Створюємо тимчасовий файл
        filename = f"finassist_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Конвертуємо в bytes для Telegram
        csv_bytes = csv_content.encode('utf-8-sig')  # BOM для правильного відображення в Excel
        
        # Відправляємо файл
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=io.BytesIO(csv_bytes),
            filename=filename,
            caption=f"📊 **Ваші транзакції**\n\nЗавантажено {len(transactions)} транзакцій\nФормат: CSV (Excel)"
        )
        
        # Оновлюємо повідомлення
        keyboard = [
            [
                InlineKeyboardButton("📊 Завантажити ще раз", callback_data="export_csv"),
                InlineKeyboardButton("⚙️ Налаштування", callback_data="settings")
            ],
            [
                InlineKeyboardButton("🏠 Головне меню", callback_data="back_to_main")
            ]
        ]
        
        await query.edit_message_text(
            f"✅ **Файл надіслано!**\n\nВаші {len(transactions)} транзакцій успішно експортовано в CSV формат.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in export_csv: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при експорті даних",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings_export")]])
        )

# ==================== ОЧИЩЕННЯ ДАНИХ ====================

async def show_clear_data_menu(query, context):
    """Показує меню очищення даних"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Підраховуємо кількість транзакцій
        transactions = get_user_transactions(user.id, limit=None)
        transactions_count = len(transactions) if transactions else 0
        
        text = (
            f"🗑️ **Очищення даних**\n\n"
            f"⚠️ **УВАГА!** Ця дія незворотна!\n\n"
            f"У вас є **{transactions_count}** транзакцій.\n\n"
            "🗑️ *Що буде видалено:*\n"
            "• Всі ваші транзакції (доходи та витрати)\n"
            "• Історія операцій\n"
            "• Статистика\n\n"
            "✅ *Що залишиться:*\n"
            "• Ваші категорії\n"
            "• Налаштування профілю\n"
            "• Налаштування бота\n\n"
            "💡 *Рекомендація:* Спочатку зробіть експорт даних!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📤 Спочатку експорт", callback_data="settings_export")
            ],
            [
                InlineKeyboardButton("🗑️ Видалити всі транзакції", callback_data="confirm_clear_data")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="settings")
            ]
        ]
        
        if transactions_count == 0:
            keyboard[1] = [InlineKeyboardButton("📭 Немає даних для видалення", callback_data="no_data")]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_clear_data_menu: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні меню очищення",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings")]])
        )

async def confirm_clear_data(query, context):
    """Підтвердження очищення даних"""
    try:
        user = get_user(query.from_user.id)
        transactions = get_user_transactions(user.id, limit=None)
        transactions_count = len(transactions) if transactions else 0
        
        text = (
            f"⚠️ **ОСТАТОЧНЕ ПІДТВЕРДЖЕННЯ**\n\n"
            f"Ви дійсно хочете видалити **{transactions_count}** транзакцій?\n\n"
            "❗ **ЦЯ ДІЯ НЕЗВОРОТНА!**\n\n"
            "Після видалення ви втратите:\n"
            "• Всю історію транзакцій\n"
            "• Всю статистику\n"
            "• Можливість аналізу минулих періодів\n\n"
            "💭 *Подумайте двічі перед підтвердженням*"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("❌ НІ, скасувати", callback_data="settings_clear_data")
            ],
            [
                InlineKeyboardButton("💀 ТАК, видалити ВСЕ", callback_data="clear_data_confirmed")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in confirm_clear_data: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при підтвердженні",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings_clear_data")]])
        )

async def clear_data_confirmed(query, context):
    """Виконує очищення всіх транзакцій"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Показуємо повідомлення про обробку
        await query.edit_message_text("⏳ Видалення транзакцій...")
        
        # Видаляємо всі транзакції користувача
        session = Session()
        deleted_count = session.query(Transaction).filter(Transaction.user_id == user.id).delete()
        session.commit()
        session.close()
        
        text = (
            f"✅ **Дані очищено**\n\n"
            f"Видалено **{deleted_count}** транзакцій.\n\n"
            "🎯 Тепер ви можете почати з чистого аркуша!\n\n"
            "💡 *Підказка:* Додайте першу транзакцію, щоб почати новий облік фінансів."
        )
        
        keyboard = [
            [
                InlineKeyboardButton("💳 Додати транзакцію", callback_data="add_transaction"),
                InlineKeyboardButton("⚙️ Налаштування", callback_data="settings")
            ],
            [
                InlineKeyboardButton("🏠 Головне меню", callback_data="back_to_main")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in clear_data_confirmed: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при очищенні даних",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings_clear_data")]])
        )

# ==================== ДОПОМІЖНІ ФУНКЦІЇ ====================

async def create_category(query, context, category_type, category_name):
    """Створює нову категорію"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Перевіряємо, чи не існує категорія з такою назвою
        existing_categories = get_user_categories(user.id, category_type)
        if any(cat.name.lower() == category_name.lower() for cat in existing_categories):
            await query.edit_message_text(
                f"❌ Категорія '{category_name}' вже існує!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="add_category")]])
            )
            return
        
        # Створюємо нову категорію
        session = Session()
        new_category = Category(
            user_id=user.id,
            name=category_name,
            type=category_type,
            icon='💸' if category_type == TransactionType.EXPENSE else '💰',
            is_default=False
        )
        session.add(new_category)
        session.commit()
        session.close()
        
        type_text = "витрат" if category_type == TransactionType.EXPENSE else "доходів"
        
        text = (
            f"✅ **Категорія створена**\n\n"
            f"Нова категорія {type_text}:\n"
            f"**{category_name}**\n\n"
            f"Тепер ви можете використовувати її для класифікації транзакцій."
        )
        
        keyboard = [
            [
                InlineKeyboardButton("➕ Додати ще", callback_data="add_category"),
                InlineKeyboardButton("🏷️ До категорій", callback_data="settings_categories")
            ],
            [
                InlineKeyboardButton("💳 Додати транзакцію", callback_data="add_transaction"),
                InlineKeyboardButton("🏠 Головне меню", callback_data="back_to_main")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in create_category: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при створенні категорії",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="add_category")]])
        )

# ==================== ОБРОБКА СТАНУ ВВОДУ ====================

async def handle_category_name_input(update, context):
    """Обробляє введення назви нової категорії"""
    if 'adding_category' not in context.user_data:
        return
    
    category_type = context.user_data['adding_category']
    category_name = update.message.text.strip()
    
    if len(category_name) < 2:
        await update.message.reply_text(
            "❌ Назва категорії повинна містити принаймні 2 символи. Спробуйте ще раз:"
        )
        return
    
    if len(category_name) > 50:
        await update.message.reply_text(
            "❌ Назва категорії занадто довга (максимум 50 символів). Спробуйте ще раз:"
        )
        return
    
    # Очищуємо стан
    del context.user_data['adding_category']
    
    # Створюємо fake query об'єкт для сумісності
    class FakeQuery:
        def __init__(self, user_id, chat_id):
            self.from_user = type('obj', (object,), {'id': user_id})
            self.message = type('obj', (object,), {'chat_id': chat_id})
        
        async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
            await context.bot.send_message(
                chat_id=self.message.chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
    
    fake_query = FakeQuery(update.effective_user.id, update.effective_chat.id)
    await create_category(fake_query, context, category_type, category_name)

async def handle_add_category_type(query, context, category_type):
    """Обробляє вибір типу категорії та просить ввести назву"""
    try:
        from database.models import TransactionType
        
        type_text = "витрат" if category_type == "expense" else "доходів"
        transaction_type = TransactionType.EXPENSE if category_type == "expense" else TransactionType.INCOME
        
        # Зберігаємо тип категорії в контекст
        context.user_data['adding_category'] = transaction_type
        
        text = (
            f"➕ **Додавання категорії {type_text}**\n\n"
            f"Введіть назву нової категорії {type_text}:\n\n"
            "📝 *Вимоги до назви:*\n"
            "• Від 2 до 50 символів\n"
            "• Унікальна назва\n"
            "• Без спеціальних символів\n\n"
            "💡 *Приклади:*\n"
        )
        
        if category_type == "expense":
            text += "• Продукти\n• Транспорт\n• Розваги\n• Комунальні послуги"
        else:
            text += "• Зарплата\n• Фріланс\n• Інвестиції\n• Подарунки"
        
        keyboard = [
            [InlineKeyboardButton("❌ Скасувати", callback_data="add_category")]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_add_category_type: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при додаванні категорії",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="add_category")]])
        )

async def show_all_categories(query, context):
    """Показує всі категорії користувача"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Отримуємо всі категорії
        expense_categories = get_user_categories(user.id, TransactionType.EXPENSE)
        income_categories = get_user_categories(user.id, TransactionType.INCOME)
        
        text = "📋 **Всі категорії**\n\n"
        
        # Категорії витрат
        if expense_categories:
            text += "💸 **Категорії витрат:**\n"
            for i, cat in enumerate(expense_categories, 1):
                icon = getattr(cat, 'icon', '💸')
                status = " 🔧" if cat.is_default else ""
                text += f"{i}. {icon} {cat.name}{status}\n"
        else:
            text += "💸 **Категорії витрат:** відсутні\n"
        
        text += "\n"
        
        # Категорії доходів
        if income_categories:
            text += "💰 **Категорії доходів:**\n"
            for i, cat in enumerate(income_categories, 1):
                icon = getattr(cat, 'icon', '💰')
                status = " 🔧" if cat.is_default else ""
                text += f"{i}. {icon} {cat.name}{status}\n"
        else:
            text += "💰 **Категорії доходів:** відсутні\n"
        
        text += "\n🔧 - системні категорії (неможливо видалити)"
        
        keyboard = [
            [
                InlineKeyboardButton("➕ Додати категорію", callback_data="add_category"),
                InlineKeyboardButton("🗑️ Видалити", callback_data="delete_category_select")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="settings_categories")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_all_categories: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні категорій",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="settings_categories")]])
        )
