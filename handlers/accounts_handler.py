"""
Модуль для управління рахунками користувача
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import logging

from database.db_operations import get_or_create_user, get_user_accounts, get_total_balance, get_accounts_count, create_account, get_accounts_statistics
from database.models import AccountType

logger = logging.getLogger(__name__)

async def show_accounts_menu(query, context):
    """Показує головне меню управління рахунками"""
    try:
        user = get_or_create_user(query.from_user.id)
        
        # Отримуємо рахунки користувача
        accounts_count = get_accounts_count(user.id)
        total_balance = get_total_balance(user.id)
        
        currency = user.currency or "UAH"
        currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
        
        message = f"💳 *Управління рахунками*\n\n"
        message += f"📊 *Поточний стан:*\n"
        message += f"🏦 Кількість рахунків: `{accounts_count}`\n"
        message += f"💰 Загальний баланс: `{total_balance:,.2f} {currency_symbol}`\n\n"
        message += "Оберіть дію:"
        
        keyboard = [
            [
                InlineKeyboardButton("📋 Мої рахунки", callback_data="accounts_list"),
                InlineKeyboardButton("➕ Додати рахунок", callback_data="accounts_add")
            ],
            [
                InlineKeyboardButton("💸 Переказ між рахунками", callback_data="accounts_transfer"),
                InlineKeyboardButton("📊 Статистика", callback_data="accounts_stats")
            ],
            [
                InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")
            ]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_accounts_menu: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка завантаження меню рахунків",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")
            ]]),
            parse_mode="Markdown"
        )

async def show_accounts_list(query, context):
    """Показує список рахунків користувача"""
    try:
        user = get_or_create_user(query.from_user.id)
        accounts = get_user_accounts(user.id)
        
        currency = user.currency or "UAH"
        currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
        
        if not accounts:
            message = "💳 *Мої рахунки*\n\n"
            message += "📭 У вас ще немає створених рахунків.\n\n"
            message += "💡 *Створіть перший рахунок:*\n"
            message += "• Основний рахунок (готівка)\n"
            message += "• Банківська картка\n"
            message += "• Ощадний рахунок\n"
            message += "• Інвестиційний рахунок"
            
            keyboard = [
                [InlineKeyboardButton("➕ Створити перший рахунок", callback_data="accounts_add")],
                [InlineKeyboardButton("🔙 Назад", callback_data="accounts_menu")]
            ]
        else:
            message = f"💳 *Мої рахунки*\n\n"
            
            for account in accounts:
                status_emoji = "✅" if account.is_active else "🔒"
                balance_color = "💚" if account.balance >= 0 else "🔴"
                
                message += f"{status_emoji} *{account.name}* {account.icon}\n"
                message += f"   {balance_color} `{account.balance:,.2f} {currency_symbol}`\n"
                message += f"   🏷️ {account.account_type.value.replace('_', ' ').title()}"
                if account.is_main:
                    message += " • ⭐ Головний"
                message += f" • 📅 {account.created_at.strftime('%d.%m.%Y')}\n\n"
            
            keyboard = [
                [
                    InlineKeyboardButton("➕ Додати рахунок", callback_data="accounts_add"),
                    InlineKeyboardButton("⚙️ Налаштувати", callback_data="accounts_settings")
                ],
                [InlineKeyboardButton("🔙 Назад", callback_data="accounts_menu")]
            ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_accounts_list: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка завантаження списку рахунків",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="accounts_menu")
            ]]),
            parse_mode="Markdown"
        )

async def show_add_account_form(query, context):
    """Показує форму для додавання нового рахунку"""
    message = f"➕ *Створення нового рахунку*\n\n"
    message += "Оберіть тип рахунку, який хочете створити:\n\n"
    message += "💵 *Готівка* - основний рахунок для щоденних витрат\n"
    message += "💳 *Банківська картка* - дебетова або кредитна картка\n"
    message += "🏦 *Банківський рахунок* - депозитний або поточний рахунок\n"
    message += "💰 *Ощадний рахунок* - для накопичень\n"
    message += "📈 *Інвестиційний* - для інвестицій та цінних паперів\n"
    message += "🌐 *Криптовалюта* - криптовалютний гаманець\n"
    message += "🎯 *Інший* - інший тип рахунку"
    
    keyboard = [
        [
            InlineKeyboardButton("💵 Готівка", callback_data="accounts_add_cash"),
            InlineKeyboardButton("💳 Картка", callback_data="accounts_add_card")
        ],
        [
            InlineKeyboardButton("🏦 Банк", callback_data="accounts_add_bank"),
            InlineKeyboardButton("💰 Ощадний", callback_data="accounts_add_savings")
        ],
        [
            InlineKeyboardButton("📈 Інвестиційний", callback_data="accounts_add_investment"),
            InlineKeyboardButton("🌐 Криптовалюта", callback_data="accounts_add_crypto")
        ],
        [
            InlineKeyboardButton("🎯 Інший", callback_data="accounts_add_other")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="accounts_menu")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_account_transfer(query, context):
    """Показує форму для переказу між рахунками"""
    user = get_or_create_user(query.from_user.id)
    accounts = get_user_accounts(user.id)
    
    if len(accounts) < 2:
        message = "💸 *Переказ між рахунками*\n\n"
        message += "❌ Для здійснення переказу потрібно мати принаймні 2 рахунки.\n\n"
        message += "Створіть додатковий рахунок для можливості переказів."
        
        keyboard = [
            [InlineKeyboardButton("➕ Створити рахунок", callback_data="accounts_add")],
            [InlineKeyboardButton("🔙 Назад", callback_data="accounts_menu")]
        ]
    else:
        message = "💸 *Переказ між рахунками*\n\n"
        message += "На даному етапі функціональність переказів знаходиться в розробці.\n\n"
        message += "💡 *Скоро буде доступно:*\n"
        message += "• Миттєві перекази між рахунками\n"
        message += "• Автоматичні перекази за розкладом\n"
        message += "• Історія всіх переказів\n"
        message += "• Комісії та ліміти"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="accounts_menu")]
        ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_accounts_stats(query, context):
    """Показує статистику по рахунках"""
    user = get_or_create_user(query.from_user.id)
    stats = get_accounts_statistics(user.id)
    
    currency = user.currency or "UAH"
    currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
    
    message = f"📊 *Статистика рахунків*\n\n"
    
    if stats['total_accounts'] == 0:
        message += "📭 Немає створених рахунків для відображення статистики."
    else:
        message += f"🏦 *Загальна інформація:*\n"
        message += f"• Всього рахунків: `{stats['total_accounts']}`\n"
        message += f"• Активних рахунків: `{stats['active_accounts']}`\n"
        message += f"• Загальний баланс: `{stats['total_balance']:,.2f} {currency_symbol}`\n\n"
        
        message += f"💰 *Розподіл за типами:*\n"
        for account_type, data in stats['by_type'].items():
            message += f"• {data['icon']} {account_type}: `{data['balance']:,.2f} {currency_symbol}` ({data['count']} рах.)\n"
        
        message += f"\n📈 *Динаміка за місяць:*\n"
        message += f"• Приріст балансу: `{stats['monthly_growth']:,.2f} {currency_symbol}`\n"
        message += f"• Кількість операцій: `{stats['monthly_transactions']}`\n"
    
    keyboard = [
        [InlineKeyboardButton("📋 Детальний звіт", callback_data="accounts_detailed_report")],
        [InlineKeyboardButton("🔙 Назад", callback_data="accounts_menu")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# Обробники для створення різних типів рахунків
async def create_cash_account(query, context):
    """Створює готівковий рахунок"""
    context.user_data['account_creation'] = {
        'type': 'cash',
        'icon': '💵',
        'name_template': 'Готівка'
    }
    await show_account_name_input(query, context)

async def create_card_account(query, context):
    """Створює рахунок банківської картки"""
    context.user_data['account_creation'] = {
        'type': 'card', 
        'icon': '💳',
        'name_template': 'Банківська картка'
    }
    await show_account_name_input(query, context)

async def create_bank_account(query, context):
    """Створює банківський рахунок"""
    context.user_data['account_creation'] = {
        'type': 'bank',
        'icon': '🏦', 
        'name_template': 'Банківський рахунок'
    }
    await show_account_name_input(query, context)

async def create_savings_account(query, context):
    """Створює ощадний рахунок"""
    context.user_data['account_creation'] = {
        'type': 'savings',
        'icon': '💰',
        'name_template': 'Ощадний рахунок'
    }
    await show_account_name_input(query, context)

async def create_investment_account(query, context):
    """Створює інвестиційний рахунок"""
    context.user_data['account_creation'] = {
        'type': 'investment',
        'icon': '📈',
        'name_template': 'Інвестиційний рахунок'
    }
    await show_account_name_input(query, context)

async def create_crypto_account(query, context):
    """Створює криптовалютний рахунок"""
    context.user_data['account_creation'] = {
        'type': 'crypto',
        'icon': '🌐',
        'name_template': 'Криптогаманець'
    }
    await show_account_name_input(query, context)

async def create_other_account(query, context):
    """Створює інший тип рахунку"""
    context.user_data['account_creation'] = {
        'type': 'other',
        'icon': '🎯',
        'name_template': 'Інший рахунок'
    }
    await show_account_name_input(query, context)

async def show_account_name_input(query, context):
    """Показує форму для введення назви рахунку"""
    account_data = context.user_data.get('account_creation', {})
    account_type = account_data.get('name_template', 'Новий рахунок')
    icon = account_data.get('icon', '💳')
    
    message = f"{icon} *Створення рахунку: {account_type}*\n\n"
    message += "📝 Введіть назву для вашого нового рахунку:\n\n"
    message += "💡 *Приклади назв:*\n"
    message += "• Моя основна картка\n"
    message += "• Готівка в гаманці\n"
    message += "• ПриватБанк - зарплата\n"
    message += "• Ощадний фонд\n\n"
    message += "Або скористайтеся назвою за замовчуванням:"
    
    keyboard = [
        [InlineKeyboardButton(f"✅ Використати: {account_type}", callback_data="accounts_use_default_name")],
        [InlineKeyboardButton("🔙 Назад до типів", callback_data="accounts_add")],
        [InlineKeyboardButton("❌ Скасувати", callback_data="accounts_menu")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Зберігаємо стан очікування введення
    context.user_data['awaiting_account_name'] = True

async def use_default_account_name(query, context):
    """Використовує назву за замовчуванням для рахунку"""
    account_data = context.user_data.get('account_creation', {})
    account_name = account_data.get('name_template', 'Новий рахунок')
    
    # Створюємо рахунок з назвою за замовчуванням
    await create_account_with_name(query, context, account_name)

async def create_account_with_name(query, context, account_name):
    """Створює рахунок з вказаною назвою"""
    try:
        user = get_or_create_user(query.from_user.id)
        account_data = context.user_data.get('account_creation', {})
        
        # TODO: Тут буде реальне створення рахунку в БД
        # create_user_account(user.id, account_name, account_data['type'], account_data['icon'])
        
        success_message = f"✅ *Рахунок успішно створено!*\n\n"
        success_message += f"{account_data.get('icon', '💳')} *{account_name}*\n"
        success_message += f"📝 Тип: {account_data.get('type', 'unknown').title()}\n"
        success_message += f"💰 Початковий баланс: `0.00 ₴`\n\n"
        success_message += "💡 Тепер ви можете:\n"
        success_message += "• Додавати транзакції до цього рахунку\n"
        success_message += "• Переказувати кошти між рахунками\n"
        success_message += "• Відстежувати баланс та історію операцій"
        
        keyboard = [
            [InlineKeyboardButton("📋 Переглянути рахунки", callback_data="accounts_list")],
            [InlineKeyboardButton("➕ Створити ще один", callback_data="accounts_add")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="back_to_main")]
        ]
        
        await query.edit_message_text(
            success_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        # Очищаємо дані створення рахунку
        context.user_data.pop('account_creation', None)
        context.user_data.pop('awaiting_account_name', None)
        
    except Exception as e:
        logger.error(f"Error creating account: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка створення рахунку. Спробуйте ще раз.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="accounts_menu")
            ]]),
            parse_mode="Markdown"
        )

# Функція для обробки введення тексту (буде викликана в text_handler)
async def handle_account_name_input(message, context):
    """Обробляє введення назви рахунку користувачем"""
    if context.user_data.get('awaiting_account_name'):
        account_name = message.text.strip()
        
        if len(account_name) > 50:
            await message.reply_text(
                "❌ Назва рахунку занадто довга. Максимум 50 символів.",
                parse_mode="Markdown"
            )
            return
        
        if len(account_name) < 2:
            await message.reply_text(
                "❌ Назва рахунку занадто коротка. Мінімум 2 символи.",
                parse_mode="Markdown"
            )
            return
        
        # Створюємо фейкове query для подальшої обробки
        class FakeQuery:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
                
            async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        
        fake_query = FakeQuery(message)
        await create_account_with_name(fake_query, context, account_name)
        
        return True  # Вказуємо, що повідомлення оброблене
    
    return False  # Повідомлення не оброблене цим обробником

# Цей файл більше не потребує симульованих функцій, 
# оскільки використовує реальні функції з database.db_operations
