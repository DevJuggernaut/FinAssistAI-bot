from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from database.models import User, Transaction, Category, TransactionType
from database.session import Session
from datetime import datetime
from .setup_handler import (
    start_setup, setup_balance, setup_budget, setup_notifications,
    cancel_setup, SETUP_START, SETUP_BALANCE, SETUP_BUDGET, SETUP_NOTIFICATIONS
)

# Стани для ConversationHandler
INITIAL_BALANCE, MONTHLY_BUDGET, CURRENCY, NOTIFICATIONS = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /start"""
    return await start_setup(update, context)

async def setup_initial_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник введення початкового балансу"""
    try:
        balance = float(update.message.text)
        session = Session()
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        
        user.initial_balance = balance
        session.commit()
        
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
            f"✅ Початковий баланс встановлено: {balance} грн\n\n"
            "Тепер встановіть ваш місячний бюджет (в гривнях):"
        )
        return MONTHLY_BUDGET
        
    except ValueError:
        await update.message.reply_text(
            "❌ Будь ласка, введіть коректну суму (наприклад: 1000)"
        )
        return INITIAL_BALANCE

async def setup_monthly_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник введення місячного бюджету"""
    try:
        budget = float(update.message.text)
        session = Session()
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        
        user.monthly_budget = budget
        session.commit()
        
        # Створюємо бюджетний план
        from database.models import BudgetPlan
        budget_plan = BudgetPlan(
            user_id=user.id,
            name="Місячний бюджет",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow().replace(day=28) + datetime.timedelta(days=4),
            total_budget=budget
        )
        session.add(budget_plan)
        session.commit()
        
        await update.message.reply_text(
            f"✅ Місячний бюджет встановлено: {budget} грн\n\n"
            "Чи хочете ви отримувати сповіщення про витрати? (так/ні)"
        )
        return NOTIFICATIONS
        
    except ValueError:
        await update.message.reply_text(
            "❌ Будь ласка, введіть коректну суму (наприклад: 5000)"
        )
        return MONTHLY_BUDGET

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
        initial_balance = user.initial_balance
        currency = user.currency
        monthly_budget = user.monthly_budget
        session.commit()
    
    await query.edit_message_text(
        f"Налаштування завершено! 🎉\n\n"
        f"Ваш початковий баланс: {initial_balance} {currency}\n"
        f"Місячний бюджет: {monthly_budget} {currency}\n"
        f"Сповіщення: {'увімкнено' if notifications_enabled else 'вимкнено'}\n\n"
        "Тепер ви можете використовувати всі функції бота:\n"
        "/help - показати список команд\n"
        "/settings - змінити налаштування\n"
        "/balance - перевірити баланс\n"
        "/add - додати транзакцію"
    )
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /help зі стислим описом функцій"""
    user_id = update.effective_user.id
    
    with Session() as session:
        user = session.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            user = User(
                telegram_id=user_id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name,
                last_name=update.effective_user.last_name,
                is_setup_completed=True
            )
            session.add(user)
            session.commit()
    
    help_text = (
        "*FinAssist - Команди*\n\n"
        "💰 *Фінанси*\n"
        "/add - додати транзакцію\n"
        "/balance - перевірити баланс\n"
        "/stats - статистика витрат\n\n"
        
        "📊 *Аналітика*\n"
        "/report - фінансовий звіт\n"
        "/budget - керувати бюджетом\n"
        "/advice - отримати поради\n\n"
        
        "⚙️ /settings - налаштування\n\n"
        
        "*Швидкий старт:* просто надішліть суму та опис (наприклад: 120 обід)"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /settings"""
    user_id = update.effective_user.id
    
    with Session() as session:
        user = session.query(User).filter(User.telegram_id == user_id).first()
        if not user or not user.is_setup_completed:
            await update.message.reply_text(
                "Будь ласка, спочатку завершіть налаштування бота командою /start"
            )
            return
    
    settings_text = (
        f"⚙️ Ваші поточні налаштування:\n\n"
        f"💰 Початковий баланс: {user.initial_balance} {user.currency}\n"
        f"📊 Місячний бюджет: {user.monthly_budget} {user.currency}\n"
        f"🔔 Сповіщення: {'увімкнено' if user.notification_enabled else 'вимкнено'}\n\n"
        "Для зміни налаштувань використовуйте відповідні команди:\n"
        "/balance - змінити баланс\n"
        "/budget - змінити бюджет\n"
        "/notifications - налаштувати сповіщення"
    )
    await update.message.reply_text(settings_text)

async def notifications_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /notifications"""
    user_id = update.effective_user.id
    
    with Session() as session:
        user = session.query(User).filter(User.telegram_id == user_id).first()
        if not user or not user.is_setup_completed:
            await update.message.reply_text(
                "Будь ласка, спочатку завершіть налаштування бота командою /start"
            )
            return
        
        # Змінюємо стан сповіщень на протилежний
        user.notification_enabled = not user.notification_enabled
        session.commit()
        
        status = "увімкнено" if user.notification_enabled else "вимкнено"
        await update.message.reply_text(f"✅ Сповіщення {status}")

async def add_transaction_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /add"""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Неправильний формат команди.\n"
            "Використовуйте: /add <сума> <опис>"
        )
        return
    
    try:
        amount = float(context.args[0])
        description = " ".join(context.args[1:])
        
        with Session() as session:
            user = session.query(User).filter(User.telegram_id == update.effective_user.id).first()
            
            if not user:
                await update.message.reply_text("❌ Помилка: користувач не знайдений")
                return
            
            transaction = Transaction(
                user_id=user.id,
                amount=amount,
                type=TransactionType.EXPENSE,
                description=description
            )
            
            session.add(transaction)
            session.commit()
            
            await update.message.reply_text(
                f"✅ Транзакцію додано!\n"
                f"Сума: {amount} грн\n"
                f"Опис: {description}"
            )
            
    except ValueError:
        await update.message.reply_text("❌ Помилка: некоректна сума")
    except Exception as e:
        await update.message.reply_text(f"❌ Помилка: {str(e)}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /stats"""
    with Session() as session:
        user = session.query(User).filter(User.telegram_id == update.effective_user.id).first()
        
        if not user:
            await update.message.reply_text("❌ Помилка: користувач не знайдений")
            return
        
        # Отримуємо транзакції за останній місяць
        month_ago = datetime.utcnow().replace(day=1)
        transactions = session.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.transaction_date >= month_ago
        ).all()
        
        total_expenses = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)
        total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
        
        stats_message = (
            f"📊 Статистика за поточний місяць:\n\n"
            f"💰 Доходи: {total_income:.2f} грн\n"
            f"💸 Витрати: {total_expenses:.2f} грн\n"
            f"💵 Баланс: {total_income - total_expenses:.2f} грн\n\n"
            f"Кількість транзакцій: {len(transactions)}"
        )
        
        await update.message.reply_text(stats_message)

async def budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /budget"""
    # Показуємо меню бюджету
    from handlers.callback_handler import show_budget_menu
    
    keyboard = [
        [
            InlineKeyboardButton("💰 Мій бюджет", callback_data="my_budget"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Натисніть кнопку нижче, щоб переглянути свій бюджет:",
        reply_markup=reply_markup
    )
    
    return
    
    if context.args[0] == "встановити" and len(context.args) > 1:
        try:
            amount = float(context.args[1])
            with Session() as session:
                user = session.query(User).filter(User.telegram_id == update.effective_user.id).first()
                if user:
                    user.monthly_budget = amount
                    session.commit()
                    await update.message.reply_text(f"✅ Бюджет встановлено: {amount} грн")
                else:
                    await update.message.reply_text("❌ Помилка: користувач не знайдений")
        except ValueError:
            await update.message.reply_text("❌ Помилка: некоректна сума")
    else:
        await update.message.reply_text(
            "❌ Неправильний формат команди.\n"
            "Використовуйте: /budget встановити <сума>"
        )

def get_setup_handler():
    """Отримання обробника процесу налаштування (без додаткових запитань)"""
    return ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            # Зберігаємо стани для зворотної сумісності, 
            # але вони не будуть використовуватися в автоматичному режимі
            SETUP_BALANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_balance)],
            SETUP_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_budget)],
            SETUP_NOTIFICATIONS: [CallbackQueryHandler(setup_notifications)]
        },
        fallbacks=[CommandHandler('cancel', cancel_setup)]
    )

async def show_main_menu(message, context):
    """Показує головне меню (для зворотної сумісності)"""
    from handlers.main_menu import show_main_menu as unified_main_menu
    await unified_main_menu(message, context, is_query=False)