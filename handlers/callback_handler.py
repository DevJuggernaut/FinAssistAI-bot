from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import os
from datetime import datetime, timedelta
import calendar
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Налаштування бек-енду для роботи без графічного інтерфейсу
import io
import uuid
import logging

from database.db_operations import get_or_create_user, get_monthly_stats, get_user_categories, get_user, get_user_transactions
from handlers.setup_callbacks import show_currency_selection, complete_setup
from services.financial_advisor import get_financial_advice
from handlers.budget_callbacks import create_budget_from_recommendations, show_budget_total_input
from services.analytics_service import analytics_service

logger = logging.getLogger(__name__)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє натискання на інлайн-кнопки"""
    try:
        query = update.callback_query
        await query.answer()  # Відповідаємо на колбек, щоб прибрати "годинник" з кнопки
        
        # Отримуємо дані користувача
        user = get_user(update.effective_user.id)
        if not user:
            await query.message.reply_text("Будь ласка, спочатку налаштуйте бота командою /start")
            return
        
        callback_data = query.data
        
        # Основні функції
        if callback_data == "stats" or callback_data == "show_stats":
            await show_stats(query, context)
        elif callback_data == "add_transaction":
            await show_add_transaction_form(query, context)
        elif callback_data == "add_expense":
            await add_expense(query, context)
        elif callback_data == "add_income":
            await add_income(query, context)
        elif callback_data == "show_help":
            await show_help_menu(query, context)
        elif callback_data == "categories":
            await show_categories(query, context)
        elif callback_data == "reports":
            await show_reports_menu(query, context)
        
        # Аналітичні функції
        elif callback_data == "stats_charts":
            await show_charts_menu(query, context)
        elif callback_data == "generate_report":
            await generate_monthly_report(query, context)
        elif callback_data == "export_transactions":
            await export_transactions(query, context)
        elif callback_data == "back_to_main":
            await back_to_main(query, context)
        
        # Початкове налаштування (тепер обробляється через ConversationHandler)
        elif callback_data == "setup_initial_balance":
            await show_currency_selection(query, context)
        elif callback_data == "complete_setup":
            await complete_setup(query, context)
        
        # Бюджетування і поради
        elif callback_data == "budget":
            await show_budget_menu(query, context)
        elif callback_data == "create_monthly_budget":
            await show_create_budget_form(query, context)
        elif callback_data == "budget_recommendations":
            await show_budget_recommendations(query, context)
        elif callback_data == "create_budget_from_recommendations":
            await create_budget_from_recommendations(query, context)
        elif callback_data == "view_past_budgets":
            await show_past_budgets(query, context)
        elif callback_data == "edit_budget":
            await show_edit_budget_form(query, context)
        elif callback_data == "detailed_budget_analysis":
            await show_budget_analysis(query, context)
        elif callback_data.startswith("select_budget_month_"):
            # Обробка вибору місяця для бюджету
            parts = callback_data.split("_")
            month = int(parts[3])
            year = int(parts[4])
            context.user_data['budget_creation'] = {'step': 'total_input', 'month': month, 'year': year}
            await show_budget_total_input(query, context)
            await show_budget_analysis(query, context)
        elif callback_data == "financial_advice":
            await show_financial_advice_menu(query, context)
        
        # Налаштування
        elif callback_data == "settings":
            await show_settings_menu(query, context)
        elif callback_data == "notification_settings":
            await show_notification_settings(query, context)
        elif callback_data == "currency_settings":
            await show_currency_settings(query, context)
        elif callback_data == "language_settings":
            await show_language_settings(query, context)
        
        # Навігація
        elif callback_data == "back_to_main":
            await show_main_menu(query, context)
        elif callback_data == "help":
            await show_help(query, context)
        
        # Додавання транзакцій
        elif callback_data.startswith("add_"):
            if callback_data == "add_expense":
                await show_add_expense_form(query, context)
            elif callback_data == "add_income":
                await show_add_income_form(query, context)
        
        # Аналіз
        elif callback_data.startswith('analyze_'):
            await handle_analysis_callback(query, user)
        
        # Неімплементована функція
        else:
            await query.edit_message_text(
                text=f"🚧 Функція '{callback_data}' знаходиться в розробці та буде доступна скоро!"
            )
    except Exception as e:
        logger.error(f"Error handling callback: {str(e)}")
        await query.edit_message_text(
            text="Виникла помилка при обробці запиту.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Назад", callback_data="back_to_main")]])
        )

async def handle_analysis_callback(query, user):
    """Обробка колбеків аналізу"""
    try:
        # Отримуємо транзакції за останні 3 місяці
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        transactions = get_user_transactions(user.id, start_date, end_date)
        
        if query.data == 'analyze_categories':
            # Аналіз категорій
            report = analytics_service.generate_custom_report(
                transactions,
                'category_analysis'
            )
            
            # Відправляємо статистику
            stats = report['statistics']
            await query.message.reply_text(
                "📊 Аналіз категорій витрат\n\n" +
                "\n".join(
                    f"• {category}: {data['sum']:.2f} (середнє: {data['mean']:.2f}, кількість: {data['count']})"
                    for category, data in stats.items()
                )
            )
            
            # Відправляємо графік
            if report['visualization']:
                await query.message.reply_photo(
                    photo=report['visualization'],
                    caption="Розподіл витрат за категоріями"
                )
        
        elif query.data == 'analyze_trends':
            # Аналіз трендів
            report = analytics_service.generate_custom_report(
                transactions,
                'trend_analysis',
                'monthly'
            )
            
            # Відправляємо статистику
            stats = report['statistics']
            await query.message.reply_text(
                "📈 Тренди витрат\n\n" +
                "\n".join(
                    f"• Місяць {month}: {data['sum']:.2f} (середнє: {data['mean']:.2f}, кількість: {data['count']})"
                    for month, data in stats.items()
                )
            )
            
            # Відправляємо графік
            if report['visualization']:
                await query.message.reply_photo(
                    photo=report['visualization'],
                    caption="Тренди витрат по місяцях"
                )
        
        elif query.data == 'analyze_budget':
            # Аналіз бюджету
            report = analytics_service.generate_custom_report(
                transactions,
                'budget_analysis'
            )
            
            # Відправляємо статистику
            stats = report['statistics']
            await query.message.reply_text(
                "💰 Аналіз бюджету\n\n" +
                "\n".join(
                    f"• {category}:\n"
                    f"  - Фактично: {data['amount']:.2f}\n"
                    f"  - Бюджет: {data['budget']:.2f}\n"
                    f"  - Використання: {data['utilization']:.1f}%"
                    for category, data in stats.items()
                )
            )
            
            # Відправляємо графік
            if report['visualization']:
                await query.message.reply_photo(
                    photo=report['visualization'],
                    caption="Порівняння фактичних витрат з бюджетом"
                )
        
        elif query.data == 'analyze_full':
            # Повний аналіз
            # Генеруємо всі типи звітів
            category_report = analytics_service.generate_custom_report(
                transactions,
                'category_analysis'
            )
            trend_report = analytics_service.generate_custom_report(
                transactions,
                'trend_analysis',
                'monthly'
            )
            budget_report = analytics_service.generate_custom_report(
                transactions,
                'budget_analysis'
            )
            
            # Відправляємо загальний підсумок
            await query.message.reply_text(
                "📊 Повний фінансовий аналіз\n\n"
                "Аналіз включає:\n"
                "• Розподіл витрат за категоріями\n"
                "• Тренди витрат по місяцях\n"
                "• Порівняння з бюджетом\n\n"
                "Детальні графіки будуть надіслані наступними повідомленнями."
            )
            
            # Відправляємо всі графіки
            for report, title in [
                (category_report, "Розподіл витрат за категоріями"),
                (trend_report, "Тренди витрат по місяцях"),
                (budget_report, "Порівняння з бюджетом")
            ]:
                if report['visualization']:
                    await query.message.reply_photo(
                        photo=report['visualization'],
                        caption=title
                    )
    except Exception as e:
        logger.error(f"Error handling analysis callback: {str(e)}")
        await query.message.reply_text("Виникла помилка при генерації аналізу.")

async def show_stats(query, context):
    """Показує статистику користувача"""
    try:
        from datetime import datetime
        
        # Отримуємо ID користувача Telegram
        telegram_id = query.from_user.id
        
        # Імпортуємо необхідні функції
        from database.db_operations import get_or_create_user, get_monthly_stats
        
        # Отримуємо або створюємо користувача в БД
        user = get_or_create_user(
            telegram_id=telegram_id, 
            username=query.from_user.username,
            first_name=query.from_user.first_name,
            last_name=query.from_user.last_name
        )
        
        # Отримуємо статистику
        stats = get_monthly_stats(user.id)
        
        # Форматуємо текст статистики
        expenses = stats['expenses']
        income = stats['income']
        balance = stats['balance']
        
        # Отримуємо поточний місяць українською
        current_month = datetime.now().strftime("%B")
        months_uk = {
            "January": "січень", "February": "лютий", "March": "березень",
            "April": "квітень", "May": "травень", "June": "червень",
            "July": "липень", "August": "серпень", "September": "вересень",
            "October": "жовтень", "November": "листопад", "December": "грудень"
        }
        month_uk = months_uk.get(current_month, current_month)
        
        # Створюємо візуальне представлення балансу (графічна шкала)
        if income > 0:
            expense_percent = min(expenses / income * 100, 100)
            balance_scale = ""
            filled_blocks = int(expense_percent / 10)
            empty_blocks = 10 - filled_blocks
            
            if expense_percent < 70:
                balance_scale = "🟢" * filled_blocks + "⚪" * empty_blocks
            elif 70 <= expense_percent < 90:
                balance_scale = "🟠" * filled_blocks + "⚪" * empty_blocks
            else:
                balance_scale = "🔴" * filled_blocks + "⚪" * empty_blocks
            
            efficiency = f"Витрачено {expense_percent:.1f}% від доходу"
        else:
            balance_scale = "⚪⚪⚪⚪⚪⚪⚪⚪⚪⚪"
            efficiency = "Додайте дохід для аналізу ефективності"
        
        # Форматуємо заголовок та загальну статистику
        stats_text = (
            f"📊 *ФІНАНСОВИЙ ОГЛЯД: {month_uk.upper()}*\n\n"
            f"💰 *Доходи:* `{income:.2f} грн`\n"
            f"💸 *Витрати:* `{expenses:.2f} грн`\n"
            f"💼 *Баланс:* `{balance:.2f} грн`\n\n"
            f"{balance_scale}\n"
            f"_{efficiency}_\n\n"
        )
        
        # Додаємо топ категорій витрат з візуалізацією
        if stats['top_categories']:
            stats_text += "*ТОП КАТЕГОРІЙ ВИТРАТ:*\n"
            for i, category in enumerate(stats['top_categories'], 1):
                name, icon, amount = category
                percentage = (amount / expenses) * 100 if expenses > 0 else 0
                
                # Додаємо візуальну шкалу для категорії
                category_bar = ""
                bar_length = int(percentage / 10) if percentage > 0 else 0
                if bar_length > 0:
                    category_bar = "▓" * min(bar_length, 10)
                
                stats_text += f"`{i}` {icon} *{name}*\n"
                stats_text += f"   `{amount:.2f} грн ({percentage:.1f}%)` {category_bar}\n"
        else:
            stats_text += "*ТОП КАТЕГОРІЙ ВИТРАТ:*\n"
            stats_text += "_Дані відсутні - додайте свою першу транзакцію!_\n\n"
        
        # Додаємо інформацію про бюджет
        # Це можна замінити на реальні дані, якщо є функція отримання бюджету
        budget_spent_percent = min((expenses / 10000) * 100, 100)  # Умовний бюджет 10000 грн
        stats_text += f"\n*БЮДЖЕТ МІСЯЦЯ:*\n"
        stats_text += f"Використано: `{budget_spent_percent:.1f}%` від плану\n"
        
        # Додаємо розширені кнопки для навігації
        keyboard = [
            [
                InlineKeyboardButton("📅 День", callback_data="stats_daily"),
                InlineKeyboardButton("📆 Тиждень", callback_data="stats_weekly"),
                InlineKeyboardButton("📆 Місяць", callback_data="stats_monthly")
            ],
            [
                InlineKeyboardButton("📊 Графіки та діаграми", callback_data="stats_charts")
            ],
            [
                InlineKeyboardButton("💹 Динаміка доходів", callback_data="income_analysis"),
                InlineKeyboardButton("💸 Аналіз витрат", callback_data="expense_analysis")
            ],
            [
                InlineKeyboardButton("📥 Експорт даних", callback_data="export_transactions"),
                InlineKeyboardButton("« Назад", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=stats_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        error_message = f"❌ Помилка при отриманні статистики: {str(e)}"
        await query.edit_message_text(
            text=error_message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Назад", callback_data="back_to_main")]])
        )
        keyboard = [[InlineKeyboardButton("« Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=error_message,
            reply_markup=reply_markup
        )

async def show_add_transaction_form(query, context):
    """Показує форму для додавання транзакції"""
    text = (
        "💰 *Додати нову транзакцію*\n\n"
        "Виберіть тип транзакції:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("➖ Витрата", callback_data="add_expense"),
            InlineKeyboardButton("➕ Дохід", callback_data="add_income")
        ],
        [InlineKeyboardButton("« Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_categories(query, context):
    """Показує категорії користувача та опції управління ними"""
    try:
        # Отримуємо ID користувача Telegram
        telegram_id = query.from_user.id
        
        # Імпортуємо необхідні функції
        from database.db_operations import get_or_create_user, get_user_categories
        
        # Отримуємо або створюємо користувача в БД
        user = get_or_create_user(
            telegram_id=telegram_id, 
            username=query.from_user.username,
            first_name=query.from_user.first_name,
            last_name=query.from_user.last_name
        )
        
        # Отримуємо категорії користувача
        expense_categories = get_user_categories(user.id, 'expense')
        income_categories = get_user_categories(user.id, 'income')
        
        # Форматуємо текст
        text = "🗂 *Ваші категорії*\n\n"
        
        text += "*Категорії витрат:*\n"
        if expense_categories:
            for category in expense_categories:
                text += f"• {category.name} {category.icon}\n"
        else:
            text += "Немає категорій витрат\n"
        
        text += "\n*Категорії доходів:*\n"
        if income_categories:
            for category in income_categories:
                text += f"• {category.name} {category.icon}\n"
        else:
            text += "Немає категорій доходів\n"
        
        # Додаємо кнопки управління
        keyboard = [
            [
                InlineKeyboardButton("➕ Додати категорію", callback_data="add_category")
            ],
            [
                InlineKeyboardButton("✏️ Редагувати", callback_data="edit_categories"),
                InlineKeyboardButton("❌ Видалити", callback_data="delete_category")
            ],
            [InlineKeyboardButton("« Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        error_message = f"❌ Помилка при отриманні категорій: {str(e)}"
        keyboard = [[InlineKeyboardButton("« Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=error_message,
            reply_markup=reply_markup
        )

async def show_reports_menu(query, context):
    """Показує меню звітів"""
    text = (
        "📊 *Фінансові звіти*\n\n"
        "Оберіть тип звіту для генерації:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📆 Місячний звіт", callback_data="generate_report"),
            InlineKeyboardButton("📈 Аналіз витрат", callback_data="expense_analysis")
        ],
        [
            InlineKeyboardButton("💰 Бюджет", callback_data="budget_report"),
            InlineKeyboardButton("📄 Експорт (CSV)", callback_data="export_transactions")
        ],
        [
            InlineKeyboardButton("📊 Розширена аналітика", callback_data="advanced_analytics")
        ],
        [InlineKeyboardButton("« Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_charts_menu(query, context):
    """Показує меню з доступними графіками"""
    text = (
        "📈 *Візуалізація даних*\n\n"
        "Оберіть тип графіка для відображення:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🍕 Структура витрат", callback_data="chart_expense_pie")
        ],
        [
            InlineKeyboardButton("📊 Доходи/Витрати", callback_data="chart_income_expense")
        ],
        [
            InlineKeyboardButton("📈 Тренд витрат", callback_data="chart_expense_trend"),
            InlineKeyboardButton("🔥 Теплова карта", callback_data="chart_heatmap")
        ],
        [
            InlineKeyboardButton("📊 Патерни витрат", callback_data="chart_patterns")
        ],
        [InlineKeyboardButton("« Назад", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def generate_monthly_report(query, context):
    """Генерує місячний звіт для користувача"""
    await query.edit_message_text(
        text="🔄 Генерую детальний звіт за поточний місяць. Це може зайняти деякий час..."
    )
    
    try:
        # Отримуємо ID користувача Telegram
        telegram_id = query.from_user.id
        
        # Імпортуємо необхідні функції
        from database.db_operations import get_or_create_user
        from services.report_generator import generate_user_report
        
        # Отримуємо або створюємо користувача в БД
        user = get_or_create_user(
            telegram_id=telegram_id, 
            username=query.from_user.username,
            first_name=query.from_user.first_name,
            last_name=query.from_user.last_name
        )
        
        # Генеруємо звіт (за поточний місяць)
        report_data = generate_user_report(user.id)
        
        if 'error' in report_data:
            raise Exception(report_data['error'])
        
        # Перевіряємо наявність основного файлу звіту
        if os.path.exists(report_data['html_path']):
            # Відправляємо кругову діаграму та посилання на повний звіт
            if os.path.exists(report_data['charts']['pie']):
                with open(report_data['charts']['pie'], 'rb') as photo:
                    await query.message.reply_photo(
                        photo=photo,
                        caption="🍕 Структура витрат за категоріями"
                    )
            
            # Відправляємо HTML файл звіту
            with open(report_data['html_path'], 'rb') as document:
                await query.message.reply_document(
                    document=document,
                    filename="Фінансовий звіт.html",
                    caption="📊 Ваш детальний фінансовий звіт готовий!"
                )
            
            # Повертаємо меню статистики
            await show_stats(query, context)
        else:
            raise Exception("Не вдалося згенерувати файл звіту")
            
    except Exception as e:
        error_message = f"❌ Помилка при генерації звіту: {str(e)}"
        keyboard = [[InlineKeyboardButton("« Назад", callback_data="stats")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=error_message,
            reply_markup=reply_markup
        )

async def export_transactions(query, context):
    """Експортує транзакції користувача в CSV файл"""
    await query.edit_message_text(
        text="🔄 Генерую експорт транзакцій у форматі CSV. Зачекайте..."
    )
    
    try:
        # Отримуємо ID користувача Telegram
        telegram_id = query.from_user.id
        
        # Імпортуємо необхідні функції
        from database.db_operations import get_or_create_user
        from services.report_generator import export_user_transactions
        
        # Отримуємо або створюємо користувача в БД
        user = get_or_create_user(
            telegram_id=telegram_id, 
            username=query.from_user.username,
            first_name=query.from_user.first_name,
            last_name=query.from_user.last_name
        )
        
        # Експортуємо транзакції поточного місяця
        csv_path, error = export_user_transactions(user.id)
        
        if error:
            raise Exception(error)
        
        if os.path.exists(csv_path):
            # Відправляємо CSV файл
            with open(csv_path, 'rb') as document:
                current_month = datetime.now().strftime('%Y-%m')
                await query.message.reply_document(
                    document=document,
                    filename=f"Транзакції_{current_month}.csv",
                    caption="📋 Ваші транзакції успішно експортовано у форматі CSV!"
                )
            
            # Повертаємо меню статистики
            await show_stats(query, context)
        else:
            raise Exception("Не вдалося створити CSV файл")
            
    except Exception as e:
        error_message = f"❌ Помилка при експорті транзакцій: {str(e)}"
        keyboard = [[InlineKeyboardButton("« Назад", callback_data="stats")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=error_message,
            reply_markup=reply_markup
        )

async def show_financial_advice_menu(query, context):
    """Показує меню вибору типу фінансової поради"""
    text = (
        "💡 *Фінансові поради*\n\n"
        "Оберіть тип фінансової поради, яку ви хочете отримати:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("💰 Загальні", callback_data="advice_general"),
            InlineKeyboardButton("💸 Економія", callback_data="advice_savings")
        ],
        [
            InlineKeyboardButton("📈 Інвестиції", callback_data="advice_investment"),
            InlineKeyboardButton("📊 Бюджет", callback_data="advice_budget")
        ],
        [InlineKeyboardButton("« Назад", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_main_menu(query, context):
    """Показує головне меню бота"""
    from datetime import datetime
    user = query.from_user
    current_hour = datetime.now().hour
    
    # Вибір привітання залежно від часу доби
    if 5 <= current_hour < 12:
        greeting = "☀️ Доброго ранку"
    elif 12 <= current_hour < 18:
        greeting = "🌤️ Доброго дня"
    elif 18 <= current_hour < 23:
        greeting = "🌙 Доброго вечора"
    else:
        greeting = "✨ Доброї ночі"
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Мої фінанси", callback_data="stats"),
            InlineKeyboardButton("➕ Нова транзакція", callback_data="add_transaction")
        ],
        [
            InlineKeyboardButton("📁 Мої категорії", callback_data="categories"),
            InlineKeyboardButton("💼 Бюджет", callback_data="budget")
        ],
        [
            InlineKeyboardButton("📈 Аналітика", callback_data="reports"),
            InlineKeyboardButton("💡 Поради", callback_data="financial_advice")
        ],
        [
            InlineKeyboardButton("⚙️ Налаштування", callback_data="settings"),
            InlineKeyboardButton("❓ Допомога", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"{greeting}, *{user.first_name}*!\n\n"
        f"*ФінАсистент* — ваш розумний помічник для управління фінансами.\n\n"
        f"🔹 *Можливості*:\n"
        f"• Відстеження витрат і доходів\n"
        f"• Автоматичне розпізнавання чеків\n"
        f"• Аналіз банківських виписок\n"
        f"• Персональна фінансова аналітика\n"
        f"• Розумні поради та рекомендації\n\n"
        f"_Оберіть опцію нижче для початку роботи:_",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_help(query, context):
    """Показує довідку користувачу - повний гід для новачків"""
    help_text = (
        "📚 *ДОВІДКА ПО ВИКОРИСТАННЮ*\n\n"
        
        "🔶 *Початкове налаштування бота*\n"
        "1️⃣ Перейдіть у розділ 'Мій бюджет' та встановіть початковий баланс\n"
        "2️⃣ Налаштуйте місячний бюджет витрат\n"
        "3️⃣ Налаштуйте категорії доходів і витрат\n\n"
        
        "🔶 *Щоденне використання*\n"
        "1️⃣ Регулярно додавайте фінансові операції (витрати/доходи)\n"
        "2️⃣ Перегляньте свій бюджет та налаштуйте ліміти витрат\n"
        "3️⃣ Переглядайте аналітику для контролю витрат\n\n"
        
        "🔷 *Основні функції (з головного меню)*\n"
        "• *💰 Мій бюджет* - перегляд стану балансу, створення та редагування бюджету\n"
        "• *➕ Додати операцію* - швидке додавання витрат/доходів різними способами\n"
        "• *📊 Аналітика* - графіки, звіти та прогнози фінансового стану\n"
        "• *⚙️ Налаштування* - персоналізація бота під ваші потреби\n\n"
        
        "🔷 *Способи додавання транзакцій*\n"
        "• 📸 Надішліть *фото чека* для автоматичного розпізнавання\n"
        "• 📎 Завантажте *банківську виписку* (.csv, .pdf, .xlsx)\n"
        "• 💬 Напишіть транзакцію текстом: `Продукти 250 грн`\n"
        "• ➕ Додавання доходу: `+Зарплата 8000 грн`\n\n"
        
        "🔷 *AI-помічник та аналітика*\n"
        "• ❓ Запитайте про фінанси: `Скільки я витратив на їжу цього місяця?`\n"
        "• 💡 Попросіть пораду: `Порадь, як заощадити на продуктах`\n"
        "• 📊 Перегляньте тенденції витрат в розділі Аналітика\n"
        "• 📉 Отримайте прогноз майбутніх витрат на основі ваших даних\n\n"
        
        "🔷 *Корисні команди*\n"
        "• `/start` - Головне меню бота\n"
        "• `/help` - Показати цю довідку\n"
        "• `/add` - Швидке додавання транзакції\n"
        "• `/stats` - Фінансова статистика"
    )
    
    # Додаємо кнопки для швидкої навігації до основних функцій
    keyboard = [
        [
            InlineKeyboardButton("📊 Мої фінанси", callback_data="stats"),
            InlineKeyboardButton("➕ Нова транзакція", callback_data="add_transaction")
        ],
        [
            InlineKeyboardButton("📈 Аналітика", callback_data="reports"),
            InlineKeyboardButton("💡 Поради", callback_data="financial_advice")
        ],
        [
            InlineKeyboardButton("« Назад", callback_data="back_to_main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=help_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_budget_menu(query, context):
    """Показує меню управління бюджетом"""
    from services.budget_manager import BudgetManager
    
    # Отримуємо дані про користувача
    telegram_id = query.from_user.id
    user = get_or_create_user(telegram_id)
    
    # Створюємо менеджер бюджету
    budget_manager = BudgetManager(user.id)
    
    # Отримуємо статус активного бюджету
    budget_status = budget_manager.get_budget_status()
    
    # Перевіряємо, чи налаштовані початкові дані користувача
    if user.initial_balance is None or user.monthly_budget is None:
        # Якщо початкові дані не налаштовані, пропонуємо це зробити
        keyboard = [
            [
                InlineKeyboardButton("💰 Встановити початковий баланс", callback_data="setup_initial_balance")
            ],
            [
                InlineKeyboardButton("📝 Встановити місячний бюджет", callback_data="setup_monthly_budget")
            ],
            [
                InlineKeyboardButton("🏷️ Налаштувати категорії витрат", callback_data="setup_categories")
            ],
            [
                InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")
            ]
        ]
    elif budget_status['status'] == 'no_active_budget':
        # Якщо немає активного бюджету, пропонуємо створити новий
        keyboard = [
            [
                InlineKeyboardButton("➕ Створити місячний бюджет", callback_data="create_monthly_budget")
            ],
            [
                InlineKeyboardButton("📊 Рекомендації по бюджету", callback_data="budget_recommendations")
            ],
            [
                InlineKeyboardButton("🔍 Переглянути попередні бюджети", callback_data="view_past_budgets")
            ],
            [
                InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if user.initial_balance is None or user.monthly_budget is None:
            await query.edit_message_text(
                "⚠️ *Необхідне початкове налаштування*\n\n"
                "Для повноцінної роботи з ботом потрібно виконати налаштування:\n\n"
                "1️⃣ Встановити ваш початковий фінансовий баланс\n"
                "2️⃣ Налаштувати місячний бюджет витрат\n"
                "3️⃣ Створити категорії для ваших фінансових операцій\n\n"
                "Оберіть опцію нижче для налаштування бота:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                "💼 *Управління бюджетом*\n\n"
                "У вас немає активного бюджету на поточний період.\n"
            "Створіть новий бюджет для кращого контролю витрат.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        # Якщо є активний бюджет, показуємо його статус
        active_budget = budget_status['data']
        start_date = active_budget['budget'].start_date.strftime('%d.%m.%Y')
        end_date = active_budget['budget'].end_date.strftime('%d.%m.%Y')
        
        # Формуємо повідомлення про стан бюджету
        usage_percent = active_budget['usage_percent']
        
        # Визначаємо emoji в залежності від стану використання бюджету
        if usage_percent > 90:
            status_emoji = "🔴"
        elif usage_percent > 70:
            status_emoji = "🟠"
        else:
            status_emoji = "🟢"
        
        message = (
            f"💼 *Бюджет: {active_budget['budget'].name}*\n"
            f"📅 Період: {start_date} - {end_date}\n\n"
            f"{status_emoji} *Стан бюджету*: {usage_percent:.1f}% використано\n"
            f"💰 *Загальний бюджет*: `{active_budget['budget'].total_budget:.2f} грн`\n"
            f"💸 *Витрачено*: `{active_budget['total_spending']:.2f} грн`\n"
            f"✅ *Залишилось*: `{active_budget['total_remaining']:.2f} грн`\n\n"
            f"📊 *Деталі по категоріям*:\n"
        )
        
        # Додаємо інформацію по категоріям
        for i, cat_budget in enumerate(sorted(active_budget['category_budgets'], key=lambda x: x['usage_percent'], reverse=True)):
            if i < 5:  # Обмежуємо кількість відображуваних категорій
                # Визначаємо emoji для категорії
                if cat_budget['usage_percent'] > 100:
                    cat_emoji = "❌"
                elif cat_budget['usage_percent'] > 90:
                    cat_emoji = "⚠️"
                else:
                    cat_emoji = "✅"
                
                message += (
                    f"{cat_emoji} {cat_budget['category_icon']} {cat_budget['category_name']}: "
                    f"`{cat_budget['usage_percent']:.1f}%` "
                    f"(`{cat_budget['actual_spending']:.0f}`/`{cat_budget['allocated_amount']:.0f}` грн)\n"
                )
        
        if len(active_budget['category_budgets']) > 5:
            message += f"... та ще {len(active_budget['category_budgets']) - 5} категорій\n"
        
        # Додаємо кнопки для управління бюджетом
        keyboard = [
            [
                InlineKeyboardButton("✏️ Редагувати бюджет", callback_data="edit_budget"),
                InlineKeyboardButton("📊 Детальний аналіз", callback_data="detailed_budget_analysis")
            ],
            [
                InlineKeyboardButton("➕ Новий бюджет", callback_data="create_monthly_budget"),
                InlineKeyboardButton("📑 Історія бюджетів", callback_data="view_past_budgets")
            ],
            [
                InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def show_create_budget_form(query, context):
    """Показує форму для створення нового бюджету"""
    # Перший крок - вибір місяця для бюджету
    today = datetime.now()
    current_month = today.month
    current_year = today.year
    
    # Формуємо список наступних 3 місяців для вибору
    months = []
    for i in range(0, 3):
        month = current_month + i
        year = current_year
        if month > 12:
            month -= 12
            year += 1
        month_name = calendar.month_name[month]
        months.append((month, year, f"{month_name} {year}"))
    
    # Створюємо кнопки для вибору місяця
    keyboard = []
    for month, year, label in months:
        keyboard.append([
            InlineKeyboardButton(label, callback_data=f"select_budget_month_{month}_{year}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔙 Назад", callback_data="budget")
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🗓 *Створення нового бюджету*\n\n"
        "Оберіть місяць, для якого хочете створити бюджет:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    # Зберігаємо контекст для створення бюджету
    context.user_data['budget_creation'] = {'step': 'month_selection'}

async def show_budget_recommendations(query, context):
    """Показує рекомендації для створення бюджету"""
    from services.budget_manager import BudgetManager
    
    # Отримуємо дані про користувача
    telegram_id = query.from_user.id
    user = get_or_create_user(telegram_id)
    
    # Створюємо менеджер бюджету
    budget_manager = BudgetManager(user.id)
    
    # Отримуємо рекомендації
    await query.edit_message_text(
        "📊 *Генерую рекомендації по бюджету...*\n\n"
        "Аналізую ваші попередні витрати для створення оптимального бюджету.",
        parse_mode="Markdown"
    )
    
    try:
        recommendations = budget_manager.generate_budget_recommendations()
        
        message = (
            "💡 *Рекомендації по бюджету*\n\n"
            f"На основі ваших попередніх витрат, рекомендований місячний бюджет становить:\n"
            f"💰 *Загальний бюджет*: `{recommendations['total_recommended_budget']:.2f} грн`\n\n"
            f"📊 *Розподіл по категоріям*:\n"
        )
        
        # Показуємо топ-5 категорій з найбільшими рекомендованими бюджетами
        for i, cat in enumerate(sorted(recommendations['category_recommendations'], key=lambda x: x['recommended_budget'], reverse=True)[:5]):
            message += (
                f"{i+1}. {cat['icon']} {cat['name']}: `{cat['recommended_budget']:.2f} грн` "
                f"({cat['percentage_of_total']:.1f}%)\n"
            )
        
        # Додаємо кнопки для дій з рекомендаціями
        keyboard = [
            [
                InlineKeyboardButton("✅ Створити бюджет за рекомендаціями", callback_data="create_budget_from_recommendations")
            ],
            [
                InlineKeyboardButton("➕ Створити власний бюджет", callback_data="create_monthly_budget")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="budget")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Зберігаємо рекомендації в контексті
        context.user_data['budget_recommendations'] = recommendations
        
    except Exception as e:
        # Якщо сталася помилка, повідомляємо про це та повертаємося до головного меню бюджету
        await query.edit_message_text(
            "❌ *Не вдалося згенерувати рекомендації*\n\n"
            "Недостатньо даних для аналізу або сталася помилка при обробці.\n"
            "Спробуйте створити бюджет вручну.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Створити бюджет", callback_data="create_monthly_budget")],
                [InlineKeyboardButton("🔙 Назад", callback_data="budget")]
            ]),
            parse_mode="Markdown"
        )

async def show_past_budgets(query, context):
    """Показує історію бюджетів користувача"""
    from services.budget_manager import BudgetManager
    
    # Отримуємо дані про користувача
    telegram_id = query.from_user.id
    user = get_or_create_user(telegram_id)
    
    # Створюємо менеджер бюджету
    budget_manager = BudgetManager(user.id)
    
    # Отримуємо всі бюджети користувача
    budgets = budget_manager.get_all_budgets()
    
    if not budgets:
        await query.edit_message_text(
            "📂 *Історія бюджетів*\n\n"
            "У вас ще немає створених бюджетів.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Створити бюджет", callback_data="create_monthly_budget")],
                [InlineKeyboardButton("🔙 Назад", callback_data="budget")]
            ]),
            parse_mode="Markdown"
        )
        return
    
    message = "📂 *Історія бюджетів*\n\n"
    
    # Показуємо останні 5 бюджетів
    for i, budget in enumerate(budgets[:5]):
        start_date = budget.start_date.strftime('%d.%m.%Y')
        end_date = budget.end_date.strftime('%d.%m.%Y')
        
        # Визначаємо статус бюджету
        today = datetime.now().date()
        if budget.start_date <= today <= budget.end_date:
            status = "🟢 Активний"
        elif budget.end_date < today:
            status = "🔵 Завершений"
        else:
            status = "🟡 Запланований"
        
        message += (
            f"{i+1}. *{budget.name}*\n"
            f"   {status} • Період: {start_date} - {end_date}\n"
            f"   Бюджет: {budget.total_budget:.2f} грн\n\n"
        )
    
    # Додаємо кнопки для навігації
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="budget")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_edit_budget_form(query, context):
    """Показує форму для редагування бюджету"""
    from services.budget_manager import BudgetManager
    
    # Отримуємо дані про користувача
    telegram_id = query.from_user.id
    user = get_or_create_user(telegram_id)
    
    # Створюємо менеджер бюджету
    budget_manager = BudgetManager(user.id)
    
    # Отримуємо активний бюджет
    active_budget = budget_manager.get_active_budget()
    
    if not active_budget:
        await query.edit_message_text(
            "❌ *Помилка*\n\n"
            "Не знайдено активного бюджету для редагування.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Створити бюджет", callback_data="create_monthly_budget")],
                [InlineKeyboardButton("🔙 Назад", callback_data="budget")]
            ]),
            parse_mode="Markdown"
        )
        return
    
    # На даному етапі ми показуємо повідомлення, що функція редагування бюджету знаходиться в розробці
    # В майбутніх версіях тут буде форма для редагування
    await query.edit_message_text(
        "✏️ *Редагування бюджету*\n\n"
        "Ця функція знаходиться в розробці та буде доступна у наступних версіях.\n\n"
        "Зараз ви можете видалити поточний бюджет і створити новий з необхідними параметрами.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Створити новий бюджет", callback_data="create_monthly_budget")],
            [InlineKeyboardButton("🔙 Назад", callback_data="budget")]
        ]),
        parse_mode="Markdown"
    )

async def show_budget_analysis(query, context):
    """Показує детальний аналіз бюджету"""
    from services.budget_manager import BudgetManager
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Отримуємо дані про користувача
    telegram_id = query.from_user.id
    user = get_or_create_user(telegram_id)
    
    # Створюємо менеджер бюджету
    budget_manager = BudgetManager(user.id)
    
    # Отримуємо активний бюджет
    active_budget = budget_manager.get_active_budget()
    
    if not active_budget:
        await query.edit_message_text(
            "❌ *Помилка*\n\n"
            "Не знайдено активного бюджету для аналізу.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Створити бюджет", callback_data="create_monthly_budget")],
                [InlineKeyboardButton("🔙 Назад", callback_data="budget")]
            ]),
            parse_mode="Markdown"
        )
        return
    
    await query.edit_message_text(
        "📊 *Генерую аналіз бюджету...*\n\n"
        "Будь ласка, зачекайте.",
        parse_mode="Markdown"
    )
    
    try:
        # Створюємо порівняльну діаграму бюджетів та витрат по категоріям
        categories = []
        allocated = []
        spent = []
        
        for cat_budget in active_budget['category_budgets']:
            categories.append(f"{cat_budget['category_icon']} {cat_budget['category_name']}")
            allocated.append(cat_budget['allocated_amount'])
            spent.append(cat_budget['actual_spending'])
        
        # Обмежуємо до топ-7 категорій
        if len(categories) > 7:
            other_allocated = sum(allocated[7:])
            other_spent = sum(spent[7:])
            
            categories = categories[:7] + ["📦 Інші"]
            allocated = allocated[:7] + [other_allocated]
            spent = spent[:7] + [other_spent]
        
        # Створюємо графік
        plt.figure(figsize=(10, 6))
        
        x = np.arange(len(categories))
        width = 0.35
        
        plt.bar(x - width/2, allocated, width, label='Бюджет')
        plt.bar(x + width/2, spent, width, label='Витрачено')
        
        plt.title('Порівняння бюджету і витрат по категоріям')
        plt.xlabel('Категорії')
        plt.ylabel('Сума (грн)')
        plt.xticks(x, categories, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        
        # Зберігаємо графік у буфер
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        
        # Очищаємо графік від пам'яті
        plt.close()
        
        # Відправляємо зображення
        filename = f"budget_analysis_{uuid.uuid4()}.png"
        await query.message.reply_photo(
            photo=buf,
            caption=(
                "📊 *Аналіз бюджету*\n\n"
                f"Період: {active_budget['budget'].start_date.strftime('%d.%m.%Y')} - "
                f"{active_budget['budget'].end_date.strftime('%d.%m.%Y')}\n"
                f"Загальний бюджет: {active_budget['budget'].total_budget:.2f} грн\n"
                f"Використано: {active_budget['total_spending']:.2f} грн ({active_budget['usage_percent']:.1f}%)"
            ),
            parse_mode="Markdown"
        )
        
        # Повертаємося до меню бюджету
        await show_budget_menu(query, context)
        
    except Exception as e:
        await query.edit_message_text(
            "❌ *Не вдалося створити аналіз*\n\n"
            f"Помилка: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="budget")]
            ]),
            parse_mode="Markdown"
        )

async def show_settings_menu(query, context):
    """Показує меню налаштувань"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Сповіщення", callback_data="notification_settings"),
            InlineKeyboardButton("💱 Валюта", callback_data="currency_settings")
        ],
        [
            InlineKeyboardButton("🌐 Мова", callback_data="language_settings"),
            InlineKeyboardButton("📋 Формат звітів", callback_data="report_format_settings")
        ],
        [
            InlineKeyboardButton("🔄 Синхронізація", callback_data="sync_settings"),
            InlineKeyboardButton("⚙️ Інші налаштування", callback_data="other_settings")
        ],
        [
            InlineKeyboardButton("« Назад", callback_data="back_to_main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚙️ *Налаштування*\n\n"
        "Тут ви можете налаштувати бота під свої потреби.\n"
        "Змінюйте валюту, мову інтерфейсу, налаштовуйте сповіщення "
        "та формати звітів.\n\n"
        "Оберіть категорію налаштувань:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_notification_settings(query, context):
    """Показує налаштування сповіщень"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Щоденні звіти", callback_data="toggle_daily_reports"),
            InlineKeyboardButton("🔕 Вимкнути все", callback_data="disable_all_notifications")
        ],
        [
            InlineKeyboardButton("⚠️ Перевищення лімітів", callback_data="toggle_limit_alerts"),
            InlineKeyboardButton("💸 Великі транзакції", callback_data="toggle_large_transactions")
        ],
        [
            InlineKeyboardButton("« Назад до налаштувань", callback_data="settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔔 *Налаштування сповіщень*\n\n"
        "Налаштуйте, які сповіщення ви хочете отримувати від бота.\n\n"
        "• Щоденні звіти: отримуйте підсумок ваших витрат щодня\n"
        "• Перевищення лімітів: отримуйте сповіщення, коли витрати в категорії перевищують встановлений ліміт\n"
        "• Великі транзакції: отримуйте сповіщення про транзакції, що перевищують встановлену вами суму\n\n"
        "Оберіть опцію нижче:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_currency_settings(query, context):
    """Показує налаштування валюти"""
    keyboard = [
        [
            InlineKeyboardButton("₴ Гривня (UAH)", callback_data="set_currency_uah"),
            InlineKeyboardButton("$ Долар (USD)", callback_data="set_currency_usd")
        ],
        [
            InlineKeyboardButton("€ Євро (EUR)", callback_data="set_currency_eur"),
            InlineKeyboardButton("£ Фунт (GBP)", callback_data="set_currency_gbp")
        ],
        [
            InlineKeyboardButton("🔄 Автоматично конвертувати", callback_data="toggle_auto_convert")
        ],
        [
            InlineKeyboardButton("« Назад до налаштувань", callback_data="settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "💱 *Налаштування валюти*\n\n"
        "Оберіть основну валюту для відображення сум та звітів.\n"
        "Також можна увімкнути автоматичну конвертацію між валютами.\n\n"
        "Поточна валюта: *₴ Гривня (UAH)*\n\n"
        "Оберіть нову валюту:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_language_settings(query, context):
    """Показує налаштування мови інтерфейсу"""
    keyboard = [
        [
            InlineKeyboardButton("🇺🇦 Українська", callback_data="set_lang_uk"),
            InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")
        ],
        [
            InlineKeyboardButton("« Назад до налаштувань", callback_data="settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🌐 *Налаштування мови*\n\n"
        "Оберіть мову інтерфейсу бота:\n\n"
        "Поточна мова: *🇺🇦 Українська*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
async def show_add_expense_form(query, context):
    """Показує форму для додавання витрати"""
    # Отримання категорій витрат користувача
    user_id = query.from_user.id
    
    # Отримуємо або створюємо користувача в БД
    user = get_or_create_user(
        telegram_id=user_id,
        username=query.from_user.username,
        first_name=query.from_user.first_name,
        last_name=query.from_user.last_name
    )
    
    # Отримуємо категорії витрат
    expense_categories = get_user_categories(user.id, 'expense')
    
    # Створюємо інструкцію для користувача
    text = (
        "💸 *Додавання витрати*\n\n"
        "Оберіть спосіб додавання витрати:\n\n"
        "1️⃣ Натисніть на категорію нижче\n"
        "2️⃣ Або відправте повідомлення в форматі:\n"
        "`[Опис] [Сума] грн`\n"
        "Наприклад: `Продукти 250 грн`"
    )
    
    # Створюємо клавіатуру з категоріями витрат
    keyboard = []
    row = []
    
    for i, category in enumerate(expense_categories):
        # Додаємо по 2 кнопки в ряд
        category_btn = InlineKeyboardButton(
            f"{category.icon} {category.name}",
            callback_data=f"expense_cat_{category.id}"
        )
        row.append(category_btn)
        
        if len(row) == 2 or i == len(expense_categories) - 1:
            keyboard.append(row)
            row = []
    
    # Додаємо кнопки для створення нової категорії та повернення
    keyboard.append([
        InlineKeyboardButton("➕ Нова категорія", callback_data="add_expense_category")
    ])
    keyboard.append([
        InlineKeyboardButton("« Назад", callback_data="add_transaction")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Зберігаємо стан користувача - він додає витрату
    if 'user_state' not in context.user_data:
        context.user_data['user_state'] = {}
    context.user_data['user_state']['action'] = 'adding_expense'
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
async def show_add_income_form(query, context):
    """Показує форму для додавання доходу"""
    # Отримання категорій доходів користувача
    user_id = query.from_user.id
    
    # Отримуємо або створюємо користувача в БД
    user = get_or_create_user(
        telegram_id=user_id,
        username=query.from_user.username,
        first_name=query.from_user.first_name,
        last_name=query.from_user.last_name
    )
    
    # Отримуємо категорії доходів
    income_categories = get_user_categories(user.id, 'income')
    
    # Створюємо інструкцію для користувача
    text = (
        "💰 *Додавання доходу*\n\n"
        "Оберіть спосіб додавання доходу:\n\n"
        "1️⃣ Натисніть на категорію нижче\n"
        "2️⃣ Або відправте повідомлення в форматі:\n"
        "`+[Опис] [Сума] грн`\n"
        "Наприклад: `+Зарплата 15000 грн`"
    )
    
    # Створюємо клавіатуру з категоріями доходів
    keyboard = []
    row = []
    
    for i, category in enumerate(income_categories):
        # Додаємо по 2 кнопки в ряд
        category_btn = InlineKeyboardButton(
            f"{category.icon} {category.name}",
            callback_data=f"income_cat_{category.id}"
        )
        row.append(category_btn)
        
        if len(row) == 2 or i == len(income_categories) - 1:
            keyboard.append(row)
            row = []
    
    # Додаємо кнопки для створення нової категорії та повернення
    keyboard.append([
        InlineKeyboardButton("➕ Нова категорія", callback_data="add_income_category")
    ])
    keyboard.append([
        InlineKeyboardButton("« Назад", callback_data="add_transaction")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Зберігаємо стан користувача - він додає дохід
    if 'user_state' not in context.user_data:
        context.user_data['user_state'] = {}
    context.user_data['user_state']['action'] = 'adding_income'
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# Нові функції для обробки кнопок з привітання

async def add_expense(query, context):
    """Відображає форму додавання витрати"""
    # Створюємо клавіатуру для вибору категорії витрат
    from database.db_operations import get_user_categories
    
    user = get_user(query.from_user.id)
    expense_categories = get_user_categories(user.id, 'expense')
    
    keyboard = []
    row = []
    for i, category in enumerate(expense_categories):
        row.append(InlineKeyboardButton(f"{category.icon} {category.name}", callback_data=f"select_expense_category_{category.id}"))
        if (i + 1) % 2 == 0 or i == len(expense_categories) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([InlineKeyboardButton("« Назад", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "💸 *Додавання витрати*\n\n"
        "Оберіть категорію витрати:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def add_income(query, context):
    """Відображає форму додавання доходу"""
    # Створюємо клавіатуру для вибору категорії доходу
    from database.db_operations import get_user_categories
    
    user = get_user(query.from_user.id)
    income_categories = get_user_categories(user.id, 'income')
    
    keyboard = []
    row = []
    for i, category in enumerate(income_categories):
        row.append(InlineKeyboardButton(f"{category.icon} {category.name}", callback_data=f"select_income_category_{category.id}"))
        if (i + 1) % 2 == 0 or i == len(income_categories) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([InlineKeyboardButton("« Назад", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "💰 *Додавання доходу*\n\n"
        "Оберіть категорію доходу:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def show_help_menu(query, context):
    """Показує меню з доступними командами і розділами довідки"""
    keyboard = [
        [
            InlineKeyboardButton("🚀 Перші кроки", callback_data="help_getting_started"),
            InlineKeyboardButton("💸 Управління фінансами", callback_data="help_transactions")
        ],
        [
            InlineKeyboardButton("📊 Аналітика та звіти", callback_data="help_stats"),
            InlineKeyboardButton("🔮 AI-помічник", callback_data="help_ai")
        ],
        [
            InlineKeyboardButton("📱 Всі команди бота", callback_data="help_commands"),
            InlineKeyboardButton("🔍 Поширені питання", callback_data="help_faq")
        ],
        [InlineKeyboardButton("« Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📚 *Довідка по використанню FinAssist*\n\n"
        "Бот допоможе вам відстежувати витрати, планувати бюджет та аналізувати фінанси.\n\n"
        "🔸 *Потрібна швидка допомога?* — виберіть розділ нижче\n"
        "🔸 *Початок роботи* — додайте свою першу транзакцію через '➕ Додати операцію'\n"
        "🔸 *Щоденне використання* — регулярно додавайте витрати для точного аналізу\n",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def back_to_main(query, context):
    """Повернення до головного меню"""
    keyboard = [
        [
            InlineKeyboardButton("💰 Мій бюджет", callback_data="budget"),
            InlineKeyboardButton("➕ Додати операцію", callback_data="add_transaction")
        ],
        [
            InlineKeyboardButton("📊 Аналітика", callback_data="reports"),
            InlineKeyboardButton("⚙️ Налаштування", callback_data="settings")
        ],
        [
            InlineKeyboardButton("❓ Допомога", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отримуємо ім'я користувача
    first_name = query.from_user.first_name or "друже"
    
    await query.edit_message_text(
        f"👋 *З поверненням, {first_name}!*\n\n"
        "Ваш особистий фінансовий помічник готовий до роботи.",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )