from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database.session import Session
from database.models import User, Transaction, TransactionType
from datetime import datetime

# Стани розмови
SETUP_START, SETUP_BALANCE, SETUP_BUDGET, SETUP_NOTIFICATIONS = range(4)

async def start_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Початок процесу налаштування з вітанням для нових користувачів"""
    user_id = update.effective_user.id
    
    with Session() as session:
        user = session.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            user = User(
                telegram_id=user_id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name,
                last_name=update.effective_user.last_name
            )
            session.add(user)
            session.commit()
            
            # Для нового користувача не встановлюємо налаштування як завершені
            user.setup_step = 'start'
            user.is_setup_completed = False
            session.commit()
    
    # Отримуємо ім'я користувача
    first_name = update.effective_user.first_name or "друже"
    
    # Перевіряємо, чи користувач налаштував бота
    with Session() as session:
        user = session.query(User).filter(User.telegram_id == user_id).first()
        is_setup_complete = user and user.is_setup_completed
    
    # Якщо налаштування не завершено, показуємо привітання з єдиною кнопкою
    if not is_setup_complete:
        keyboard = [
            [
                InlineKeyboardButton("🚀 Налаштувати бота", callback_data="setup_initial_balance")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Привітання для нових користувачів
        message_text = (
            f"👋 *Вітаємо, {first_name}, у FinAssist!*\n\n"
            "*Ваш особистий помічник для контролю фінансів*\n\n"
            "*Основні функції бота:*\n"
            "• Облік доходів та витрат\n"
            "• Аналіз фінансів та статистика\n"
            "• Управління бюджетом\n"
            "• Персоналізовані фінансові поради\n\n"
            "*⚠️ Для початку роботи необхідно налаштувати бота*\n"
            "Натисніть на кнопку нижче щоб розпочати процес налаштування.\n"
            "Вам потрібно буде:\n"
            "1️⃣ Встановити початковий баланс\n"
            "2️⃣ Вказати місячний бюджет\n\n"
        )
        
        await update.message.reply_text(
            message_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        # Для вже налаштованих користувачів показуємо привітання і головне меню через єдину функцію
        from handlers.main_menu import show_main_menu
        
        # Привітання для вже налаштованих користувачів
        welcome_message = (
            f"👋 *З поверненням, {first_name}!*\n\n"
            "*Ваш особистий помічник для контролю фінансів*\n\n"
            "*Основні функції бота:*\n"
            "• Облік доходів та витрат\n"
            "• Аналіз фінансів та статистика\n"
            "• Управління бюджетом\n"
            "• Персоналізовані фінансові поради\n\n"
            "📌 *⚙️ Налаштування* — персоналізація бота під ваші потреби\n\n"
            "*Порада:* Почніть з розділу 'Мій бюджет', а потім додайте перші операції!"
        )
        
        # Відправляємо привітання
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown'
        )
        
        # Показуємо головне меню через єдину функцію
        await show_main_menu(update.message, context, is_query=False)
    return ConversationHandler.END

async def setup_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка введення початкового балансу"""
    try:
        balance = float(update.message.text.replace(',', '.'))
        user_id = update.effective_user.id
        
        with Session() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            user.initial_balance = balance
            user.setup_step = 'balance'
            currency = user.currency
            
            # Створюємо початкову транзакцію
            transaction = Transaction(
                user_id=user.id,
                amount=balance,
                type=TransactionType.INCOME,
                description="Початковий баланс",
                transaction_date=datetime.utcnow()
            )
            session.add(transaction)
            session.commit()
        
        await update.message.reply_text(
            f"Чудово! Ваш початковий баланс встановлено: {balance} {currency}\n\n"
            "Тепер вкажіть ваш місячний бюджет (наприклад: 5000):"
        )
        return SETUP_BUDGET
        
    except ValueError:
        await update.message.reply_text(
            "Будь ласка, введіть коректне число (наприклад: 1000):"
        )
        return SETUP_BALANCE

async def setup_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка введення місячного бюджету"""
    try:
        budget = float(update.message.text.replace(',', '.'))
        user_id = update.effective_user.id
        
        with Session() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            user.monthly_budget = budget
            user.setup_step = 'budget'
            currency = user.currency
            session.commit()
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Увімкнути", callback_data="notifications_on"),
                InlineKeyboardButton("❌ Вимкнути", callback_data="notifications_off")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Чудово! Ваш місячний бюджет встановлено: {budget} {currency}\n\n"
            "Бажаєте отримувати сповіщення про витрати та доходи?",
            reply_markup=reply_markup
        )
        return SETUP_NOTIFICATIONS
        
    except ValueError:
        await update.message.reply_text(
            "Будь ласка, введіть коректне число (наприклад: 5000):"
        )
        return SETUP_BUDGET

async def setup_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка налаштування сповіщень"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    notifications_enabled = query.data == "notifications_on"
    
    with Session() as session:
        user = session.query(User).filter(User.telegram_id == user_id).first()
        user.notification_enabled = notifications_enabled
        user.setup_step = 'completed'
        user.is_setup_completed = True
        session.commit()
    
    await query.edit_message_text(
        f"Налаштування завершено! 🎉\n\n"
        f"Ваш початковий баланс: {user.initial_balance} {user.currency}\n"
        f"Місячний бюджет: {user.monthly_budget} {user.currency}\n"
        f"Сповіщення: {'увімкнено' if notifications_enabled else 'вимкнено'}\n\n"
        "Тепер ви можете використовувати всі функції бота:\n"
        "/help - показати список команд\n"
        "/settings - змінити налаштування\n"
        "/balance - перевірити баланс\n"
        "/add - додати транзакцію"
    )
    return ConversationHandler.END

async def cancel_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Скасування процесу налаштування"""
    await update.message.reply_text(
        "Налаштування скасовано. Ви можете почати знову командою /start"
    )
    return ConversationHandler.END 