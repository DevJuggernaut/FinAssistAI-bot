from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database.db_operations import get_user, get_or_create_user, get_user_categories
from database.session import Session
from database.models import User, Category, TransactionType, Transaction
from datetime import datetime
        ("Одяг", "👚"),
        ("Здоров'я", "🏥"),
        ("Освіта", "📚"),
        ("Техніка", "📱"),
        ("Кафе та ресторани", "☕"),
        ("Спорт", "🏃"),
        ("Подарунки", "🎁"),
        ("Краса", "💄"),
        ("Хобі", "🎨"),
        ("Інше", "📦")
    ]
    
    standard_income_categories = [
        ("Зарплата", "💰"),
        ("Фріланс", "💻"),
        ("Подарунки", "🎁"),
        ("Інвестиції", "📈"),
        ("Продаж", "🏷️"),
        ("Бонуси", "💎"),
        ("Стипендія", "🎓"),
        ("Інше", "💸")
    ]egory, TransactionType, Transaction
from datetime import datetime

# Стани для ConversationHandler
WAITING_CURRENCY_SELECTION = 1
WAITING_BALANCE_INPUT = 2
SETUP_COMPLETE = 3

async def show_currency_selection(update_or_query, context):
    """Починає процес початкового налаштування бота - крок 1: вибір валюти"""
    # Встановлюємо перший крок налаштування
    context.user_data['setup_step'] = 'currency'
    
    # Створюємо кнопки для вибору валюти
    keyboard = [
        [
            InlineKeyboardButton("🇺🇦 UAH (₴)", callback_data="currency_UAH"),
            InlineKeyboardButton("🇺🇸 USD ($)", callback_data="currency_USD")
        ],
        [
            InlineKeyboardButton("🇪🇺 EUR (€)", callback_data="currency_EUR"),
            InlineKeyboardButton("🇬🇧 GBP (£)", callback_data="currency_GBP")
        ],
        [
            InlineKeyboardButton("« Скасувати", callback_data="back_to_main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "🚀 *Налаштування бота - Крок 1 з 2*\n\n"
        "💱 *Оберіть основну валюту*\n\n"
        "Ця валюта буде використовуватись для відображення балансу та операцій.\n"
        "Оберіть валюту, в якій ви зазвичай ведете облік фінансів:"
    )
    
    # Перевіряємо, який тип об'єкта ми отримали
    if hasattr(update_or_query, 'callback_query'):  # Якщо це Update з CallbackQuery
        query = update_or_query.callback_query
        message = await query.edit_message_text(
            message_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        context.user_data['message_id'] = message.message_id
    elif hasattr(update_or_query, 'edit_message_text'):  # Якщо це CallbackQuery
        message = await update_or_query.edit_message_text(
            message_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        context.user_data['message_id'] = message.message_id
    else:  # Якщо це Update без CallbackQuery (наприклад, з команди)
        message = await update_or_query.message.reply_text(
            message_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        context.user_data['message_id'] = message.message_id
    
    return WAITING_CURRENCY_SELECTION

async def process_currency_selection(update_or_query, context):
    """Обробка вибору валюти"""
    # Перевіряємо, який тип об'єкта ми отримали
    if hasattr(update_or_query, 'callback_query'):
        query = update_or_query.callback_query
    else:
        query = update_or_query
    
    # Отримуємо вибрану валюту
    currency_code = query.data.split("_")[1]
    user_id = query.from_user.id
    
    with Session() as session:
        user = session.query(User).filter(User.telegram_id == user_id).first()
        user.currency = currency_code
        session.commit()
    
    # Тепер переходимо до кроку введення балансу
    keyboard = [[InlineKeyboardButton("« Назад", callback_data="back_to_currency")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отримуємо символ валюти для відображення
    currency_symbols = {
        "UAH": "₴",
        "USD": "$",
        "EUR": "€",
        "GBP": "£"
    }
    currency_symbol = currency_symbols.get(currency_code, currency_code)
    
    message_text = (
        "🚀 *Налаштування бота - Крок 2 з 2*\n\n"
        f"✅ Валюта встановлена: {currency_code} ({currency_symbol})\n\n"
        "💰 *Введіть ваш початковий баланс*\n\n"
        f"Вкажіть суму коштів, яку ви маєте зараз (наприклад: 5000).\n"
        "Це допоможе нам правильно відстежувати ваші фінанси.\n\n"
        "Введіть суму в числовому форматі:"
    )
    
    # Перевіряємо, який тип об'єкта ми отримали
    if hasattr(query, 'edit_message_text'):
        await query.edit_message_text(
            message_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await query.message.reply_text(
            message_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    context.user_data['setup_step'] = 'balance'
    
    return WAITING_BALANCE_INPUT

async def back_to_currency(update_or_query, context):
    """Повернення до вибору валюти"""
    return await show_currency_selection(update_or_query, context)

async def process_initial_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка введеного початкового балансу і завершення налаштування"""
    try:
        balance = float(update.message.text.replace(',', '.'))
        user_id = update.effective_user.id
        
        with Session() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            
            # Зберігаємо валюту користувача перед закриттям сесії
            currency_code = user.currency
            user_db_id = user.id
            
            user.initial_balance = balance
            
            # Встановлюємо, що налаштування завершено
            user.setup_step = 'completed'
            user.is_setup_completed = True
            
            session.commit()
            
            # Створюємо початкову транзакцію
            transaction = Transaction(
                user_id=user_db_id,
                amount=balance,
                type=TransactionType.INCOME,
                description="Початковий баланс",
                transaction_date=datetime.utcnow()
            )
            session.add(transaction)
            session.commit()
        
        # Створюємо стандартні категорії для користувача
        await setup_default_categories(user_id)
        
        # Використовуємо збережений currency_code поза сесією
        currency_symbols = {
            "UAH": "₴",
            "USD": "$",
            "EUR": "€",
            "GBP": "£"
        }
        currency_symbol = currency_symbols.get(currency_code, currency_code)
        
        # Показуємо повідомлення про успішне завершення налаштування
        # Створюємо кнопки головного меню для завершення налаштування
        keyboard = [
            [
                InlineKeyboardButton("💰 Мій бюджет", callback_data="my_budget")
            ],
            [
                InlineKeyboardButton("💳 Додати транзакцію", callback_data="add_transaction")
            ],
            [
                InlineKeyboardButton("📊 Аналітика", callback_data="analytics")
            ],
            [
                InlineKeyboardButton("⚙️ Налаштування", callback_data="settings")
            ],
            [
                InlineKeyboardButton("❓ Допомога", callback_data="help")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Відправляємо єдине повідомлення про завершення налаштування з головним меню
        completion_message = (
            "🎉 *Налаштування успішно завершено!*\n\n"
            f"✅ Валюта: {currency_code} ({currency_symbol})\n"
            f"✅ Початковий баланс: {balance} {currency_symbol}\n\n"
            "Тепер ви можете повноцінно користуватися усіма функціями бота FinAssist.\n\n"
            "*Що робити далі:*\n"
            "• Додайте ваші регулярні доходи і витрати\n"
            "• Перегляньте аналітику в розділі 'Мій бюджет'\n"
            "• Налаштуйте категорії в розділі 'Налаштування'\n\n"
            "Дякуємо, що обрали нашого бота для керування фінансами! 💼"
        )
        
        await update.message.reply_text(
            completion_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Будь ласка, введіть коректне число (наприклад: 5000)."
        )
    
    return WAITING_BALANCE_INPUT

async def complete_setup(query, context):
    """Завершує процес початкового налаштування бота"""
    user_id = query.from_user.id
    
    # Встановлюємо, що налаштування бота завершено
    with Session() as session:
        user = session.query(User).filter(User.telegram_id == user_id).first()
        user.is_setup_completed = True
        user.setup_step = 'completed'
        session.commit()
    
    keyboard = [
        [
            InlineKeyboardButton("💰 Мій бюджет", callback_data="my_budget"),
            InlineKeyboardButton("➕ Додати операцію", callback_data="add_transaction")
        ],
        [
            InlineKeyboardButton("📊 Аналітика", callback_data="analytics"),
            InlineKeyboardButton("⚙️ Налаштування", callback_data="settings")
        ],
        [
            InlineKeyboardButton("❓ Допомога", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎉 *Налаштування бота успішно завершено!*\n\n"
        "Тепер ви можете повноцінно користуватися усіма функціями бота FinAssist.\n\n"
        "Рекомендуємо почати з додавання ваших перших фінансових операцій, "
        "щоб ми могли надати вам корисну аналітику та поради.\n\n"
        "*Що робити далі:*\n"
        "• Додайте ваші регулярні доходи і витрати\n"
        "• Перегляньте аналітику в розділі 'Мій бюджет'\n"
        "• Налаштуйте категорії в розділі 'Налаштування'\n\n"
        "Дякуємо, що обрали нашого бота для керування фінансами! 💼",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

async def setup_default_categories(user_id):
    """Створює стандартні категорії витрат та доходів для користувача"""
    user = get_or_create_user(user_id)
    
    categories = get_user_categories(user.id)
    expense_categories = [c for c in categories if c.type == TransactionType.EXPENSE]
    income_categories = [c for c in categories if c.type == TransactionType.INCOME]
    
    # Формуємо список стандартних категорій
    standard_expense_categories = [
        ("Продукти", "🥗"),
        ("Транспорт", "🚌"),
        ("Житло", "🏠"),
        ("Комунальні послуги", "��"),
        ("Розваги", "🎭"),
        ("Одяг", "👚"),
        ("Здоров'я", "🏥"),
        ("Освіта", "📚"),
        ("Техніка", "📱")
    ]
    
    standard_income_categories = [
        ("Зарплата", "💰"),
        ("Фріланс", "💻"),
        ("Подарунки", "🎁"),
        ("Інвестиції", "📈"),
        ("Продаж", "🏷️")
    ]
    
    # Додаємо стандартні категорії для користувача
    with Session() as session:
        if not expense_categories:
            for name, emoji in standard_expense_categories:
                category = Category(
                    user_id=user.id,
                    name=name,
                    type=TransactionType.EXPENSE,
                    icon=emoji
                )
                session.add(category)
            
        if not income_categories:
            for name, emoji in standard_income_categories:
                category = Category(
                    user_id=user.id,
                    name=name,
                    type=TransactionType.INCOME,
                    icon=emoji
                )
                session.add(category)
        
        session.commit()
