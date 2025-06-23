from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import calendar
import logging

from database.db_operations import get_or_create_user
from services.report_generator import FinancialReport

logger = logging.getLogger(__name__)

async def create_budget_from_recommendations(query, context):
    """Створює бюджет на основі рекомендацій"""
    from services.budget_manager import BudgetManager
    
    # Перевіряємо, чи є рекомендації у контексті користувача
    if 'budget_recommendations' not in context.user_data:
        await query.edit_message_text(
            "❌ *Помилка*\n\n"
            "Не знайдено рекомендацій для створення бюджету. Будь ласка, спочатку отримайте рекомендації.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Рекомендації по бюджету", callback_data="budget_recommendations")],
                [InlineKeyboardButton("🔙 Назад", callback_data="budget")]
            ]),
            parse_mode="Markdown"
        )
        return
    
    # Отримуємо дані користувача
    telegram_id = query.from_user.id
    user = get_or_create_user(telegram_id)
    
    # Отримуємо рекомендації
    recommendations = context.user_data['budget_recommendations']
    
    # Визначаємо місяць для бюджету (поточний)
    today = datetime.now()
    month = today.month
    year = today.year
    month_name = calendar.month_name[month]
    
    # Створюємо бюджет
    await query.edit_message_text(
        f"💾 *Створення бюджету на {month_name} {year}*\n\n"
        "Створюю бюджет на основі рекомендацій...",
        parse_mode="Markdown"
    )
    
    try:
        # Створюємо менеджер бюджету
        budget_manager = BudgetManager(user.id)
        
        # Готуємо дані для категорій
        category_allocations = {}
        for cat in recommendations['category_recommendations']:
            category_allocations[cat['category_id']] = cat['recommended_budget']
        
        # Створюємо бюджет
        budget = budget_manager.create_monthly_budget(
            name=f"Бюджет на {month_name} {year}",
            total_budget=recommendations['total_recommended_budget'],
            year=year,
            month=month,
            category_allocations=category_allocations
        )
        
        # Повідомляємо про успіх
        await query.edit_message_text(
            f"✅ *Бюджет успішно створено!*\n\n"
            f"📅 Період: {budget.start_date.strftime('%d.%m.%Y')} - {budget.end_date.strftime('%d.%m.%Y')}\n"
            f"💰 Загальна сума: {budget.total_budget:.2f} грн\n\n"
            f"Тепер ви можете переглянути деталі бюджету та відстежувати витрати.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Перегляд бюджету", callback_data="budget")]
            ]),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await query.edit_message_text(
            f"❌ *Не вдалося створити бюджет*\n\n"
            f"Помилка: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="budget")]
            ]),
            parse_mode="Markdown"
        )

async def show_budget_total_input(query, context):
    """Показує форму для введення загальної суми бюджету"""
    # Отримуємо дані з контексту
    budget_data = context.user_data.get('budget_creation', {})
    month = budget_data.get('month', datetime.now().month)
    year = budget_data.get('year', datetime.now().year)
    
    # Отримуємо назву місяця
    month_name = calendar.month_name[month]
    
    # Повідомляємо користувача про обмеження функціональності на цьому етапі
    await query.edit_message_text(
        f"💰 *Введення суми бюджету на {month_name} {year}*\n\n"
        "На даному етапі функціональність створення бюджету знаходиться в розробці.\n\n"
        "Для створення бюджету з повною функціональністю ми рекомендуємо використовувати "
        "опцію 'Рекомендації по бюджету', яка автоматично проаналізує ваші витрати та "
        "запропонує оптимальний бюджет.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Рекомендації по бюджету", callback_data="budget_recommendations")],
            [InlineKeyboardButton("🔙 Назад до бюджетів", callback_data="budget")]
        ]),
        parse_mode="Markdown"
    )

async def show_my_budget_overview(query, context):
    """Відображає детальний огляд фінансового стану користувача на одному екрані"""
    from services.budget_manager import BudgetManager
    from database.db_operations import get_transactions
    
    telegram_id = query.from_user.id
    user = get_or_create_user(telegram_id)
    
    # Якщо бюджет не встановлений, створюємо базовий
    if user.monthly_budget is None or user.monthly_budget <= 0:
        user.monthly_budget = 10000
        from database.session import Session
        session = Session()
        try:
            session.merge(user)
            session.commit()
        finally:
            session.close()
    
    budget_manager = BudgetManager(user.id)
    
    # Отримуємо фінансову інформацію
    financial_status = budget_manager.get_user_financial_status()
    comprehensive_status = budget_manager.get_comprehensive_budget_status()
    
    if not financial_status:
        await query.edit_message_text(
            "❌ *Помилка*\n\n"
            "Не вдалося отримати фінансову інформацію.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown"
        )
        return
    
    # Визначаємо валюту
    currency = user.currency or "UAH"
    currency_symbol = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
    
    # =============== ВЕРХНЯ ЧАСТИНА: ЗАГАЛЬНИЙ БАЛАНС ===============
    balance = financial_status['current_balance']
    balance_emoji = "💰" if balance >= 0 else "📉"
    
    message = f"💼 *Огляд фінансів*\n\n"
    message += f"{balance_emoji} *Ваш баланс:* `{balance:,.2f}{currency_symbol}`\n\n"
    
    # =============== ОГЛЯД ЗА ПОТОЧНИЙ МІСЯЦЬ ===============
    if comprehensive_status:
        monthly_income = comprehensive_status['current_status']['monthly_income']
        monthly_expenses = comprehensive_status['current_status']['monthly_expenses']
        difference = monthly_income - monthly_expenses
        
        # Визначаємо статус різниці з покращеними текстами
        if difference > 0:
            diff_emoji = "✨"
            diff_text = f"Ви зекономили: `+{difference:.2f}{currency_symbol}`"
        elif difference < 0:
            diff_emoji = "⚠️"
            diff_text = f"Перевитрата: `{difference:.2f}{currency_symbol}`"
        else:
            diff_emoji = "⚖️"
            diff_text = f"Ідеальний баланс: `{difference:.2f}{currency_symbol}`"
    else:
        monthly_income = 0
        monthly_expenses = 0
        difference = 0
        diff_emoji = "📊"
        diff_text = "Почніть відстежувати фінанси"
    
    # Обчислюємо відсоток економії/перевитрати
    # (мотиваційні статуси та підказки видалено за побажанням користувача)
    savings_status = ""
    diff_tip = ""
    
    message += "📊 *ФІНАНСОВИЙ ПІДСУМОК МІСЯЦЯ*\n"
    message += f"⬆️ Доходи: `{monthly_income:,.2f}{currency_symbol}`\n"
    message += f"⬇️ Витрати: `{monthly_expenses:,.2f}{currency_symbol}`\n"
    message += f"───────────────────\n"
    message += f"{diff_emoji} {diff_text}\n\n"
    
    # =============== ЦЕНТРАЛЬНА ЧАСТИНА: ОСТАННІ ТРАНЗАКЦІЇ ===============
    message += "� *ОСТАННІ ОПЕРАЦІЇ*\n"
    
    # Отримуємо останні 7 транзакцій
    recent_transactions = get_transactions(user.id, limit=7)
    
    if recent_transactions:
        message += f"_Показано {len(recent_transactions)} останніх операцій:_\n\n"
        
        for i, transaction in enumerate(recent_transactions):
            # Форматуємо дату більш читабельно
            date_str = transaction.transaction_date.strftime("%d.%m")
            
            # Отримуємо категорію та її іконку
            category_name = "Інше"
            category_icon = "📋"
            if transaction.category:
                category_name = transaction.category.name
                category_icon = transaction.category.icon or "📋"
            
            # Визначаємо колір та знак суми з покращеним форматуванням
            if transaction.type.value == 'income':
                amount_str = f"+{transaction.amount:,.0f}{currency_symbol}"
                amount_emoji = "🟢"
                type_text = "доход"
            else:
                amount_str = f"-{transaction.amount:,.0f}{currency_symbol}"
                amount_emoji = "🔴"
                type_text = "витрата"
            
            # Обрізаємо опис якщо занадто довгий
            description = transaction.description or "Без опису"
            if len(description) > 20:
                description = description[:17] + "..."
            
            # Форматуємо транзакцію більш читабельно
            message += f"┌ `{date_str}` {category_icon} *{description}*\n"
            message += f"└ {amount_emoji} `{amount_str}` • _{category_name}_\n\n"
        
    else:
        message += "🌟 *Почніть свій фінансовий шлях!*\n\n"
        message += "💡 Додайте першу транзакцію, щоб:\n"
        message += "• 📊 Відстежувати витрати та доходи\n"
        message += "• 📈 Бачити фінансові тенденції\n"
        message += "• 🎯 Досягати фінансових цілей\n"
        message += "• 💰 Краще контролювати бюджет\n\n"
    
    # =============== НИЖНЯ ЧАСТИНА: ШВИДКІ ДІЇ ===============
    keyboard = [
        [
            InlineKeyboardButton("📊 Діаграма витрат", callback_data="show_expense_pie_chart"),
            InlineKeyboardButton("📋 Історія операцій", callback_data="view_all_transactions")
        ],
        [
            InlineKeyboardButton("➕ Додати операцію", callback_data="add_transaction")
        ],
        [
            InlineKeyboardButton("🏠 Головне меню", callback_data="back_to_main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Якщо попереднє повідомлення було фото, надсилаємо новий огляд
    if hasattr(query.message, 'photo') and query.message.photo:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def show_budget_detailed_view(query, context):
    """Детальний перегляд бюджету з категоріями"""
    from services.budget_manager import BudgetManager
    
    telegram_id = query.from_user.id
    user = get_or_create_user(telegram_id)
    budget_manager = BudgetManager(user.id)
    
    comprehensive_status = budget_manager.get_comprehensive_budget_status()
    alerts = budget_manager.get_category_spending_alerts()
    
    if not comprehensive_status:
        await query.edit_message_text("❌ Помилка отримання даних", 
                                    parse_mode="Markdown")
        return
    
    currency = comprehensive_status['user_info']['currency']
    active_budget = comprehensive_status['active_budget']
    
    message = "📊 *Детальний огляд бюджету*\n\n"
    
    # Оповіщення про проблемні категорії
    if alerts:
        message += "⚠️ *Увага:*\n"
        for alert in alerts[:3]:  # Показуємо тільки топ-3
            if alert['type'] == 'exceeded':
                message += f"🔴 {alert['icon']} {alert['category']}: перевищено на {alert['overspend']:.2f} {currency}\n"
            else:
                message += f"🟡 {alert['icon']} {alert['category']}: залишилось {alert['remaining']:.2f} {currency}\n"
        message += "\n"
    
    # Категорії бюджету
    if active_budget and active_budget['category_budgets']:
        message += "💼 *Бюджет по категоріях:*\n"
        
        for cat in active_budget['category_budgets']:
            progress_bar = create_progress_bar(cat['usage_percent'], width=8)
            message += f"{cat['category_icon']} *{cat['category_name']}*\n"
            message += f"   {progress_bar} `{cat['usage_percent']:.1f}%`\n"
            message += f"   `{cat['actual_spending']:.2f}/{cat['allocated_amount']:.2f} {currency}`\n\n"
    else:
        message += "📝 *Категорії бюджету не налаштовані*\n"
        message += "Налаштуйте розподіл бюджету по категоріях для кращого контролю.\n\n"
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Редагувати категорії", callback_data="budget_edit_categories")],
        [InlineKeyboardButton("📊 Експорт даних", callback_data="budget_export"),
         InlineKeyboardButton("📈 Метрики", callback_data="budget_metrics")],
        [InlineKeyboardButton("🔙 Назад", callback_data="my_budget_overview")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_budget_settings(query, context):
    """Налаштування бюджету"""
    from services.budget_manager import BudgetManager
    
    telegram_id = query.from_user.id
    user = get_or_create_user(telegram_id)
    budget_manager = BudgetManager(user.id)
    
    comprehensive_status = budget_manager.get_comprehensive_budget_status()
    currency = comprehensive_status['user_info']['currency'] if comprehensive_status else 'UAH'
    
    current_budget = comprehensive_status['budget_limits']['total_monthly_budget'] if comprehensive_status else 0
    
    message = "⚙️ *Налаштування бюджету*\n\n"
    message += f"💰 Поточний місячний бюджет: `{current_budget:.2f} {currency}`\n\n"
    message += "Оберіть дію:"
    
    keyboard = [
        [InlineKeyboardButton("💰 Змінити загальний бюджет", callback_data="budget_change_total")],
        [InlineKeyboardButton("🏷️ Налаштувати категорії", callback_data="budget_setup_categories")],
        [InlineKeyboardButton("📅 Встановити денний ліміт", callback_data="budget_set_daily_limit")],
        [InlineKeyboardButton("🎯 Створити розумний бюджет", callback_data="budget_create_smart")],
        [InlineKeyboardButton("🔙 Назад", callback_data="my_budget_overview")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_budget_statistics(query, context):
    """Показує статистику бюджету"""
    from services.budget_manager import BudgetManager
    
    telegram_id = query.from_user.id
    user = get_or_create_user(telegram_id)
    budget_manager = BudgetManager(user.id)
    
    # Отримуємо статистику
    month_comparison = budget_manager.get_month_comparison(3)
    daily_stats = budget_manager.get_daily_spending_stats(7)
    performance_metrics = budget_manager.get_budget_performance_metrics()
    
    currency = 'UAH'  # Можна отримати з comprehensive_status
    
    message = "📊 *Статистика бюджету*\n\n"
    
    # Метрики ефективності
    if performance_metrics:
        message += "🎯 *Оцінка ефективності:*\n"
        message += f"🏆 Загальна оцінка: `{performance_metrics['overall_score']:.1f}/100`\n"
        message += f"💯 Дотримання бюджету: `{performance_metrics['budget_adherence_score']:.1f}/100`\n"
        message += f"📊 Стабільність витрат: `{performance_metrics['spending_consistency']:.1f}/100`\n\n"
    
    # Порівняння за місяцями
    if month_comparison:
        message += "📅 *Витрати за місяцями:*\n"
        for i, month_data in enumerate(month_comparison[:3]):
            emoji = "📍" if i == 0 else "📊"
            status = "(поточний)" if i == 0 else ""
            message += f"{emoji} {month_data['period']} {status}: `{month_data['total_expenses']:.2f} {currency}`\n"
        message += "\n"
    
    # Витрати за тиждень
    if daily_stats:
        week_total = sum(day['amount'] for day in daily_stats)
        avg_daily = week_total / len(daily_stats) if daily_stats else 0
        message += f"📈 *За останні 7 днів:*\n"
        message += f"💰 Загальні витрати: `{week_total:.2f} {currency}`\n"
        message += f"📊 Середньо за день: `{avg_daily:.2f} {currency}`\n\n"
    
    keyboard = [
        [InlineKeyboardButton("📈 Детальна аналітика", callback_data="budget_detailed_analytics")],
        [InlineKeyboardButton("📊 Експорт звіту", callback_data="budget_export_report")],
        [InlineKeyboardButton("🔙 Назад", callback_data="my_budget_overview")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def confirm_budget_reset(query, context):
    """Підтвердження скидання бюджету"""
    message = "⚠️ *Скидання бюджету*\n\n"
    message += "Ви впевнені, що хочете скинути поточний бюджет?\n\n"
    message += "Це дія:\n"
    message += "• Видалить всі налаштовані ліміти\n"
    message += "• Деактивує поточний бюджетний план\n"
    message += "• Збереже історію транзакцій\n\n"
    message += "❗️ Цю дію неможливо відмінити!"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Так, скинути", callback_data="budget_reset_confirmed"),
            InlineKeyboardButton("❌ Скасувати", callback_data="my_budget_overview")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def execute_budget_reset(query, context):
    """Виконує скидання бюджету"""
    from services.budget_manager import BudgetManager
    
    telegram_id = query.from_user.id
    user = get_or_create_user(telegram_id)
    budget_manager = BudgetManager(user.id)
    
    # Виконуємо скидання
    result = budget_manager.reset_monthly_budget(confirm=True)
    
    if result['status'] == 'success':
        message = "✅ *Бюджет успішно скинуто*\n\n"
        message += "Тепер ви можете:\n"
        message += "• Встановити новий місячний бюджет\n"
        message += "• Налаштувати ліміти по категоріях\n"
        message += "• Створити розумний бюджет на основі історії\n\n"
        message += "Що бажаєте зробити далі?"
        
        keyboard = [
            [InlineKeyboardButton("💰 Встановити новий бюджет", callback_data="budget_change_total")],
            [InlineKeyboardButton("🎯 Створити розумний бюджет", callback_data="budget_create_smart")],
            [InlineKeyboardButton("🔙 До головного меню", callback_data="main_menu")]
        ]
    else:
        message = "❌ *Помилка*\n\n"
        message += "Не вдалося скинути бюджет. Спробуйте ще раз."
        
        keyboard = [
            [InlineKeyboardButton("🔄 Спробувати ще раз", callback_data="budget_reset_confirm")],
            [InlineKeyboardButton("🔙 Назад", callback_data="my_budget_overview")]
        ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_expense_pie_chart(query, context):
    """Показує кругову діаграму витрат по категоріях з огляду фінансів"""
    try:
        user = get_or_create_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Створюємо звіт для генерації діаграми
        financial_report = FinancialReport(user.id)
        
        # Генеруємо кругову діаграму за поточний місяць
        chart_buffer, error = financial_report.generate_expense_pie_chart()
        
        if error or not chart_buffer:
            await query.edit_message_text(
                "📊 Немає даних для створення діаграми витрат\n\n" +
                "💡 *Почніть додавати витрати, щоб побачити розподіл по категоріях*",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 До огляду", callback_data="my_budget_overview")
                ]]),
                parse_mode="Markdown"
            )
            return
        
        # Відправляємо діаграму з лаконічним і сучасним підписом
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=chart_buffer,
            caption=(
                "📊 *Розподіл витрат по категоріях*\n"
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💰 Доходи", callback_data="show_income_pie_chart")
                ],
                [
                    InlineKeyboardButton("🔙 До огляду", callback_data="my_budget_overview")
                ]
            ])
        )
        
    except Exception as e:
        logger.error(f"Error in show_expense_pie_chart: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка створення діаграми\n\n" +
            "Спробуйте пізніше або зверніться до підтримки.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 До огляду", callback_data="my_budget_overview")
            ]]),
            parse_mode="Markdown"
        )

async def show_income_pie_chart(query, context):
    """Показує кругову діаграму доходів по категоріях"""
    try:
        user = get_or_create_user(query.from_user.id)
        
        # Створюємо звіт для генерації діаграми
        financial_report = FinancialReport(user.id)
        
        # Генеруємо кругову діаграму доходів за поточний місяць
        chart_buffer, error = financial_report.generate_income_pie_chart()
        
        if error or not chart_buffer:
            await query.edit_message_text(
                "📊 Немає даних для створення діаграми доходів\n\n" +
                "💡 *Почніть додавати доходи, щоб побачити розподіл по джерелах*",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 До огляду", callback_data="my_budget_overview")
                ]]),
                parse_mode="Markdown"
            )
            return
        
        # Відправляємо діаграму з лаконічним підписом
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=chart_buffer,
            caption=(
                "💰 *Розподіл доходів по категоріях*\n"
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 Витрати", callback_data="show_expense_pie_chart")
                ],
                [
                    InlineKeyboardButton("🔙 До огляду", callback_data="my_budget_overview")
                ]
            ])
        )
        
    except Exception as e:
        logger.error(f"Error in show_income_pie_chart: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка створення діаграми доходів",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 До огляду", callback_data="my_budget_overview")
            ]]),
            parse_mode="Markdown"
        )

def create_progress_bar(percentage, width=10):
    """Створює текстовий прогрес-бар"""
    filled = int(percentage / 100 * width)
    empty = width - filled
    
    if percentage > 100:
        # Червоний прогрес-бар для перевищення
        bar = "🔴" * min(filled, width) + "⚪" * max(0, empty)
    elif percentage > 80:
        # Жовтий прогрес-бар для попередження
        bar = "🟡" * filled + "⚪" * empty
    else:
        # Зелений прогрес-бар для нормального стану
        bar = "🟢" * filled + "⚪" * empty
    
    return bar
