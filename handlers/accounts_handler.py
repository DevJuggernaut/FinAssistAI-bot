"""
Модуль для управління рахунками користувача
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
from datetime import datetime
import logging

from database.db_operations import get_or_create_user, get_user_accounts, get_total_balance, get_accounts_count, create_account, transfer_between_accounts
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
        
        message = f"💳 **Управління рахунками**\n\n"
        message += f"📊 **Поточний стан:**\n"
        message += f"🏦 Кількість рахунків: `{accounts_count}`\n"
        message += f"💰 Загальний баланс: `{total_balance:,.2f} {currency_symbol}`\n\n"
        message += "👆 *Оберіть дію для роботи з рахунками:*"
        
        keyboard = [
            [
                InlineKeyboardButton("📋 Мої рахунки", callback_data="accounts_list"),
                InlineKeyboardButton("➕ Додати рахунок", callback_data="accounts_add")
            ],
            [
                InlineKeyboardButton("💸 Переказ між рахунками", callback_data="accounts_transfer")
            ],
            [
                InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
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
                InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
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
            message = "💳 **Мої рахунки**\n\n"
            message += "📭 У вас ще немає створених рахунків.\n\n"
            message += "💡 **Створіть перший рахунок для початку роботи:**\n\n"
            message += "💵 **Готівка** — для щоденних трат\n"
            message += "💳 **Банківська картка** — основний рахунок\n"
            message += "💰 **Ощадний рахунок** — для накопичень\n"
            message += "📈 **Інвестиційний** — для інвестицій\n\n"
            message += "👆 *Почніть з будь-якого типу рахунку*"
            
            keyboard = [
                [InlineKeyboardButton("➕ Створити рахунок", callback_data="accounts_add")],
                [InlineKeyboardButton("◀️ Рахунки", callback_data="accounts_menu")]
            ]
        else:
            message = f"💳 **Мої рахунки**\n\n"
            
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
                    InlineKeyboardButton("⚙️ Налаштування", callback_data="accounts_settings")
                ],
                [InlineKeyboardButton("◀️ Рахунки", callback_data="accounts_menu")]
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
                InlineKeyboardButton("◀️ Рахунки", callback_data="accounts_menu")
            ]]),
            parse_mode="Markdown"
        )

async def show_add_account_form(query, context):
    """Показує форму для додавання нового рахунку"""
    message = f"➕ **Створення рахунку**\n\n"
    message += "Оберіть тип рахунку:\n\n"
    message += "💵 **Готівка** — для щоденних витрат\n"
    message += "💳 **Картка** — дебетова або кредитна\n"
    message += "🏦 **Банк** — депозитний рахунок\n"
    message += "💰 **Ощадний** — для накопичень\n"
    message += "📈 **Інвестиційний** — цінні папери\n"
    message += "🌐 **Криптовалюта** — цифровий гаманець\n\n"
    message += "👆 *Оберіть підходящий тип*"
    
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
            InlineKeyboardButton("◀️ Рахунки", callback_data="accounts_menu")
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
        message = "💸 **Переказ між рахунками**\n\n"
        message += "❌ Для переказу потрібно мати принаймні 2 рахунки.\n\n"
        message += "💡 **Створіть додатковий рахунок:**\n"
        message += "• Банківська картка\n"
        message += "• Ощадний рахунок\n"
        message += "• Готівковий рахунок\n\n"
        message += "👆 *Після створення ви зможете переказувати кошти*"
        
        keyboard = [
            [InlineKeyboardButton("➕ Створити рахунок", callback_data="accounts_add")],
            [InlineKeyboardButton("◀️ Назад до рахунків", callback_data="accounts_menu")]
        ]
    else:
        currency = user.currency or "UAH"
        currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
        
        message = "💸 **Переказ між рахунками**\n\n"
        message += "📤 **Крок 1: Оберіть рахунок-джерело**\n\n"
        message += "Оберіть рахунок, з якого хочете переказати кошти:\n\n"
        
        # Показуємо тільки рахунки з позитивним балансом
        available_accounts = [acc for acc in accounts if acc.balance > 0]
        
        if not available_accounts:
            message = "💸 **Переказ між рахунками**\n\n"
            message += "❌ Немає рахунків з доступними коштами для переказу.\n\n"
            message += "💡 **Для переказу потрібен рахунок з позитивним балансом:**\n"
            message += "• Додайте доходи до існуючих рахунків\n"
            message += "• Або створіть новий рахунок з початковим балансом\n\n"
            
            keyboard = [
                [InlineKeyboardButton("➕ Додати дохід", callback_data="add_income")],
                [InlineKeyboardButton("◀️ Назад до рахунків", callback_data="accounts_menu")]
            ]
        else:
            # Показуємо доступні рахунки
            for account in available_accounts:
                balance_text = f"{account.balance:,.2f} {currency_symbol}"
                message += f"{account.icon} **{account.name}**\n"
                message += f"   💰 `{balance_text}`\n\n"
            
            # Створюємо кнопки для вибору рахунку-джерела
            keyboard = []
            for account in available_accounts:
                button_text = f"{account.icon} {account.name} ({account.balance:,.0f} {currency_symbol})"
                callback_data = f"transfer_from_{account.id}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            keyboard.append([InlineKeyboardButton("◀️ Назад до рахунків", callback_data="accounts_menu")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_transfer_destination(query, context, from_account_id):
    """Показує список рахунків для вибору призначення переказу"""
    user = get_or_create_user(query.from_user.id)
    accounts = get_user_accounts(user.id)
    
    # Знаходимо рахунок-джерело
    from_account = next((acc for acc in accounts if acc.id == from_account_id), None)
    if not from_account:
        await query.edit_message_text(
            "❌ Рахунок-джерело не знайдено",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад до рахунків", callback_data="accounts_menu")
            ]]),
            parse_mode="Markdown"
        )
        return
    
    # Показуємо всі інші рахунки як можливі призначення
    destination_accounts = [acc for acc in accounts if acc.id != from_account_id]
    
    currency = user.currency or "UAH"
    currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
    
    message = "💸 **Переказ між рахунками**\n\n"
    message += f"📤 **Джерело:** {from_account.icon} {from_account.name}\n"
    message += f"   💰 Доступно: `{from_account.balance:,.2f} {currency_symbol}`\n\n"
    message += "📋 **Крок 2: Оберіть рахунок-призначення**\n\n"
    
    if not destination_accounts:
        message += "❌ Немає інших рахунків для переказу."
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="accounts_transfer")]]
    else:
        for account in destination_accounts:
            balance_text = f"{account.balance:,.2f} {currency_symbol}"
            message += f"{account.icon} **{account.name}**\n"
            message += f"   💰 `{balance_text}`\n\n"
        
        # Створюємо кнопки для вибору рахунку-призначення
        keyboard = []
        for account in destination_accounts:
            button_text = f"{account.icon} {account.name}"
            callback_data = f"transfer_to_{from_account_id}_{account.id}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("◀️ Вибір джерела", callback_data="accounts_transfer")])
    
    # Зберігаємо ID рахунку-джерела в контексті
    context.user_data['transfer_from_account'] = from_account_id
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_transfer_amount_input(query, context, from_account_id, to_account_id):
    """Показує форму для введення суми переказу"""
    user = get_or_create_user(query.from_user.id)
    accounts = get_user_accounts(user.id)
    
    from_account = next((acc for acc in accounts if acc.id == from_account_id), None)
    to_account = next((acc for acc in accounts if acc.id == to_account_id), None)
    
    if not from_account or not to_account:
        await query.edit_message_text(
            "❌ Один з рахунків не знайдено",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад до рахунків", callback_data="accounts_menu")
            ]]),
            parse_mode="Markdown"
        )
        return
    
    currency = user.currency or "UAH"
    currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
    
    message = "💸 **Переказ між рахунками**\n\n"
    message += f"📤 **З рахунку:** {from_account.icon} {from_account.name}\n"
    message += f"   💰 Доступно: `{from_account.balance:,.2f} {currency_symbol}`\n\n"
    message += f"📥 **На рахунок:** {to_account.icon} {to_account.name}\n"
    message += f"   💰 Поточний баланс: `{to_account.balance:,.2f} {currency_symbol}`\n\n"
    message += "📋 **Крок 3: Введіть суму переказу**\n\n"
    message += f"💰 Введіть суму для переказу в {currency_symbol}:\n\n"
    message += "💡 **Приклади:**\n"
    message += "• `1000` — одна тисяча\n"
    message += "• `500.50` — з копійками\n"
    message += f"• `{from_account.balance:,.0f}` — весь баланс\n\n"
    message += f"👆 *Максимум: {from_account.balance:,.2f} {currency_symbol}*\n\n"
    message += "✍️ **Напишіть суму в наступному повідомленні**"
    
    keyboard = [
        [InlineKeyboardButton("◀️ Вибір призначення", callback_data=f"transfer_from_{from_account_id}")]
    ]
    
    # Зберігаємо дані переказу в контексті
    context.user_data['transfer_data'] = {
        'from_account_id': from_account_id,
        'to_account_id': to_account_id
    }
    context.user_data['awaiting_transfer_amount'] = True
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def execute_transfer(query, context, from_account_id, to_account_id, amount):
    """Виконує переказ між рахунками"""
    try:
        user = get_or_create_user(query.from_user.id)
        accounts = get_user_accounts(user.id)
        
        from_account = next((acc for acc in accounts if acc.id == from_account_id), None)
        to_account = next((acc for acc in accounts if acc.id == to_account_id), None)
        
        if not from_account or not to_account:
            await query.edit_message_text(
                "❌ Один з рахунків не знайдено",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Назад до рахунків", callback_data="accounts_menu")
                ]]),
                parse_mode="Markdown"
            )
            return
        
        # Виконуємо переказ
        success, message_text = transfer_between_accounts(
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            amount=amount,
            description="Переказ через бота"
        )
        
        currency = user.currency or "UAH"
        currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
        
        if success:
            # Оновлюємо дані рахунків після переказу
            updated_accounts = get_user_accounts(user.id)
            updated_from = next((acc for acc in updated_accounts if acc.id == from_account_id), None)
            updated_to = next((acc for acc in updated_accounts if acc.id == to_account_id), None)
            
            success_message = "✅ **Переказ виконано успішно!**\n\n"
            success_message += f"💸 **Переказано:** `{amount:,.2f} {currency_symbol}`\n\n"
            success_message += f"📤 **З рахунку:** {from_account.icon} {from_account.name}\n"
            if updated_from:
                success_message += f"   💰 Залишок: `{updated_from.balance:,.2f} {currency_symbol}`\n\n"
            success_message += f"📥 **На рахунок:** {to_account.icon} {to_account.name}\n"
            if updated_to:
                success_message += f"   💰 Новий баланс: `{updated_to.balance:,.2f} {currency_symbol}`\n\n"
            success_message += f"📅 Дата операції: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            success_message += "💡 **Переказ записано в історію транзакцій**"
            
            keyboard = [
                [
                    InlineKeyboardButton("📋 Мої рахунки", callback_data="accounts_list"),
                    InlineKeyboardButton("🔄 Ще переказ", callback_data="accounts_transfer")
                ],
                [
                    InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
                ]
            ]
        else:
            success_message = f"❌ **Помилка переказу**\n\n"
            success_message += f"Деталі: {message_text}\n\n"
            success_message += "💡 Можливі причини:\n"
            success_message += "• Недостатньо коштів на рахунку\n"
            success_message += "• Рахунок заблокований\n"
            success_message += "• Технічна помилка\n\n"
            success_message += "Спробуйте ще раз або зверніться до підтримки."
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Спробувати знову", callback_data="accounts_transfer"),
                    InlineKeyboardButton("📋 Мої рахунки", callback_data="accounts_list")
                ],
                [
                    InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
                ]
            ]
        
        await query.edit_message_text(
            success_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        # Очищаємо дані переказу
        context.user_data.pop('transfer_data', None)
        context.user_data.pop('awaiting_transfer_amount', None)
        
    except Exception as e:
        logger.error(f"Error executing transfer: {str(e)}")
        await query.edit_message_text(
            f"❌ **Критична помилка переказу**\n\n"
            f"Деталі: {str(e)}\n\n"
            f"💡 Зверніться до підтримки бота.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад до рахунків", callback_data="accounts_menu")
            ]]),
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
    
    message = f"{icon} **Крок 1: Назва рахунку**\n\n"
    message += "📝 Введіть назву для рахунку:\n\n"
    message += "💡 **Приклади:**\n"
    message += "• Основна картка\n"
    message += "• Готівка\n"
    message += "• ПриватБанк\n"
    message += "• Ощадження\n\n"
    message += f"👆 *Або використайте: {account_type}*\n\n"
    message += "📋 *Наступним кроком буде введення початкового балансу*"
    
    keyboard = [
        [InlineKeyboardButton(f"✅ {account_type}", callback_data="accounts_use_default_name")],
        [InlineKeyboardButton("◀️ Тип рахунку", callback_data="accounts_add")],
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
    
    # Зберігаємо назву і переходимо до введення балансу
    context.user_data['account_creation']['name'] = account_name
    await show_account_balance_input(query, context)

async def show_account_balance_input(query, context):
    """Показує форму для введення початкового балансу рахунку"""
    account_data = context.user_data.get('account_creation', {})
    account_name = account_data.get('name', 'Новий рахунок')
    icon = account_data.get('icon', '💳')
    
    user = get_or_create_user(query.from_user.id)
    currency = user.currency or "UAH"
    currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
    
    message = f"{icon} **Крок 2: Початковий баланс**\n\n"
    message += f"📝 Рахунок: *{account_name}*\n\n"
    message += f"💰 Введіть початковий баланс рахунку в {currency_symbol}:\n\n"
    message += "💡 **Приклади:**\n"
    message += "• `5000` — п'ять тисяч\n"
    message += "• `12500.50` — з копійками\n"
    message += "• `0` — порожній рахунок\n\n"
    message += f"✍️ **Напишіть суму в наступному повідомленні**"
    
    keyboard = [
        [
            InlineKeyboardButton("◀️ Назва рахунку", callback_data="accounts_edit_name"),
            InlineKeyboardButton("❌ Скасувати", callback_data="accounts_menu")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Зберігаємо стан очікування введення балансу
    context.user_data['awaiting_account_balance'] = True



async def create_account_with_balance(query, context, account_name, balance):
    """Створює рахунок з вказаною назвою та балансом"""
    try:
        user = get_or_create_user(query.from_user.id)
        account_data = context.user_data.get('account_creation', {})
        
        # Мапимо типи з тих, що використовуються в UI, на AccountType з моделі
        type_mapping = {
            'cash': AccountType.CASH,
            'card': AccountType.BANK_CARD,
            'bank': AccountType.BANK_CARD,  # Банківський рахунок як картка
            'savings': AccountType.SAVINGS,
            'investment': AccountType.INVESTMENT,
            'crypto': AccountType.OTHER,  # Криптовалюта як інше
            'other': AccountType.OTHER
        }
        
        account_type_key = account_data.get('type', 'other')
        account_type = type_mapping.get(account_type_key, AccountType.OTHER)
        
        # Створюємо рахунок в базі даних
        new_account = create_account(
            user_id=user.id,
            name=account_name,
            account_type=account_type,
            balance=balance,
            currency=user.currency or 'UAH',
            is_main=False,  # Головний рахунок встановлюється окремо
            icon=account_data.get('icon', '💳'),
            description=f"Створено через бота - {account_type_key.title()}"
        )
        
        currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(user.currency or 'UAH', '₴')
        
        success_message = f"✅ **Рахунок успішно створено!**\n\n"
        success_message += f"{account_data.get('icon', '💳')} **{account_name}**\n"
        success_message += f"📝 Тип: {account_type_key.replace('_', ' ').title()}\n"
        success_message += f"💰 Початковий баланс: `{balance:,.2f} {currency_symbol}`\n"
        success_message += f"🆔 ID рахунку: `{new_account.id}`\n\n"
        
        if balance > 0:
            success_message += "💡 **Рахунок готовий до використання!**\n"
            success_message += "• Додавайте нові доходи та витрати\n"
            success_message += "• Переказуйте кошти між рахунками\n"
            success_message += "• Відстежуйте зміни балансу\n"
            success_message += "• Переглядайте статистику по рахунку"
        else:
            success_message += "💡 **Рахунок створено з нульовим балансом:**\n"
            success_message += "• Додайте перший дохід для поповнення\n"
            success_message += "• Введіть початкові кошти як транзакцію\n"
            success_message += "• Переказуйте кошти з інших рахунків"
        
        keyboard = [
            [
                InlineKeyboardButton("📋 Мої рахунки", callback_data="accounts_list"),
                InlineKeyboardButton("➕ Створити ще", callback_data="accounts_add")
            ],
            [
                InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
            ]
        ]
        
        await query.edit_message_text(
            success_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        # Очищаємо дані створення рахунку
        context.user_data.pop('account_creation', None)
        context.user_data.pop('awaiting_account_name', None)
        context.user_data.pop('awaiting_account_balance', None)
        
    except Exception as e:
        logger.error(f"Error creating account: {str(e)}")
        await query.edit_message_text(
            f"❌ **Помилка створення рахунку**\n\n"
            f"Деталі: {str(e)}\n\n"
            f"💡 Спробуйте ще раз або зверніться до підтримки.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад до рахунків", callback_data="accounts_menu")
            ]]),
            parse_mode="Markdown"
        )

# Функція для обробки введення тексту (буде викликана в text_handler)
async def handle_account_text_input(message, context):
    """Обробляє введення тексту користувачем для рахунків"""
    logger.info(f"handle_account_text_input called with text: '{message.text}'")
    logger.info(f"Context user_data: {context.user_data}")
    
    # Обробка введення назви рахунку
    if context.user_data.get('awaiting_account_name'):
        logger.info("Processing as account name input")
        account_name = message.text.strip()
        
        # Перевірка довжини назви
        if len(account_name) > 50:
            await message.reply_text(
                "❌ **Назва занадто довга**\n\n"
                "Максимальна довжина: 50 символів\n"
                "Поточна довжина: {}\n\n"
                "💡 Спробуйте коротшу назву".format(len(account_name)),
                parse_mode="Markdown"
            )
            return True
        
        if len(account_name) < 2:
            await message.reply_text(
                "❌ **Назва занадто коротка**\n\n"
                "Мінімальна довжина: 2 символи\n\n"
                "💡 Введіть більш описову назву",
                parse_mode="Markdown"
            )
            return True
        
        # Перевірка на заборонені символи
        forbidden_chars = ['<', '>', '&', '"', "'", '`']
        if any(char in account_name for char in forbidden_chars):
            await message.reply_text(
                "❌ **Недозволені символи**\n\n"
                f"Заборонені символи: {', '.join(forbidden_chars)}\n\n"
                "💡 Використовуйте тільки букви, цифри та базові знаки пунктуації",
                parse_mode="Markdown"
            )
            return True
        
        try:
            # Зберігаємо назву і переходимо до введення балансу
            context.user_data['account_creation']['name'] = account_name
            context.user_data.pop('awaiting_account_name', None)
            
            # Створюємо фейкове query для переходу до введення балансу
            class FakeQuery:
                def __init__(self, message):
                    self.message = message
                    self.from_user = message.from_user
                    
                async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                    await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            
            fake_query = FakeQuery(message)
            await show_account_balance_input(fake_query, context)
            
        except Exception as e:
            logger.error(f"Error handling account name input: {str(e)}")
            await message.reply_text(
                "❌ **Помилка при обробці назви рахунку**\n\n"
                "Спробуйте ще раз або зверніться до підтримки.",
                parse_mode="Markdown"
            )
        
        return True  # Вказуємо, що повідомлення оброблене
    
    # Обробка введення балансу рахунку
    elif context.user_data.get('awaiting_account_balance'):
        logger.info("Processing as account balance input")
        balance_text = message.text.strip()
        
        try:
            # Парсимо суму
            balance = float(balance_text.replace(',', '.'))
            
            if balance < 0:
                await message.reply_text(
                    "❌ **Від'ємний баланс недозволений**\n\n"
                    "💡 Введіть позитивну суму або 0",
                    parse_mode="Markdown"
                )
                return True
            
            if balance > 999999999:
                await message.reply_text(
                    "❌ **Сума занадто велика**\n\n"
                    "Максимум: 999,999,999\n\n"
                    "💡 Введіть реальну суму",
                    parse_mode="Markdown"
                )
                return True
                
            # Створюємо рахунок з введеним балансом
            account_data = context.user_data.get('account_creation', {})
            account_name = account_data.get('name', 'Новий рахунок')
            
            class FakeQuery:
                def __init__(self, message):
                    self.message = message
                    self.from_user = message.from_user
                    
                async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                    await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            
            fake_query = FakeQuery(message)
            await create_account_with_balance(fake_query, context, account_name, balance)
            
        except ValueError:
            await message.reply_text(
                "❌ **Неправильний формат суми**\n\n"
                "💡 **Приклади правильного формату:**\n"
                "• `5000`\n"
                "• `12500.50`\n"
                "• `0`\n\n"
                "Спробуйте ще раз:",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error handling account balance input: {str(e)}")
            await message.reply_text(
                "❌ **Помилка при обробці суми**\n\n"
                "Спробуйте ще раз або зверніться до підтримки.",
                parse_mode="Markdown"
            )
        
        return True  # Вказуємо, що повідомлення оброблене
    
    # Обробка введення суми переказу
    elif context.user_data.get('awaiting_transfer_amount'):
        amount_text = message.text.strip()
        transfer_data = context.user_data.get('transfer_data', {})
        
        try:
            # Парсимо суму
            amount = float(amount_text.replace(',', '.'))
            
            if amount <= 0:
                await message.reply_text(
                    "❌ **Сума повинна бути більше нуля**\n\n"
                    "💡 Введіть позитивну суму для переказу",
                    parse_mode="Markdown"
                )
                return True
            
            # Перевіряємо доступний баланс
            user = get_or_create_user(message.from_user.id)
            accounts = get_user_accounts(user.id)
            from_account = next((acc for acc in accounts if acc.id == transfer_data.get('from_account_id')), None)
            
            if not from_account:
                await message.reply_text(
                    "❌ **Рахунок-джерело не знайдено**\n\n"
                    "💡 Почніть переказ заново",
                    parse_mode="Markdown"
                )
                return True
            
            if amount > from_account.balance:
                currency = user.currency or "UAH"
                currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
                await message.reply_text(
                    f"❌ **Недостатньо коштів**\n\n"
                    f"Доступно: `{from_account.balance:,.2f} {currency_symbol}`\n"
                    f"Запитано: `{amount:,.2f} {currency_symbol}`\n\n"
                    f"💡 Введіть суму не більше {from_account.balance:,.2f}",
                    parse_mode="Markdown"
                )
                return True
                
            # Виконуємо переказ
            class FakeQuery:
                def __init__(self, message):
                    self.message = message
                    self.from_user = message.from_user
                    
                async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                    await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            
            fake_query = FakeQuery(message)
            await execute_transfer(
                fake_query, 
                context, 
                transfer_data.get('from_account_id'), 
                transfer_data.get('to_account_id'), 
                amount
            )
            
        except ValueError:
            await message.reply_text(
                "❌ **Неправильний формат суми**\n\n"
                "💡 **Приклади правильного формату:**\n"
                "• `1000`\n"
                "• `500.50`\n"
                "• `250`\n\n"
                "Спробуйте ще раз:",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error handling transfer amount input: {str(e)}")
            await message.reply_text(
                "❌ **Помилка при обробці суми**\n\n"
                "Спробуйте ще раз або зверніться до підтримки.",
                parse_mode="Markdown"
            )
        
        return True  # Вказуємо, що повідомлення оброблене
    
    return False  # Повідомлення не оброблене цим обробником

# Цей файл більше не потребує симульованих функцій, 
# оскільки використовує реальні функції з database.db_operations
