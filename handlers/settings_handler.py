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
                InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
            ]
        ]
        
        text = (
            "⚙️ **Налаштування**\n\n"
            "Керуйте своїм профілем:\n\n"
            "🏷️ **Категорії** — управління категоріями\n"
            "💱 **Валюта** — основна валюта відображення\n"
            "📤 **Експорт** — завантаження ваших даних\n"
            "🗑️ **Очистити** — видалення всіх транзакцій\n\n"
            "💡 *Зміни зберігаються автоматично*"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_settings_menu: {str(e)}")
        await query.edit_message_text(
            "❌ Не вдалося завантажити налаштування",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")]])
        )

# ==================== УПРАВЛІННЯ КАТЕГОРІЯМИ ====================

async def show_categories_management(query, context):
    """Показує меню управління категоріями з інтерактивними кнопками"""
async def show_categories_management(query, context):
    """Показує меню управління категоріями з пагінацією"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Ініціалізуємо або отримуємо параметри перегляду категорій
        if 'categories_view' not in context.user_data:
            context.user_data['categories_view'] = {
                'page': 1,
                'per_page': 8,  # 8 категорій на сторінку
                'show_type': 'all'  # 'all', 'income', 'expense'
            }
        
        view_params = context.user_data['categories_view']
        page = view_params.get('page', 1)
        per_page = view_params.get('per_page', 8)
        show_type = view_params.get('show_type', 'all')
        
        # Отримуємо всі категорії
        expense_categories = get_user_categories(user.id, TransactionType.EXPENSE.value)
        income_categories = get_user_categories(user.id, TransactionType.INCOME.value)
        
        # Фільтруємо категорії за типом
        if show_type == 'expense':
            all_categories = [('expense', cat) for cat in expense_categories]
        elif show_type == 'income':
            all_categories = [('income', cat) for cat in income_categories]
        else:  # show_type == 'all'
            all_categories = []
            # Спочатку додаємо витрати, потім доходи
            all_categories.extend([('expense', cat) for cat in expense_categories])
            all_categories.extend([('income', cat) for cat in income_categories])
        
        total_categories = len(all_categories)
        
        if total_categories == 0:
            text = "🏷️ **Категорії**\n\n📭 У вас немає категорій.\nСтворіть першу категорію!"
            keyboard = [
                [InlineKeyboardButton("➕ Створити категорію", callback_data="add_category")],
                [InlineKeyboardButton("◀️ Налаштування", callback_data="settings")]
            ]
        else:
            # Розраховуємо пагінацію
            total_pages = max(1, (total_categories + per_page - 1) // per_page)
            start_idx = (page - 1) * per_page
            end_idx = min(start_idx + per_page, total_categories)
            
            # Формуємо заголовок
            type_filter_text = ""
            if show_type == 'expense':
                type_filter_text = " (Витрати)"
            elif show_type == 'income':
                type_filter_text = " (Доходи)"
            
            text = f"🏷️ **Категорії{type_filter_text}**\n"
            text += f"📄 Сторінка {page} з {total_pages} | Всього: {total_categories}\n\n"
            text += "💡 *Натисніть на категорію для редагування або видалення*\n\n"
            
            keyboard = []
            
            # Групуємо категорії для відображення
            current_categories = all_categories[start_idx:end_idx]
            current_section = None
            
            for cat_type, cat in current_categories:
                # Додаємо заголовок секції, якщо змінився тип
                if show_type == 'all' and current_section != cat_type:
                    current_section = cat_type
                    if cat_type == 'expense':
                        keyboard.append([InlineKeyboardButton("💸 ── ВИТРАТИ ──", callback_data="noop_header")])
                    else:
                        keyboard.append([InlineKeyboardButton("💰 ── ДОХОДИ ──", callback_data="noop_header")])
                
                # Додаємо кнопку категорії
                icon = getattr(cat, 'icon', '💸' if cat_type == 'expense' else '💰')
                status = " 🔧" if getattr(cat, 'is_default', False) else ""
                button_text = f"{icon} {cat.name}{status}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"edit_category_{cat.id}")])
            
            # Додаємо кнопки фільтрів
            filter_row = []
            if show_type != 'expense':
                filter_row.append(InlineKeyboardButton("� Витрати", callback_data="categories_filter_expense"))
            if show_type != 'income':
                filter_row.append(InlineKeyboardButton("💰 Доходи", callback_data="categories_filter_income"))
            if show_type != 'all':
                filter_row.append(InlineKeyboardButton("📋 Всі", callback_data="categories_filter_all"))
            
            if filter_row:
                keyboard.append(filter_row)
            
            # Додаємо кнопки пагінації, якщо потрібно
            pagination_row = []
            if page > 1:
                pagination_row.append(InlineKeyboardButton("◀️ Попередня", callback_data="categories_prev_page"))
            if page < total_pages:
                pagination_row.append(InlineKeyboardButton("Наступна ▶️", callback_data="categories_next_page"))
                
            if pagination_row:
                keyboard.append(pagination_row)
            
            # Додаємо функціональні кнопки
            keyboard.append([InlineKeyboardButton("➕ Нова категорія", callback_data="add_category")])
            keyboard.append([InlineKeyboardButton("◀️ Налаштування", callback_data="settings")])
            
            if show_type == 'all':
                text += "🔧 — системні категорії (захищені від видалення)"
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_categories_management: {str(e)}")
        await query.edit_message_text(
            "❌ Не вдалося завантажити категорії",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="settings")]])
        )

async def show_add_category_menu(query, context):
    """Показує меню додавання категорії"""
    keyboard = [
        [
            InlineKeyboardButton("💸 Витрати", callback_data="add_category_expense"),
            InlineKeyboardButton("💰 Доходи", callback_data="add_category_income")
        ],
        [
            InlineKeyboardButton("◀️ Назад", callback_data="settings_categories")
        ]
    ]
    
    text = (
        "➕ **Нова категорія**\n\n"
        "Оберіть тип:\n\n"
        "💸 *Витрати* — для класифікації трат\n"
        "💰 *Доходи* — для типів надходжень\n\n"
        "💡 *Далі введіть назву категорії*"
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
                "📭 Немає категорій для видалення\n\n"
                "Можна видаляти лише власні категорії.\n"
                "Системні категорії захищені від видалення."
            )
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="settings_categories")]]
        else:
            text = "🗑️ **Оберіть категорію для видалення:**\n\n"
            
            keyboard = []
            for cat in user_categories[:10]:  # Показуємо максимум 10
                icon = getattr(cat, 'icon', '🏷️')
                type_emoji = "💸" if cat.type == TransactionType.EXPENSE else "💰"
                button_text = f"{type_emoji} {icon} {cat.name}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"confirm_delete_cat_{cat.id}")])
            
            keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="settings_categories")])
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_delete_category_select: {str(e)}")
        await query.edit_message_text(
            "❌ Не вдалося завантажити категорії",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="settings_categories")]])
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
            f"Видалити категорію **{category.name}**?\n\n"
        )
        
        if transactions_count > 0:
            text += f"⚠️ *Увага:* {transactions_count} транзакцій використовують цю категорію.\n"
            text += "Вони залишаться, але без категорії.\n\n"
        
        text += "❗ *Дія незворотна*"
        
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
            "❌ Не вдалося підтвердити видалення",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="settings_categories")]])
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
            f"✅ **Категорію видалено**\n\n"
            f"**{category_name}** більше не існує"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("◀️ До категорій", callback_data="settings_categories"),
                InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
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
            "❌ Не вдалося видалити категорію",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="settings_categories")]])
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
            f"💱 **Валюта відображення**\n\n"
            f"Поточна: **{current_currency}**\n\n"
            "Оберіть основну валюту для показу сум:"
        )
        
        keyboard = []
        for code, flag, name in currencies:
            status = " ✅" if code == current_currency else ""
            button_text = f"{flag} {code} - {name}{status}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"set_currency_{code}")])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="settings")])
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_currency_settings: {str(e)}")
        await query.edit_message_text(
            "❌ Не вдалося завантажити налаштування валюти",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="settings")]])
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
            f"✅ **Валюту змінено**\n\n"
            f"Тепер основна валюта: {flag} **{currency_code}**\n\n"
            f"Всі суми відображатимуться у {currency_code}"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("💱 Змінити валюту", callback_data="settings_currency"),
                InlineKeyboardButton("⚙️ Налаштування", callback_data="settings")
            ],
            [
                InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
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
            "❌ Не вдалося змінити валюту",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="settings_currency")]])
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
            f"Доступно **{transactions_count}** транзакцій\n\n"
            "📊 *Формат CSV* — таблиця для Excel\n\n"
            "📋 *Що експортується:*\n"
            "• Дата та час\n"
            "• Тип та сума\n"
            "• Категорія та опис\n"
            "• Джерело транзакції\n\n"
            "💡 *Файл надійде у цей чат*"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Завантажити CSV", callback_data="export_csv"),
            ],
            [
                InlineKeyboardButton("◀️ Налаштування", callback_data="settings")
            ]
        ]
        
        if transactions_count == 0:
            keyboard[0] = [InlineKeyboardButton("� Немає даних", callback_data="no_data")]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_export_menu: {str(e)}")
        await query.edit_message_text(
            "❌ Не вдалося підготувати експорт",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="settings")]])
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
                "📭 **Немає даних**\n\nПоки що транзакції відсутні",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="settings_export")]])
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
                InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
            ]
        ]
        
        await query.edit_message_text(
            f"✅ **Файл надіслано**\n\n{len(transactions)} транзакцій експортовано у CSV",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in export_csv: {str(e)}")
        await query.edit_message_text(
            "❌ Не вдалося експортувати дані",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="settings_export")]])
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
            f"⚠️ **УВАГА! Дія незворотна**\n\n"
            f"Транзакцій: **{transactions_count}**\n\n"
            "🗑️ *Що видалиться:*\n"
            "• Всі транзакції\n"
            "• Історія операцій\n"
            "• Статистика\n\n"
            "✅ *Що залишиться:*\n"
            "• Категорії\n"
            "• Налаштування\n\n"
            "💡 *Спочатку зробіть експорт!*"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📤 Спочатку експорт", callback_data="settings_export")
            ],
            [
                InlineKeyboardButton("🗑️ Видалити всі транзакції", callback_data="confirm_clear_data")
            ],
            [
                InlineKeyboardButton("◀️ Назад", callback_data="settings")
            ]
        ]
        
        if transactions_count == 0:
            keyboard[1] = [InlineKeyboardButton("📭 Немає даних", callback_data="no_data")]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_clear_data_menu: {str(e)}")
        await query.edit_message_text(
            "❌ Не вдалося підготувати очищення",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="settings")]])
        )

async def confirm_clear_data(query, context):
    """Підтвердження очищення даних"""
    try:
        user = get_user(query.from_user.id)
        transactions = get_user_transactions(user.id, limit=None)
        transactions_count = len(transactions) if transactions else 0
        
        text = (
            f"⚠️ **ОСТАННЄ ПІДТВЕРДЖЕННЯ**\n\n"
            f"Видалити **{transactions_count}** транзакцій?\n\n"
            "❗ **ДІЯ НЕЗВОРОТНА**\n\n"
            "Ви втратите:\n"
            "• Всю історію транзакцій\n"
            "• Статистику та аналітику\n"
            "• Можливість аналізу періодів\n\n"
            "💭 *Подумайте двічі*"
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
            "❌ Не вдалося підтвердити дію",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="settings_clear_data")]])
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
            f"Видалено: **{deleted_count}** транзакцій\n\n"
            "🎯 Тепер можна почати заново!\n\n"
            "💡 *Додайте першу транзакцію*"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("💳 Додати транзакцію", callback_data="add_transaction"),
                InlineKeyboardButton("⚙️ Налаштування", callback_data="settings")
            ],
            [
                InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
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
            "❌ Не вдалося очистити дані",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="settings_clear_data")]])
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
                f"❌ Категорія **{category_name}** вже існує",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="add_category")]]),
                parse_mode="Markdown"
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
            f"✅ **Категорію створено**\n\n"
            f"Нова категорія {type_text}: **{category_name}**\n\n"
            f"Тепер можна використовувати її у транзакціях"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("➕ Додати ще", callback_data="add_category"),
                InlineKeyboardButton("🏷️ До категорій", callback_data="settings_categories")
            ],
            [
                InlineKeyboardButton("💳 Додати транзакцію", callback_data="add_transaction"),
                InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
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
            "❌ Не вдалося створити категорію",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="add_category")]])
        )

# ==================== ОБРОБКА СТАНУ ВВОДУ ====================

async def handle_category_name_input(update, context):
    """Обробляє введення назви нової категорії або перейменування"""
    # Перевіряємо, чи це перейменування категорії
    if 'renaming_category' in context.user_data:
        await handle_category_rename_input(update, context)
        return
    
    # Обробляємо створення нової категорії
    if 'adding_category' not in context.user_data:
        return
    
    category_type = context.user_data['adding_category']
    category_name = update.message.text.strip()
    
    if len(category_name) < 2:
        await update.message.reply_text(
            "❌ Назва занадто коротка (мінімум 2 символи). Спробуйте ще раз:"
        )
        return
    
    if len(category_name) > 50:
        await update.message.reply_text(
            "❌ Назва занадто довга (максимум 50 символів). Спробуйте ще раз:"
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
            f"➕ **Створення категорії {type_text}**\n\n"
            f"Введіть назву категорії {type_text}:\n\n"
            "📝 *Вимоги:*\n"
            "• 2-50 символів\n"
            "• Унікальна назва\n\n"
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
            "❌ Не вдалося додати категорію",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="add_category")]])
        )

async def show_all_categories(query, context):
    """Показує всі категорії користувача з пагінацією"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Ініціалізуємо або отримуємо параметри перегляду категорій
        if 'categories_view' not in context.user_data:
            context.user_data['categories_view'] = {
                'page': 1,
                'per_page': 8,  # 8 категорій на сторінку (по 4 для доходів і витрат)
                'show_type': 'all'  # 'all', 'income', 'expense'
            }
        
        view_params = context.user_data['categories_view']
        page = view_params.get('page', 1)
        per_page = view_params.get('per_page', 8)
        show_type = view_params.get('show_type', 'all')
        
        # Отримуємо всі категорії
        expense_categories = get_user_categories(user.id, TransactionType.EXPENSE.value)
        income_categories = get_user_categories(user.id, TransactionType.INCOME.value)
        
        # Фільтруємо категорії за типом
        if show_type == 'expense':
            all_categories = [('expense', cat) for cat in expense_categories]
        elif show_type == 'income':
            all_categories = [('income', cat) for cat in income_categories]
        else:  # show_type == 'all'
            all_categories = []
            # Спочатку додаємо витрати, потім доходи
            all_categories.extend([('expense', cat) for cat in expense_categories])
            all_categories.extend([('income', cat) for cat in income_categories])
        
        total_categories = len(all_categories)
        
        if total_categories == 0:
            text = "📋 **Всі категорії**\n\n📭 У вас немає категорій.\nСтворіть першу категорію!"
            keyboard = [
                [InlineKeyboardButton("➕ Створити категорію", callback_data="add_category")],
                [InlineKeyboardButton("◀️ Назад", callback_data="settings_categories")]
            ]
        else:
            # Розраховуємо пагінацію
            total_pages = max(1, (total_categories + per_page - 1) // per_page)
            start_idx = (page - 1) * per_page
            end_idx = min(start_idx + per_page, total_categories)
            
            # Формуємо заголовок
            type_filter_text = ""
            if show_type == 'expense':
                type_filter_text = " (Витрати)"
            elif show_type == 'income':
                type_filter_text = " (Доходи)"
            
            text = f"📋 **Всі категорії{type_filter_text}**\n"
            text += f"📄 Сторінка {page} з {total_pages} | Всього: {total_categories}\n\n"
            text += "💡 *Натисніть на категорію для редагування або видалення*\n\n"
            
            keyboard = []
            
            # Групуємо категорії для відображення
            current_categories = all_categories[start_idx:end_idx]
            current_section = None
            
            for cat_type, cat in current_categories:
                # Додаємо заголовок секції, якщо змінився тип
                if show_type == 'all' and current_section != cat_type:
                    current_section = cat_type
                    if cat_type == 'expense':
                        keyboard.append([InlineKeyboardButton("💸 ── ВИТРАТИ ──", callback_data="noop_header")])
                    else:
                        keyboard.append([InlineKeyboardButton("💰 ── ДОХОДИ ──", callback_data="noop_header")])
                
                # Додаємо кнопку категорії
                icon = getattr(cat, 'icon', '💸' if cat_type == 'expense' else '💰')
                status = " 🔧" if getattr(cat, 'is_default', False) else ""
                button_text = f"{icon} {cat.name}{status}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"edit_category_{cat.id}")])
            
            # Додаємо кнопки фільтрів
            filter_row = []
            if show_type != 'expense':
                filter_row.append(InlineKeyboardButton("� Витрати", callback_data="categories_filter_expense"))
            if show_type != 'income':
                filter_row.append(InlineKeyboardButton("💰 Доходи", callback_data="categories_filter_income"))
            if show_type != 'all':
                filter_row.append(InlineKeyboardButton("📋 Всі", callback_data="categories_filter_all"))
            
            if filter_row:
                keyboard.append(filter_row)
            
            # Додаємо кнопки пагінації, якщо потрібно
            pagination_row = []
            if page > 1:
                pagination_row.append(InlineKeyboardButton("◀️ Попередня", callback_data="categories_prev_page"))
            if page < total_pages:
                pagination_row.append(InlineKeyboardButton("Наступна ▶️", callback_data="categories_next_page"))
                
            if pagination_row:
                keyboard.append(pagination_row)
            
            # Додаємо функціональні кнопки
            keyboard.append([InlineKeyboardButton("➕ Нова категорія", callback_data="add_category")])
            keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="settings_categories")])
            
            if show_type == 'all':
                text += "🔧 — системні категорії (захищені від видалення)"
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_all_categories: {str(e)}")
        await query.edit_message_text(
            "❌ Не вдалося завантажити категорії",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="settings_categories")]])
        )

async def show_category_edit_menu(query, context, category_id):
    """Показує меню редагування конкретної категорії"""
    try:
        session = Session()
        category = session.query(Category).filter(Category.id == category_id).first()
        
        if not category:
            await query.edit_message_text("❌ Категорія не знайдена")
            session.close()
            return
        
        # Перевіряємо, чи це категорія користувача
        user = get_user(query.from_user.id)
        if not user or category.user_id != user.id:
            await query.edit_message_text("❌ Немає доступу до цієї категорії")
            session.close()
            return
        
        icon = getattr(category, 'icon', '🏷️')
        type_emoji = "💸" if category.type == TransactionType.EXPENSE else "💰"
        type_text = "витрат" if category.type == TransactionType.EXPENSE else "доходів"
        
        # Підраховуємо кількість транзакцій з цією категорією
        transactions_count = session.query(Transaction).filter(Transaction.category_id == category_id).count()
        
        text = (
            f"✏️ **Редагування категорії**\n\n"
            f"{type_emoji} **{icon} {category.name}**\n"
            f"Тип: {type_text}\n"
            f"Транзакцій: {transactions_count}\n"
        )
        
        if category.is_default:
            text += "\n🔧 *Системна категорія* — захищена від видалення"
        
        keyboard = []
        
        # Додаємо кнопки редагування тільки для користувацьких категорій
        if not category.is_default:
            keyboard.extend([
                [InlineKeyboardButton("✏️ Змінити назву", callback_data=f"rename_category_{category_id}")],
                [InlineKeyboardButton("🗑️ Видалити категорію", callback_data=f"confirm_delete_cat_{category_id}")]
            ])
        else:
            keyboard.append([InlineKeyboardButton("ℹ️ Системну категорію не можна змінювати", callback_data="noop_header")])
        
        keyboard.append([InlineKeyboardButton("◀️ До категорій", callback_data="settings_categories")])
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        session.close()
        
    except Exception as e:
        logger.error(f"Error in show_category_edit_menu: {str(e)}")
        await query.edit_message_text(
            "❌ Не вдалося завантажити категорію",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ До категорій", callback_data="settings_categories")]])
        )

async def show_rename_category_form(query, context, category_id):
    """Показує форму для перейменування категорії"""
    try:
        session = Session()
        category = session.query(Category).filter(Category.id == category_id).first()
        
        if not category or category.is_default:
            await query.edit_message_text("❌ Категорію неможливо перейменувати")
            session.close()
            return
        
        # Зберігаємо ID категорії для перейменування
        context.user_data['renaming_category'] = category_id
        
        icon = getattr(category, 'icon', '🏷️')
        
        text = (
            f"✏️ **Перейменування категорії**\n\n"
            f"Поточна назва: **{icon} {category.name}**\n\n"
            f"Введіть нову назву категорії:\n\n"
            f"📝 *Вимоги:*\n"
            f"• 2-50 символів\n"
            f"• Унікальна назва\n\n"
            f"💡 *Надішліть повідомлення з новою назвою*"
        )
        
        keyboard = [
            [InlineKeyboardButton("❌ Скасувати", callback_data=f"edit_category_{category_id}")]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        session.close()
        
    except Exception as e:
        logger.error(f"Error in show_rename_category_form: {str(e)}")
        await query.edit_message_text(
            "❌ Не вдалося відкрити форму перейменування",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ До категорій", callback_data="settings_categories")]])
        )

async def handle_category_rename_input(update, context):
    """Обробляє введення нової назви категорії"""
    if 'renaming_category' not in context.user_data:
        return
    
    category_id = context.user_data['renaming_category']
    new_name = update.message.text.strip()
    
    if len(new_name) < 2:
        await update.message.reply_text(
            "❌ Назва занадто коротка (мінімум 2 символи). Спробуйте ще раз:"
        )
        return
    
    if len(new_name) > 50:
        await update.message.reply_text(
            "❌ Назва занадто довга (максимум 50 символів). Спробуйте ще раз:"
        )
        return
    
    # Очищуємо стан
    del context.user_data['renaming_category']
    
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
    await rename_category(fake_query, context, category_id, new_name)

async def rename_category(query, context, category_id, new_name):
    """Перейменовує категорію"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        session = Session()
        category = session.query(Category).filter(
            Category.id == category_id,
            Category.user_id == user.id
        ).first()
        
        if not category:
            await query.edit_message_text("❌ Категорія не знайдена")
            session.close()
            return
        
        if category.is_default:
            await query.edit_message_text("❌ Системну категорію неможливо перейменувати")
            session.close()
            return
        
        # Перевіряємо, чи не існує категорія з такою назвою
        existing_categories = get_user_categories(user.id, category.type)
        if any(cat.name.lower() == new_name.lower() and cat.id != category_id for cat in existing_categories):
            await query.edit_message_text(
                f"❌ Категорія **{new_name}** вже існує",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"edit_category_{category_id}")]]),
                parse_mode="Markdown"
            )
            session.close()
            return
        
        old_name = category.name
        category.name = new_name
        session.commit()
        session.close()
        
        text = (
            f"✅ **Категорію перейменовано**\n\n"
            f"**{old_name}** → **{new_name}**\n\n"
            f"Зміни застосовано до всіх транзакцій"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✏️ Редагувати ще", callback_data=f"edit_category_{category_id}"),
                InlineKeyboardButton("🏷️ До категорій", callback_data="settings_categories")
            ],
            [
                InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in rename_category: {str(e)}")
        await query.edit_message_text(
            "❌ Не вдалося перейменувати категорію",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ До категорій", callback_data="settings_categories")]])
        )

# ==================== ОБРОБНИКИ ПАГІНАЦІЇ ТА ФІЛЬТРІВ КАТЕГОРІЙ ====================

async def handle_categories_pagination(query, context, direction):
    """Обробка пагінації списку категорій"""
    try:
        # Ініціалізуємо параметри перегляду, якщо їх немає
        if 'categories_view' not in context.user_data:
            context.user_data['categories_view'] = {
                'page': 1,
                'per_page': 8,
                'show_type': 'all'
            }
        
        view_params = context.user_data['categories_view']
        current_page = view_params.get('page', 1)
        
        # Розраховуємо нову сторінку
        if direction == 'next':
            view_params['page'] = current_page + 1
        else:  # prev
            view_params['page'] = max(1, current_page - 1)
        
        context.user_data['categories_view'] = view_params
        
        # Оновлюємо список категорій з новою сторінкою
        await show_all_categories(query, context)
        
    except Exception as e:
        logger.error(f"Error handling categories pagination: {str(e)}")
        await query.answer("Помилка при пагінації списку категорій.")

async def handle_categories_filter(query, context, filter_type):
    """Обробка фільтрів категорій"""
    try:
        # Ініціалізуємо параметри перегляду, якщо їх немає
        if 'categories_view' not in context.user_data:
            context.user_data['categories_view'] = {
                'page': 1,
                'per_page': 8,
                'show_type': 'all'
            }
        
        view_params = context.user_data['categories_view']
        
        # Встановлюємо новий фільтр
        view_params['show_type'] = filter_type
        view_params['page'] = 1  # Скидаємо на першу сторінку при зміні фільтра
        
        context.user_data['categories_view'] = view_params
        
        # Оновлюємо список категорій з новим фільтром
        await show_all_categories(query, context)
        
    except Exception as e:
        logger.error(f"Error handling categories filter: {str(e)}")
        await query.answer("Помилка при фільтрації категорій.")
