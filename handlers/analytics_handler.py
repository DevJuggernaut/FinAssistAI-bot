"""
Модуль аналітики для бота FinAssist.
Включає статистику витрат, AI рекомендації та звіти за період.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
import calendar
import logging

from database.db_operations import get_user, get_monthly_stats, get_user_transactions, get_user_categories
from database.models import TransactionType
from services.financial_advisor import get_financial_advice

logger = logging.getLogger(__name__)

# ==================== ГОЛОВНЕ МЕНЮ АНАЛІТИКИ ====================

async def show_analytics_main_menu(query, context):
    """Показує головне меню аналітики"""
    try:
        keyboard = [
            [
                InlineKeyboardButton("📈 Статистика витрат", callback_data="analytics_expense_stats"),
                InlineKeyboardButton("💡 AI рекомендації", callback_data="analytics_ai_recommendations")
            ],
            [
                InlineKeyboardButton("📋 Звіти за період", callback_data="analytics_period_reports"),
                InlineKeyboardButton("📊 Порівняння періодів", callback_data="analytics_period_comparison")
            ],
            [
                InlineKeyboardButton("🔍 Детальний аналіз", callback_data="analytics_detailed_analysis"),
                InlineKeyboardButton("⚙️ Налаштування", callback_data="analytics_settings")
            ],
            [
                InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")
            ]
        ]
        
        text = (
            "📊 **Аналітика FinAssist**\n\n"
            "Глибокий аналіз ваших фінансових звичок:\n\n"
            "📈 *Статистика витрат* — огляд по категоріях та періодах\n"
            "💡 *AI рекомендації* — персоналізовані поради від ШІ\n"
            "📋 *Звіти за період* — детальні звіти з можливістю експорту\n"
            "📊 *Порівняння періодів* — аналіз трендів та змін\n\n"
            "💭 *Порада:* Регулярно переглядайте аналітику для кращого контролю фінансів"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_analytics_main_menu: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні аналітики",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]])
        )

# ==================== СТАТИСТИКА ВИТРАТ ====================

async def show_expense_statistics(query, context):
    """Показує статистику витрат з вибором періоду"""
    keyboard = [
        [
            InlineKeyboardButton("📅 Тиждень", callback_data="expense_stats_week"),
            InlineKeyboardButton("📆 Місяць", callback_data="expense_stats_month")
        ],
        [
            InlineKeyboardButton("📊 Квартал", callback_data="expense_stats_quarter"),
            InlineKeyboardButton("📈 Рік", callback_data="expense_stats_year")
        ],
        [
            InlineKeyboardButton("🎯 Останні 30 днів", callback_data="expense_stats_30days"),
            InlineKeyboardButton("⚡ Поточний місяць", callback_data="expense_stats_current_month")
        ],
        [
            InlineKeyboardButton("📋 Розподіл по категоріях", callback_data="expense_stats_categories"),
            InlineKeyboardButton("🏆 Топ операцій", callback_data="expense_stats_top")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="analytics")
        ]
    ]
    
    text = (
        "📈 **Статистика витрат**\n\n"
        "Оберіть період для аналізу:\n\n"
        "📅 *Швидкий вибір:*\n"
        "• Тиждень — останні 7 днів\n"
        "• Місяць — поточний календарний місяць\n"
        "• Квартал — останні 3 місяці\n"
        "• Рік — останні 12 місяців\n\n"
        "📊 *Детальний аналіз:*\n"
        "• Розподіл по категоріях\n"
        "• Топ найбільших операцій\n"
        "• Порівняння з попереднім періодом"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_period_statistics(query, context, period_type):
    """Показує статистику за обраний період"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Визначаємо період
        now = datetime.now()
        if period_type == "week":
            start_date = now - timedelta(days=7)
            period_name = "останній тиждень"
        elif period_type == "month":
            start_date = now.replace(day=1)
            period_name = "поточний місяць"
        elif period_type == "quarter":
            start_date = now - timedelta(days=90)
            period_name = "останній квартал"
        elif period_type == "year":
            start_date = now - timedelta(days=365)
            period_name = "останній рік"
        elif period_type == "30days":
            start_date = now - timedelta(days=30)
            period_name = "останні 30 днів"
        elif period_type == "current_month":
            start_date = now.replace(day=1)
            period_name = "поточний місяць"
        else:
            start_date = now - timedelta(days=30)
            period_name = "останні 30 днів"
        
        # Отримуємо транзакції за період
        transactions = get_user_transactions(user.id, start_date, now)
        
        # Розраховуємо статистику
        total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
        total_expenses = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)
        balance = total_income - total_expenses
        
        # Статистика по категоріях
        categories_stats = {}
        for transaction in transactions:
            if transaction.type == TransactionType.EXPENSE and transaction.category:
                cat_name = transaction.category.name
                if cat_name not in categories_stats:
                    categories_stats[cat_name] = 0
                categories_stats[cat_name] += transaction.amount
        
        # Сортуємо категорії за сумою
        sorted_categories = sorted(categories_stats.items(), key=lambda x: x[1], reverse=True)
        
        # Формуємо текст статистики
        text = f"📈 **Статистика за {period_name}**\n\n"
        text += f"💰 *Доходи:* `{total_income:.2f} грн`\n"
        text += f"💸 *Витрати:* `{total_expenses:.2f} грн`\n"
        text += f"💼 *Баланс:* `{balance:.2f} грн`\n\n"
        
        if balance >= 0:
            text += "✅ *Позитивний баланс* — ви економите!\n\n"
        else:
            text += "⚠️ *Негативний баланс* — витрати перевищують доходи\n\n"
        
        # Додаємо топ-3 категорії
        if sorted_categories:
            text += "🏆 *Топ категорії витрат:*\n"
            for i, (category, amount) in enumerate(sorted_categories[:3], 1):
                percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                text += f"{i}. {category}: `{amount:.2f} грн` ({percentage:.1f}%)\n"
        
        text += f"\n📊 Всього операцій: {len(transactions)}"
        
        keyboard = [
            [
                InlineKeyboardButton("📋 Детальний розподіл", callback_data=f"detailed_categories_{period_type}"),
                InlineKeyboardButton("🏆 Топ операцій", callback_data=f"top_transactions_{period_type}")
            ],
            [
                InlineKeyboardButton("📈 Порівняти з минулим", callback_data=f"compare_periods_{period_type}"),
                InlineKeyboardButton("💡 AI аналіз", callback_data=f"ai_analysis_{period_type}")
            ],
            [
                InlineKeyboardButton("🔄 Оновити", callback_data=f"expense_stats_{period_type}"),
                InlineKeyboardButton("🔙 Назад", callback_data="analytics_expense_stats")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_period_statistics: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при формуванні статистики",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="analytics_expense_stats")]])
        )

# ==================== AI РЕКОМЕНДАЦІЇ ====================

async def show_ai_recommendations(query, context):
    """Показує AI рекомендації"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Отримуємо дані для аналізу
        now = datetime.now()
        start_date = now - timedelta(days=30)
        transactions = get_user_transactions(user.id, start_date, now)
        
        # Формуємо запит до AI
        total_expenses = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)
        total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
        
        # Категорії витрат
        expense_categories = {}
        for t in transactions:
            if t.type == TransactionType.EXPENSE and t.category:
                cat = t.category.name
                expense_categories[cat] = expense_categories.get(cat, 0) + t.amount
        
        # Отримуємо поради від AI
        advice = await get_financial_advice(
            user_id=user.id,
            monthly_budget=user.monthly_budget or 0,
            current_expenses=total_expenses,
            categories=expense_categories
        )
        
        keyboard = [
            [
                InlineKeyboardButton("💡 Поради з економії", callback_data="ai_savings_tips"),
                InlineKeyboardButton("📈 Планування бюджету", callback_data="ai_budget_planning")
            ],
            [
                InlineKeyboardButton("🔍 Аналіз паттернів", callback_data="ai_pattern_analysis"),
                InlineKeyboardButton("🎯 Цілі на місяць", callback_data="ai_monthly_goals")
            ],
            [
                InlineKeyboardButton("❓ Запитати AI", callback_data="ai_custom_question"),
                InlineKeyboardButton("🔄 Оновити аналіз", callback_data="analytics_ai_recommendations")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="analytics")
            ]
        ]
        
        text = (
            "💡 **AI Рекомендації**\n\n"
            f"📊 *Аналіз за останні 30 днів:*\n"
            f"💸 Витрати: `{total_expenses:.2f} грн`\n"
            f"💰 Доходи: `{total_income:.2f} грн`\n\n"
            f"🤖 *Персоналізовані поради:*\n"
            f"{advice}\n\n"
            "🎯 *Що ще можна проаналізувати:*\n"
            "• Поради з економії грошей\n"
            "• Планування бюджету на наступний місяць\n"
            "• Виявлення необычних паттернів витрат\n"
            "• Постановка фінансових цілей"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_ai_recommendations: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при отриманні AI рекомендацій",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="analytics")]])
        )

# ==================== ЗВІТИ ЗА ПЕРІОД ====================

async def show_period_reports(query, context):
    """Показує меню звітів за період"""
    keyboard = [
        [
            InlineKeyboardButton("📅 Швидкий звіт", callback_data="quick_report_menu"),
            InlineKeyboardButton("🎯 Кастомний період", callback_data="custom_period_report")
        ],
        [
            InlineKeyboardButton("📊 Місячний звіт", callback_data="monthly_report_select"),
            InlineKeyboardButton("📈 Квартальний звіт", callback_data="quarterly_report")
        ],
        [
            InlineKeyboardButton("🏷️ Звіт по категоріях", callback_data="category_report"),
            InlineKeyboardButton("💰 Звіт по сумах", callback_data="amount_report")
        ],
        [
            InlineKeyboardButton("📤 Експорт даних", callback_data="export_data_menu"),
            InlineKeyboardButton("📧 Надіслати звіт", callback_data="send_report_menu")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="analytics")
        ]
    ]
    
    text = (
        "📋 **Звіти за період**\n\n"
        "Створюйте детальні звіти про ваші фінанси:\n\n"
        "📅 *Швидкий звіт* — готові шаблони періодів\n"
        "🎯 *Кастомний період* — оберіть власні дати\n"
        "📊 *Місячний звіт* — детальний аналіз за місяць\n"
        "🏷️ *По категоріях* — розбивка по типах витрат\n\n"
        "📤 *Експорт:* Зберігайте звіти у форматі Excel/PDF\n"
        "📧 *Відправка:* Діліться звітами через месенджери"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ==================== ПОРІВНЯННЯ ПЕРІОДІВ ====================

async def show_period_comparison(query, context):
    """Показує порівняння між різними періодами"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Цей vs минулий місяць", callback_data="compare_current_prev_month"),
            InlineKeyboardButton("📈 Цей vs минулий тиждень", callback_data="compare_current_prev_week")
        ],
        [
            InlineKeyboardButton("🔄 Останні 30 vs попередні 30", callback_data="compare_30_days"),
            InlineKeyboardButton("📅 Цей vs минулий квартал", callback_data="compare_quarters")
        ],
        [
            InlineKeyboardButton("📆 Рік до року", callback_data="compare_year_to_year"),
            InlineKeyboardButton("🎯 Кастомне порівняння", callback_data="custom_comparison")
        ],
        [
            InlineKeyboardButton("📊 Трендовий аналіз", callback_data="trend_analysis"),
            InlineKeyboardButton("🔙 Назад", callback_data="analytics")
        ]
    ]
    
    text = (
        "📊 **Порівняння періодів**\n\n"
        "Аналізуйте зміни у ваших фінансових звичках:\n\n"
        "📈 *Стандартні порівняння:*\n"
        "• Поточний vs попередній місяць\n"
        "• Тиждень до тижня\n"
        "• Квартал до кварталу\n\n"
        "🎯 *Кастомні періоди:*\n"
        "• Оберіть будь-які дати для порівняння\n"
        "• Аналіз трендів за довгий період\n\n"
        "📊 *Що аналізуємо:*\n"
        "• Зміни в доходах та витратах\n"
        "• Динаміка по категоріях\n"
        "• Загальний фінансовий тренд"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ==================== ДЕТАЛЬНІ АНАЛІТИЧНІ ФУНКЦІЇ ====================

async def show_detailed_categories(query, context, period_type):
    """Показує детальний розподіл по категоріях"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Визначаємо період
        now = datetime.now()
        if period_type == "week":
            start_date = now - timedelta(days=7)
            period_name = "тиждень"
        elif period_type == "month":
            start_date = now.replace(day=1)
            period_name = "місяць"
        elif period_type == "quarter":
            start_date = now - timedelta(days=90)
            period_name = "квартал"
        elif period_type == "year":
            start_date = now - timedelta(days=365)
            period_name = "рік"
        else:
            start_date = now - timedelta(days=30)
            period_name = "30 днів"
        
        # Отримуємо транзакції
        transactions = get_user_transactions(user.id, start_date, now)
        expense_transactions = [t for t in transactions if t.type == TransactionType.EXPENSE]
        
        # Групуємо по категоріях
        categories_stats = {}
        total_expenses = 0
        for transaction in expense_transactions:
            if transaction.category:
                cat_name = transaction.category.name
                cat_icon = getattr(transaction.category, 'icon', '💸')
                if cat_name not in categories_stats:
                    categories_stats[cat_name] = {'amount': 0, 'count': 0, 'icon': cat_icon}
                categories_stats[cat_name]['amount'] += transaction.amount
                categories_stats[cat_name]['count'] += 1
                total_expenses += transaction.amount
        
        # Сортуємо по сумі
        sorted_categories = sorted(categories_stats.items(), key=lambda x: x[1]['amount'], reverse=True)
        
        text = f"📊 **Розподіл по категоріях ({period_name})**\n\n"
        text += f"💸 *Загальні витрати:* `{total_expenses:.2f} грн`\n"
        text += f"📋 *Операцій:* {len(expense_transactions)}\n\n"
        
        if sorted_categories:
            for i, (category, stats) in enumerate(sorted_categories[:10], 1):
                percentage = (stats['amount'] / total_expenses * 100) if total_expenses > 0 else 0
                avg_per_transaction = stats['amount'] / stats['count'] if stats['count'] > 0 else 0
                
                text += f"{stats['icon']} **{category}**\n"
                text += f"   💰 `{stats['amount']:.2f} грн` ({percentage:.1f}%)\n"
                text += f"   📊 {stats['count']} операцій, середня: `{avg_per_transaction:.2f} грн`\n\n"
        else:
            text += "📭 Немає витрат за цей період"
        
        keyboard = [
            [
                InlineKeyboardButton("📈 Сортувати за сумою", callback_data=f"sort_categories_amount_{period_type}"),
                InlineKeyboardButton("📊 Сортувати за кількістю", callback_data=f"sort_categories_count_{period_type}")
            ],
            [
                InlineKeyboardButton("💡 AI аналіз категорій", callback_data=f"ai_category_analysis_{period_type}"),
                InlineKeyboardButton("📋 Експортувати", callback_data=f"export_categories_{period_type}")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data=f"expense_stats_{period_type}")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_detailed_categories: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при аналізі категорій",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=f"expense_stats_{period_type}")]])
        )

async def show_top_transactions(query, context, period_type):
    """Показує топ операцій за період"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Визначаємо період
        now = datetime.now()
        if period_type == "week":
            start_date = now - timedelta(days=7)
            period_name = "тиждень"
        elif period_type == "month":
            start_date = now.replace(day=1)
            period_name = "місяць"
        elif period_type == "quarter":
            start_date = now - timedelta(days=90)
            period_name = "квартал"
        elif period_type == "year":
            start_date = now - timedelta(days=365)
            period_name = "рік"
        else:
            start_date = now - timedelta(days=30)
            period_name = "30 днів"
        
        # Отримуємо транзакції
        transactions = get_user_transactions(user.id, start_date, now)
        
        # Розділяємо на доходи та витрати
        expenses = [t for t in transactions if t.type == TransactionType.EXPENSE]
        incomes = [t for t in transactions if t.type == TransactionType.INCOME]
        
        # Сортуємо за сумою
        top_expenses = sorted(expenses, key=lambda x: x.amount, reverse=True)[:5]
        top_incomes = sorted(incomes, key=lambda x: x.amount, reverse=True)[:5]
        
        # Аналіз найактивніших днів
        daily_counts = {}
        for t in transactions:
            date_key = t.transaction_date.strftime("%Y-%m-%d")
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        most_active_days = sorted(daily_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        text = f"🏆 **Топ операцій ({period_name})**\n\n"
        
        # Топ витрат
        if top_expenses:
            text += "💸 *5 найбільших витрат:*\n"
            for i, transaction in enumerate(top_expenses, 1):
                date_str = transaction.transaction_date.strftime("%d.%m")
                category = transaction.category.name if transaction.category else "Без категорії"
                desc = transaction.description[:20] + "..." if len(transaction.description) > 20 else transaction.description
                text += f"{i}. `{transaction.amount:.2f} грн` — {category}\n"
                text += f"   📅 {date_str} | {desc}\n\n"
        
        # Топ доходів
        if top_incomes:
            text += "💰 *5 найбільших доходів:*\n"
            for i, transaction in enumerate(top_incomes, 1):
                date_str = transaction.transaction_date.strftime("%d.%m")
                category = transaction.category.name if transaction.category else "Без категорії"
                desc = transaction.description[:20] + "..." if len(transaction.description) > 20 else transaction.description
                text += f"{i}. `{transaction.amount:.2f} грн` — {category}\n"
                text += f"   📅 {date_str} | {desc}\n\n"
        
        # Найактивніші дні
        if most_active_days:
            text += "📈 *Найактивніші дні:*\n"
            for date_str, count in most_active_days:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d.%m.%Y")
                weekday = calendar.day_name[date_obj.weekday()]
                text += f"📅 {formatted_date} ({weekday[:3]}) — {count} операцій\n"
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Деталі витрат", callback_data=f"expense_details_{period_type}"),
                InlineKeyboardButton("💰 Деталі доходів", callback_data=f"income_details_{period_type}")
            ],
            [
                InlineKeyboardButton("📈 Аналіз активності", callback_data=f"activity_analysis_{period_type}"),
                InlineKeyboardButton("💡 AI інсайти", callback_data=f"ai_transaction_insights_{period_type}")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data=f"expense_stats_{period_type}")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_top_transactions: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при аналізі топ операцій",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=f"expense_stats_{period_type}")]])
        )

# ==================== AI АНАЛІЗ СПЕЦИФІЧНИХ ОБЛАСТЕЙ ====================

async def show_ai_savings_tips(query, context):
    """Показує AI поради з економії"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Отримуємо дані за останні 30 днів
        now = datetime.now()
        start_date = now - timedelta(days=30)
        transactions = get_user_transactions(user.id, start_date, now)
        
        # Аналізуємо категорії витрат
        categories_stats = {}
        total_expenses = 0
        for t in transactions:
            if t.type == TransactionType.EXPENSE and t.category:
                cat_name = t.category.name
                categories_stats[cat_name] = categories_stats.get(cat_name, 0) + t.amount
                total_expenses += t.amount
        
        # Формуємо персоналізовані поради
        tips = []
        
        # Аналіз найбільших категорій
        if categories_stats:
            top_category = max(categories_stats.items(), key=lambda x: x[1])
            percentage = (top_category[1] / total_expenses * 100) if total_expenses > 0 else 0
            
            if percentage > 30:
                tips.append(f"🎯 Ваша найбільша категорія витрат — {top_category[0]} ({percentage:.1f}%). Спробуйте зменшити витрати тут на 10-15%.")
        
        # Поради залежно від бюджету
        if user.monthly_budget and total_expenses > user.monthly_budget:
            overspend = total_expenses - user.monthly_budget
            tips.append(f"⚠️ Ви перевищили місячний бюджет на {overspend:.2f} грн. Рекомендуємо переглянути найбільші категорії витрат.")
        
        # Загальні поради
        tips.extend([
            "💡 Веддіть щоденний облік витрат — це допоможе краще контролювати фінанси",
            "🎯 Встановіть ліміти на категорії, які 'з'їдають' найбільше коштів",
            "📊 Регулярно переглядайте статистику — це допомагає виявити неочевидні витрати",
            "💰 Спробуйте правило 50/30/20: 50% на потреби, 30% на бажання, 20% на заощадження"
        ])
        
        text = (
            "💡 **Персональні поради з економії**\n\n"
            f"📊 *Аналіз за останні 30 днів:*\n"
            f"💸 Загальні витрати: `{total_expenses:.2f} грн`\n"
            f"🎯 Місячний бюджет: `{user.monthly_budget or 'не встановлено'}`\n\n"
            "🤖 *AI рекомендації:*\n\n"
        )
        
        for i, tip in enumerate(tips[:5], 1):
            text += f"{i}. {tip}\n\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🎯 Встановити ліміти", callback_data="set_category_limits"),
                InlineKeyboardButton("📈 Планування бюджету", callback_data="ai_budget_planning")
            ],
            [
                InlineKeyboardButton("💰 Цілі заощаджень", callback_data="savings_goals"),
                InlineKeyboardButton("🔄 Оновити поради", callback_data="ai_savings_tips")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="analytics_ai_recommendations")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_ai_savings_tips: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при формуванні порад",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="analytics_ai_recommendations")]])
        )

# ==================== ДОПОМІЖНІ ФУНКЦІЇ ====================

async def show_analytics_settings(query, context):
    """Показує налаштування аналітики"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Автозвіти", callback_data="analytics_auto_reports"),
            InlineKeyboardButton("📊 Формат звітів", callback_data="analytics_report_format")
        ],
        [
            InlineKeyboardButton("🎯 Цілі та нагадування", callback_data="analytics_goals_reminders"),
            InlineKeyboardButton("📧 Налаштування експорту", callback_data="analytics_export_settings")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="analytics")
        ]
    ]
    
    text = (
        "⚙️ **Налаштування аналітики**\n\n"
        "Персоналізуйте ваш досвід аналітики:\n\n"
        "🔔 *Автозвіти* — отримуйте щотижневі/щомісячні звіти\n"
        "📊 *Формат звітів* — налаштуйте вигляд та деталізацію\n"
        "🎯 *Цілі* — встановіть фінансові цілі та отримуйте нагадування\n"
        "📧 *Експорт* — налаштуйте формати файлів для збереження"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_auto_reports_settings(query, context):
    """Налаштування автоматичних звітів"""
    keyboard = [
        [
            InlineKeyboardButton("📅 Щотижневі звіти", callback_data="weekly_reports_toggle"),
            InlineKeyboardButton("📅 Щомісячні звіти", callback_data="monthly_reports_toggle")
        ],
        [
            InlineKeyboardButton("🕐 Час відправки", callback_data="report_time_settings"),
            InlineKeyboardButton("📧 Email звіти", callback_data="email_reports_settings")
        ],
        [
            InlineKeyboardButton("📊 Зміст звітів", callback_data="report_content_settings"),
            InlineKeyboardButton("🔔 Формат нагадувань", callback_data="reminder_format_settings")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="analytics_settings")
        ]
    ]
    
    text = (
        "🔔 **Налаштування автоматичних звітів**\n\n"
        "Отримуйте регулярні звіти про ваші фінанси:\n\n"
        "📅 *Періодичність:*\n"
        "• Щотижневі підсумки\n"
        "• Щомісячні звіти\n"
        "• Квартальна аналітика\n\n"
        "📊 *Зміст звітів:*\n"
        "• Загальна статистика\n"
        "• Топ категорії витрат\n"
        "• Порівняння з попереднім періодом\n"
        "• AI рекомендації\n"
        "• Прогрес цілей заощаджень\n\n"
        "⏰ *Гнучкість:* Налаштуйте час та формат під ваші потреби"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_report_format_settings(query, context):
    """Налаштування формату звітів"""
    keyboard = [
        [
            InlineKeyboardButton("📋 Текстовий формат", callback_data="format_text"),
            InlineKeyboardButton("📊 З графіками", callback_data="format_charts")
        ],
        [
            InlineKeyboardButton("📄 PDF експорт", callback_data="format_pdf"),
            InlineKeyboardButton("📈 Excel файли", callback_data="format_excel")
        ],
        [
            InlineKeyboardButton("🎨 Стиль звітів", callback_data="report_style_settings"),
            InlineKeyboardButton("📏 Рівень деталізації", callback_data="detail_level_settings")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="analytics_settings")
        ]
    ]
    
    text = (
        "📊 **Налаштування формату звітів**\n\n"
        "Персоналізуйте вигляд ваших фінансових звітів:\n\n"
        "📋 *Формати:*\n"
        "• Короткі текстові зведення\n"
        "• Детальні звіти з графіками\n"
        "• PDF документи для архіву\n"
        "• Excel файли для аналізу\n\n"
        "🎨 *Стилізація:*\n"
        "• Кольорові схеми\n"
        "• Рівень деталізації\n"
        "• Включення AI коментарів\n"
        "• Персональні нотатки\n\n"
        "💡 *Порада:* Оберіть формат залежно від того, як ви плануєте використовувати звіти"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_goals_reminders_settings(query, context):
    """Налаштування цілей та нагадувань"""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Налаштування цілей", callback_data="configure_goals"),
            InlineKeyboardButton("🔔 Частота нагадувань", callback_data="reminder_frequency")
        ],
        [
            InlineKeyboardButton("📱 Типи повідомлень", callback_data="notification_types"),
            InlineKeyboardButton("⏰ Час нагадувань", callback_data="reminder_time")
        ],
        [
            InlineKeyboardButton("🎖️ Досягнення та винагороди", callback_data="achievements_settings"),
            InlineKeyboardButton("📊 Прогрес-бар в повідомленнях", callback_data="progress_display")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="analytics_settings")
        ]
    ]
    
    text = (
        "🎯 **Цілі та нагадування**\n\n"
        "Налаштуйте систему мотивації та контролю:\n\n"
        "🔔 *Нагадування:*\n"
        "• Щоденні мотиваційні повідомлення\n"
        "• Попередження про перевитрати\n"
        "• Нагадування про заощадження\n"
        "• Прогрес досягнення цілей\n\n"
        "🎖️ *Система досягнень:*\n"
        "• Бейджі за економію\n"
        "• Винагороди за досягнення цілей\n"
        "• Статистика успіхів\n"
        "• Особисті рекорди\n\n"
        "💪 *Мотивація:* Правильні нагадування допомагають досягати фінансових цілей!"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_export_settings(query, context):
    """Налаштування експорту даних"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Excel експорт", callback_data="excel_export_config"),
            InlineKeyboardButton("📄 PDF звіти", callback_data="pdf_export_config")
        ],
        [
            InlineKeyboardButton("📅 CSV файли", callback_data="csv_export_config"),
            InlineKeyboardButton("📈 Графіки PNG", callback_data="charts_export_config")
        ],
        [
            InlineKeyboardButton("☁️ Хмарне збереження", callback_data="cloud_storage_config"),
            InlineKeyboardButton("📧 Email надсилання", callback_data="email_sending_config")
        ],
        [
            InlineKeyboardButton("🔐 Безпека та приватність", callback_data="privacy_settings"),
            InlineKeyboardButton("⚙️ Автоекспорт", callback_data="auto_export_settings")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="analytics_settings")
        ]
    ]
    
    text = (
        "📤 **Налаштування експорту**\n\n"
        "Налаштуйте експорт ваших фінансових даних:\n\n"
        "📊 *Формати файлів:*\n"
        "• Excel таблиці з формулами\n"
        "• PDF звіти з графіками\n"
        "• CSV файли для імпорту\n"
        "• PNG графіки та діаграми\n\n"
        "☁️ *Збереження:*\n"
        "• Google Drive інтеграція\n"
        "• Dropbox синхронізація\n"
        "• Email автовідправка\n"
        "• Локальне збереження\n\n"
        "🔐 *Безпека:* Всі дані шифруються перед експортом"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ==================== AI АНАЛІЗ ПО ПЕРІОДАХ ====================

async def show_ai_analysis_for_period(query, context, period_type):
    """Показує AI аналіз для обраного періоду"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return

        # Визначаємо період
        now = datetime.now()
        if period_type == "week":
            start_date = now - timedelta(days=7)
            period_name = "тиждень"
        elif period_type == "month":
            start_date = now.replace(day=1)
            period_name = "місяць"
        elif period_type == "quarter":
            start_date = now - timedelta(days=90)
            period_name = "квартал"
        elif period_type == "year":
            start_date = now - timedelta(days=365)
            period_name = "рік"
        else:
            start_date = now - timedelta(days=30)
            period_name = "30 днів"

        # Отримуємо транзакції
        transactions = get_user_transactions(user.id, start_date, now)
        
        # Формуємо AI аналіз
        total_expenses = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)
        total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
        
        # Аналіз трендів
        analysis_points = []
        
        if total_income > 0:
            expense_ratio = (total_expenses / total_income) * 100
            if expense_ratio > 90:
                analysis_points.append("⚠️ **Критично високий рівень витрат** — ви витрачаєте понад 90% доходу")
            elif expense_ratio > 70:
                analysis_points.append("⚡ **Високі витрати** — рекомендуємо проаналізувати найбільші категорії")
            else:
                analysis_points.append("✅ **Помірні витрати** — ваш рівень витрат у нормі")
        
        # Аналіз категорій
        categories_analysis = {}
        for transaction in transactions:
            if transaction.type == TransactionType.EXPENSE and transaction.category:
                cat_name = transaction.category.name
                if cat_name not in categories_analysis:
                    categories_analysis[cat_name] = []
                categories_analysis[cat_name].append(transaction.amount)
        
        # Знаходимо проблемні категорії
        for cat, amounts in categories_analysis.items():
            total_cat = sum(amounts)
            if total_expenses > 0:
                percentage = (total_cat / total_expenses) * 100
                if percentage > 30:
                    analysis_points.append(f"🎯 **{cat}** — {percentage:.1f}% бюджету. Розгляньте можливості економії")
                elif percentage > 20:
                    analysis_points.append(f"📊 **{cat}** — значна частка витрат ({percentage:.1f}%)")
        
        # Загальні AI рекомендації
        if len(transactions) < 5:
            analysis_points.append("📝 **Мало даних** — додайте більше транзакцій для точнішого аналізу")
        
        text = f"🤖 **AI Аналіз за {period_name}**\n\n"
        text += f"💰 *Доходи:* `{total_income:.2f} грн`\n"
        text += f"💸 *Витрати:* `{total_expenses:.2f} грн`\n"
        text += f"💼 *Баланс:* `{total_income - total_expenses:.2f} грн`\n\n"
        
        text += "🔍 **Аналіз AI:**\n\n"
        for point in analysis_points[:5]:  # Показуємо максимум 5 пунктів
            text += f"• {point}\n\n"
        
        if not analysis_points:
            text += "📊 Поки недостатньо даних для детального аналізу. Продовжуйте додавати транзакції!"
        
        keyboard = [
            [
                InlineKeyboardButton("💡 Персональні поради", callback_data="ai_savings_tips"),
                InlineKeyboardButton("📊 Детальна статистика", callback_data=f"expense_stats_{period_type}")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="analytics_ai_recommendations")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_ai_analysis_for_period: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при формуванні AI аналізу",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="analytics_ai_recommendations")]])
        )

# ==================== ПОРІВНЯННЯ ПЕРІОДІВ ДЕТАЛЬНО ====================

async def show_period_comparison_detail(query, context, period_type):
    """Детальне порівняння періодів"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return

        now = datetime.now()
        
        # Визначаємо поточний та попередній періоди
        if period_type == "week":
            current_start = now - timedelta(days=7)
            current_end = now
            prev_start = now - timedelta(days=14)
            prev_end = now - timedelta(days=7)
            period_name = "тиждень"
        elif period_type == "month":
            current_start = now.replace(day=1)
            current_end = now
            # Попередній місяць
            if now.month == 1:
                prev_start = now.replace(year=now.year-1, month=12, day=1)
                prev_end = now.replace(day=1) - timedelta(days=1)
            else:
                prev_start = now.replace(month=now.month-1, day=1)
                # Останній день попереднього місяця
                prev_end = now.replace(day=1) - timedelta(days=1)
            period_name = "місяць"
        else:  # 30 днів
            current_start = now - timedelta(days=30)
            current_end = now
            prev_start = now - timedelta(days=60)
            prev_end = now - timedelta(days=30)
            period_name = "30 днів"
        
        # Отримуємо транзакції для обох періодів
        current_transactions = get_user_transactions(user.id, current_start, current_end)
        prev_transactions = get_user_transactions(user.id, prev_start, prev_end)
        
        # Розраховуємо статистику
        current_income = sum(t.amount for t in current_transactions if t.type == TransactionType.INCOME)
        current_expenses = sum(t.amount for t in current_transactions if t.type == TransactionType.EXPENSE)
        
        prev_income = sum(t.amount for t in prev_transactions if t.type == TransactionType.INCOME)
        prev_expenses = sum(t.amount for t in prev_transactions if t.type == TransactionType.EXPENSE)
        
        # Розраховуємо зміни
        income_change = current_income - prev_income
        expenses_change = current_expenses - prev_expenses
        
        income_change_percent = (income_change / prev_income * 100) if prev_income > 0 else 0
        expenses_change_percent = (expenses_change / prev_expenses * 100) if prev_expenses > 0 else 0
        
        # Емодзі для змін
        income_emoji = "📈" if income_change > 0 else "📉" if income_change < 0 else "➡️"
        expenses_emoji = "📈" if expenses_change > 0 else "📉" if expenses_change < 0 else "➡️"
        
        text = f"📊 **Порівняння: поточний vs попередній {period_name}**\n\n"
        
        text += f"💰 **ДОХОДИ:**\n"
        text += f"Поточний: `{current_income:.2f} грн`\n"
        text += f"Попередній: `{prev_income:.2f} грн`\n"
        text += f"Зміна: {income_emoji} `{income_change:+.2f} грн ({income_change_percent:+.1f}%)`\n\n"
        
        text += f"💸 **ВИТРАТИ:**\n"
        text += f"Поточний: `{current_expenses:.2f} грн`\n"
        text += f"Попередній: `{prev_expenses:.2f} грн`\n"
        text += f"Зміна: {expenses_emoji} `{expenses_change:+.2f} грн ({expenses_change_percent:+.1f}%)`\n\n"
        
        # Висновки
        text += f"📝 **ВИСНОВКИ:**\n"
        if income_change > 0 and expenses_change < 0:
            text += "✅ Ідеальна ситуація: доходи зросли, витрати зменшились!\n"
        elif income_change > 0 and expenses_change > 0:
            if expenses_change_percent < income_change_percent:
                text += "👍 Добре: доходи зростають швидше за витрати\n"
            else:
                text += "⚠️ Увага: витрати зростають швидше за доходи\n"
        elif income_change < 0 and expenses_change < 0:
            text += "📊 Зменшились і доходи, і витрати\n"
        else:
            text += "📈 Змішана динаміка — варто проаналізувати детальніше\n"
        
        keyboard = [
            [
                InlineKeyboardButton("📋 Детальний аналіз", callback_data=f"detailed_categories_{period_type}"),
                InlineKeyboardButton("💡 AI поради", callback_data=f"ai_analysis_{period_type}")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="analytics_period_comparison")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_period_comparison_detail: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при порівнянні періодів",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="analytics_period_comparison")]])
        )

# ==================== НАЛАШТУВАННЯ АНАЛІТИКИ ====================

async def show_category_limits_settings(query, context):
    """Налаштування лімітів по категоріях"""
    keyboard = [
        [
            InlineKeyboardButton("🍔 Їжа та ресторани", callback_data="set_limit_food"),
            InlineKeyboardButton("🚗 Транспорт", callback_data="set_limit_transport")
        ],
        [
            InlineKeyboardButton("🛍️ Покупки", callback_data="set_limit_shopping"),
            InlineKeyboardButton("🏠 Житло та комунальні", callback_data="set_limit_utilities")
        ],
        [
            InlineKeyboardButton("💊 Здоров'я", callback_data="set_limit_health"),
            InlineKeyboardButton("🎬 Розваги", callback_data="set_limit_entertainment")
        ],
        [
            InlineKeyboardButton("🔧 Додати кастомний ліміт", callback_data="set_custom_limit"),
            InlineKeyboardButton("📊 Переглянути всі ліміти", callback_data="view_all_limits")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="analytics_ai_recommendations")
        ]
    ]
    
    text = (
        "🎯 **Налаштування лімітів категорій**\n\n"
        "Встановіть максимальні суми витрат для кожної категорії.\n"
        "Бот буде попереджати вас при наближенні до ліміту.\n\n"
        "📊 *Переваги лімітів:*\n"
        "• Контроль витрат в реальному часі\n"
        "• Попередження про перевитрати\n"
        "• Кращий бюджетний контроль\n"
        "• Автоматичні рекомендації\n\n"
        "💡 *Порада:* Встановлюйте реалістичні ліміти на основі вашої історії витрат"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_ai_budget_planning(query, context):
    """AI планування бюджету"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return

        # Отримуємо історію за останні 3 місяці для аналізу
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        transactions = get_user_transactions(user.id, start_date, end_date)
        
        # Аналізуємо середні витрати по категоріях
        monthly_averages = {}
        total_months = 3
        
        for transaction in transactions:
            if transaction.type == TransactionType.EXPENSE and transaction.category:
                cat_name = transaction.category.name
                if cat_name not in monthly_averages:
                    monthly_averages[cat_name] = 0
                monthly_averages[cat_name] += transaction.amount
        
        # Розраховуємо середньомісячні витрати
        for cat in monthly_averages:
            monthly_averages[cat] = monthly_averages[cat] / total_months
        
        # Сортуємо за сумою
        sorted_categories = sorted(monthly_averages.items(), key=lambda x: x[1], reverse=True)
        
        # Формуємо рекомендації
        total_avg_expenses = sum(monthly_averages.values())
        recommended_budget = total_avg_expenses * 1.15  # 15% буфер
        
        text = (
            "🤖 **AI Планування Бюджету**\n\n"
            f"📊 *Аналіз за останні 3 місяці:*\n"
            f"💸 Середні витрати: `{total_avg_expenses:.2f} грн/міс`\n"
            f"💰 Рекомендований бюджет: `{recommended_budget:.2f} грн/міс`\n\n"
            f"📈 *Топ категорії витрат:*\n"
        )
        
        for i, (category, amount) in enumerate(sorted_categories[:5], 1):
            percentage = (amount / total_avg_expenses * 100) if total_avg_expenses > 0 else 0
            recommended_limit = amount * 1.1  # 10% буфер для категорії
            text += f"{i}. **{category}**: `{amount:.2f}` грн ({percentage:.1f}%)\n"
            text += f"   *Рекомендований ліміт:* `{recommended_limit:.2f}` грн\n\n"
        
        text += (
            "💡 **AI Рекомендації:**\n"
            "• Встановіть ліміти на основі історичних даних\n"
            "• Додайте 10-15% буфер для непередбачених витрат\n"
            "• Переглядайте та коригуйте бюджет щомісяця\n"
            "• Відстежуйте тренди для планування майбутнього"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Створити бюджет", callback_data="create_ai_budget"),
                InlineKeyboardButton("🎯 Встановити ліміти", callback_data="set_category_limits")
            ],
            [
                InlineKeyboardButton("📊 Детальний аналіз", callback_data="detailed_budget_analysis"),
                InlineKeyboardButton("🔄 Оновити прогноз", callback_data="ai_budget_planning")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="analytics_ai_recommendations")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_ai_budget_planning: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при формуванні AI планування",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="analytics_ai_recommendations")]])
        )

async def show_savings_goals(query, context):
    """Цілі заощаджень"""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Створити нову ціль", callback_data="create_savings_goal"),
            InlineKeyboardButton("📊 Поточні цілі", callback_data="view_current_goals")
        ],
        [
            InlineKeyboardButton("🏆 Досягнуті цілі", callback_data="achieved_goals"),
            InlineKeyboardButton("📈 Прогрес цілей", callback_data="goals_progress")
        ],
        [
            InlineKeyboardButton("💡 Поради по заощадженнях", callback_data="savings_tips"),
            InlineKeyboardButton("🔔 Налаштування нагадувань", callback_data="goals_reminders")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="analytics_ai_recommendations")
        ]
    ]
    
    text = (
        "🎯 **Цілі заощаджень**\n\n"
        "Встановлюйте та відстежуйте ваші фінансові цілі:\n\n"
        "💰 *Типи цілей:*\n"
        "• Накопичення на покупку\n"
        "• Резервний фонд\n"
        "• Відпустка або подорож\n"
        "• Інвестиції\n"
        "• Погашення боргів\n\n"
        "📊 *Можливості:*\n"
        "• Відстеження прогресу в реальному часі\n"
        "• Автоматичні нагадування\n"
        "• AI рекомендації щодо заощаджень\n"
        "• Візуалізація досягнень\n\n"
        "🏆 *Мотивація:* Чіткі цілі допомагають заощаджувати ефективніше!"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ==================== ДОДАТКОВІ АНАЛІТИЧНІ ФУНКЦІЇ ====================

async def show_custom_period_comparison(query, context):
    """Кастомне порівняння періодів"""
    keyboard = [
        [
            InlineKeyboardButton("📅 Обрати дати", callback_data="select_custom_dates"),
            InlineKeyboardButton("🗓️ Швидкий вибір", callback_data="quick_period_select")
        ],
        [
            InlineKeyboardButton("📊 Цей vs минулий місяць", callback_data="compare_current_prev_month"),
            InlineKeyboardButton("📈 Квартал до кварталу", callback_data="compare_quarters")
        ],
        [
            InlineKeyboardButton("📆 Рік до року", callback_data="compare_year_to_year"),
            InlineKeyboardButton("⚡ Останні 30 vs 60", callback_data="compare_30_60_days")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="analytics_period_comparison")
        ]
    ]
    
    text = (
        "🎯 **Кастомне порівняння періодів**\n\n"
        "Порівняйте будь-які періоди для глибокого аналізу:\n\n"
        "📅 *Гнучкий вибір:*\n"
        "• Оберіть конкретні дати початку та кінця\n"
        "• Використовуйте готові шаблони\n"
        "• Порівнюйте різні за тривалістю періоди\n\n"
        "📊 *Що аналізуємо:*\n"
        "• Доходи та витрати\n"
        "• Розподіл по категоріях\n"
        "• Середні чеки та частота операцій\n"
        "• Тренди та сезонність\n\n"
        "💡 *Приклади використання:*\n"
        "• Порівняння до/після зміни роботи\n"
        "• Аналіз святкових періодів\n"
        "• Оцінка ефективності економії"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_trend_analysis(query, context):
    """Показує трендовий аналіз"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return

        # Отримуємо дані за останні 6 місяців
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        transactions = get_user_transactions(user.id, start_date, end_date)
        
        # Групуємо по місяцях
        monthly_data = {}
        for transaction in transactions:
            month_key = transaction.transaction_date.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {'income': 0, 'expenses': 0}
            
            if transaction.type == TransactionType.INCOME:
                monthly_data[month_key]['income'] += transaction.amount
            else:
                monthly_data[month_key]['expenses'] += transaction.amount
        
        # Сортуємо по датах
        sorted_months = sorted(monthly_data.keys())
        
        # Розраховуємо тренди
        income_trend = []
        expense_trend = []
        for month in sorted_months:
            income_trend.append(monthly_data[month]['income'])
            expense_trend.append(monthly_data[month]['expenses'])
        
        # Аналіз тренду
        trend_analysis = []
        if len(income_trend) >= 3:
            recent_income = sum(income_trend[-3:]) / 3
            older_income = sum(income_trend[:3]) / 3 if len(income_trend) >= 6 else income_trend[0]
            income_change = ((recent_income - older_income) / older_income * 100) if older_income > 0 else 0
            
            if income_change > 10:
                trend_analysis.append("📈 **Доходи зростають** — позитивна динаміка!")
            elif income_change < -10:
                trend_analysis.append("📉 **Доходи знижуються** — варто звернути увагу")
            else:
                trend_analysis.append("➡️ **Доходи стабільні** — помірні коливання")
        
        if len(expense_trend) >= 3:
            recent_expenses = sum(expense_trend[-3:]) / 3
            older_expenses = sum(expense_trend[:3]) / 3 if len(expense_trend) >= 6 else expense_trend[0]
            expense_change = ((recent_expenses - older_expenses) / older_expenses * 100) if older_expenses > 0 else 0
            
            if expense_change > 15:
                trend_analysis.append("⚠️ **Витрати значно зросли** — рекомендуємо аналіз")
            elif expense_change < -10:
                trend_analysis.append("✅ **Витрати знизились** — ви економите!")
            else:
                trend_analysis.append("📊 **Витрати стабільні** — контрольований рівень")
        
        # Формуємо текст
        text = "📈 **Трендовий аналіз (останні 6 місяців)**\n\n"
        
        if sorted_months:
            text += "📊 *Помісячна динаміка:*\n"
            for month in sorted_months[-3:]:  # Показуємо останні 3 місяці
                month_name = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
                income = monthly_data[month]['income']
                expenses = monthly_data[month]['expenses']
                balance = income - expenses
                text += f"• **{month_name}**: {balance:+.2f} грн\n"
                text += f"  Дохід: {income:.2f}, Витрати: {expenses:.2f}\n"
        
        text += "\n🔍 **Аналіз трендів:**\n"
        for trend in trend_analysis:
            text += f"• {trend}\n"
        
        if not trend_analysis:
            text += "📝 Поки недостатньо даних для трендового аналізу\n"
            text += "Продовжуйте додавати транзакції для отримання інсайтів!"
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Детальна статистика", callback_data="detailed_trend_analysis"),
                InlineKeyboardButton("📈 Прогноз на майбутнє", callback_data="financial_forecast")
            ],
            [
                InlineKeyboardButton("📋 Експортувати дані", callback_data="export_trend_data"),
                InlineKeyboardButton("🔄 Оновити аналіз", callback_data="trend_analysis")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="analytics_period_comparison")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_trend_analysis: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при формуванні трендового аналізу",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="analytics_period_comparison")]])
        )

async def show_financial_insights(query, context):
    """Показує фінансові інсайти та паттерни"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return

        # Отримуємо дані за останні 3 місяці
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        transactions = get_user_transactions(user.id, start_date, end_date)
        
        insights = []
        
        # Аналіз по днях тижня
        weekday_spending = {}
        for transaction in transactions:
            if transaction.type == TransactionType.EXPENSE:
                weekday = transaction.transaction_date.strftime("%A")
                weekday_spending[weekday] = weekday_spending.get(weekday, 0) + transaction.amount
        
        if weekday_spending:
            max_day = max(weekday_spending, key=weekday_spending.get)
            min_day = min(weekday_spending, key=weekday_spending.get)
            
            weekdays_uk = {
                "Monday": "понеділок", "Tuesday": "вівторок", "Wednesday": "середа",
                "Thursday": "четвер", "Friday": "п'ятниця", "Saturday": "субота", "Sunday": "неділя"
            }
            
            max_day_uk = weekdays_uk.get(max_day, max_day)
            min_day_uk = weekdays_uk.get(min_day, min_day)
            
            insights.append(f"📅 Найбільше витрачаєте у **{max_day_uk}** ({weekday_spending[max_day]:.2f} грн)")
            insights.append(f"💰 Найменше — у **{min_day_uk}** ({weekday_spending[min_day]:.2f} грн)")
        
        # Аналіз розміру операцій
        expense_amounts = [t.amount for t in transactions if t.type == TransactionType.EXPENSE]
        if expense_amounts:
            avg_expense = sum(expense_amounts) / len(expense_amounts)
            large_expenses = [a for a in expense_amounts if a > avg_expense * 2]
            small_expenses = [a for a in expense_amounts if a < avg_expense * 0.5]
            
            insights.append(f"📊 Середній чек: **{avg_expense:.2f} грн**")
            if large_expenses:
                insights.append(f"💸 Великих покупок (>{avg_expense * 2:.0f} грн): **{len(large_expenses)}**")
            if len(small_expenses) > len(expense_amounts) * 0.6:
                insights.append("☕ Багато дрібних покупок — можливо, варто консолідувати")
        
        # Аналіз регулярності
        monthly_count = len(transactions) / 3  # Середня кількість операцій на місяць
        if monthly_count > 50:
            insights.append("📈 Висока активність — понад 50 операцій на місяць")
        elif monthly_count < 10:
            insights.append("📝 Низька активність — додавайте більше транзакцій для точнішого аналізу")
        
        # Аналіз категорій
        category_counts = {}
        for transaction in transactions:
            if transaction.type == TransactionType.EXPENSE and transaction.category:
                cat_name = transaction.category.name
                category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
        
        if category_counts:
            top_category = max(category_counts, key=category_counts.get)
            top_count = category_counts[top_category]
            insights.append(f"🏆 Найчастіша категорія: **{top_category}** ({top_count} операцій)")
        
        text = "🔍 **Фінансові інсайти та паттерни**\n\n"
        text += "🤖 *AI проаналізував ваші звички:*\n\n"
        
        for insight in insights:
            text += f"• {insight}\n"
        
        if not insights:
            text += "📊 Поки недостатньо даних для аналізу паттернів.\n"
            text += "Додайте більше транзакцій для отримання цікавих інсайтів!"
        
        text += "\n💡 *Рекомендації базуються на аналізі ваших фінансових звичок за останні 3 місяці*"
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Детальний аналіз звичок", callback_data="detailed_habits_analysis"),
                InlineKeyboardButton("🎯 Персональні поради", callback_data="ai_savings_tips")
            ],
            [
                InlineKeyboardButton("📈 Прогноз витрат", callback_data="expense_forecast"),
                InlineKeyboardButton("🔄 Оновити інсайти", callback_data="financial_insights")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="analytics_ai_recommendations")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_financial_insights: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при формуванні інсайтів",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="analytics_ai_recommendations")]])
        )

async def show_spending_heatmap(query, context):
    """Показує теплову карту витрат"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return

        # Отримуємо дані за останній місяць
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        transactions = get_user_transactions(user.id, start_date, end_date)
        
        # Створюємо мапу витрат по днях
        daily_spending = {}
        for transaction in transactions:
            if transaction.type == TransactionType.EXPENSE:
                day_key = transaction.transaction_date.strftime("%Y-%m-%d")
                daily_spending[day_key] = daily_spending.get(day_key, 0) + transaction.amount
        
        # Сортуємо дні
        if daily_spending:
            sorted_days = sorted(daily_spending.keys())
            max_spending = max(daily_spending.values())
            
            text = "🔥 **Теплова карта витрат (останні 30 днів)**\n\n"
            
            # Показуємо останні 14 днів з візуалізацією
            recent_days = sorted_days[-14:] if len(sorted_days) >= 14 else sorted_days
            
            for day in recent_days:
                amount = daily_spending[day]
                date_obj = datetime.strptime(day, "%Y-%m-%d")
                day_name = date_obj.strftime("%d.%m (%a)")
                
                # Створюємо візуальну шкалу
                intensity = amount / max_spending if max_spending > 0 else 0
                if intensity > 0.8:
                    heat_emoji = "🔴🔴🔴"
                elif intensity > 0.6:
                    heat_emoji = "🟠🟠🟡"
                elif intensity > 0.4:
                    heat_emoji = "🟡🟡⚪"
                elif intensity > 0.2:
                    heat_emoji = "🟡⚪⚪"
                else:
                    heat_emoji = "⚪⚪⚪"
                
                text += f"`{day_name}` {heat_emoji} `{amount:.2f} грн`\n"
            
            # Статистика
            avg_daily = sum(daily_spending.values()) / len(daily_spending)
            high_spending_days = len([v for v in daily_spending.values() if v > avg_daily * 1.5])
            text += f"\n📊 **Статистика:**\n"
            text += f"• Середньоденні витрати: `{avg_daily:.2f} грн`\n"
            text += f"• Максимум за день: `{max_spending:.2f} грн`\n"
            text += f"• Днів з високими витратами: `{high_spending_days}`\n"
            
            # Аналіз паттернів
            weekday_analysis = {}
            for day, amount in daily_spending.items():
                weekday = datetime.strptime(day, "%Y-%m-%d").strftime("%A")
                weekday_analysis[weekday] = weekday_analysis.get(weekday, [])
                weekday_analysis[weekday].append(amount)
            
            if weekday_analysis:
                avg_by_weekday = {day: sum(amounts)/len(amounts) for day, amounts in weekday_analysis.items()}
                highest_weekday = max(avg_by_weekday, key=avg_by_weekday.get)
                
                weekdays_uk = {
                    "Monday": "понеділки", "Tuesday": "вівторки", "Wednesday": "середи",
                    "Thursday": "четверги", "Friday": "п'ятниці", "Saturday": "суботи", "Sunday": "неділі"
                }
                
                text += f"\n💡 **Паттерн:** Найбільше витрачаєте у {weekdays_uk.get(highest_weekday, highest_weekday)}"
        else:
            text = "📊 **Теплова карта витрат**\n\n"
            text += "📝 Поки недостатньо даних для створення теплової карти.\n"
            text += "Додайте транзакції за останні дні для візуалізації ваших витрат!"
        
        keyboard = [
            [
                InlineKeyboardButton("📈 Графік за місяць", callback_data="monthly_spending_chart"),
                InlineKeyboardButton("📊 Порівняти з минулим", callback_data="compare_spending_patterns")
            ],
            [
                InlineKeyboardButton("🎯 Аналіз паттернів", callback_data="financial_insights"),
                InlineKeyboardButton("⚙️ Налаштування періоду", callback_data="heatmap_period_settings")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="analytics_detailed_analysis")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_spending_heatmap: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при створенні теплової карти",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="analytics_detailed_analysis")]])
        )

# ==================== ДЕТАЛЬНИЙ АНАЛІЗ МЕНЮ ====================

async def show_detailed_analysis_menu(query, context):
    """Показує меню детального аналізу з новими функціями"""
    try:
        keyboard = [
            [
                InlineKeyboardButton("🤖 AI аналіз по періодах", callback_data="ai_analysis_periods"),
                InlineKeyboardButton("⚖️ Порівняння періодів", callback_data="detailed_period_comparison")
            ],
            [
                InlineKeyboardButton("📈 Трендовий аналіз", callback_data="trend_analysis"),
                InlineKeyboardButton("💡 Фінансові інсайти", callback_data="financial_insights")
            ],
            [
                InlineKeyboardButton("🗓️ Теплова карта витрат", callback_data="spending_heatmap"),
                InlineKeyboardButton("🎯 Кастомне порівняння", callback_data="custom_period_comparison")
            ],
            [
                InlineKeyboardButton("🤖 AI планування бюджету", callback_data="ai_budget_planning"),
                InlineKeyboardButton("💰 Цілі заощаджень", callback_data="savings_goals")
            ],
            [
                InlineKeyboardButton("🔙 Назад до аналітики", callback_data="analytics")
            ]
        ]
        
        text = (
            "🔍 **Детальний аналіз**\n\n"
            "Розширені аналітичні інструменти:\n\n"
            "🤖 *AI аналіз по періодах* — штучний інтелект проаналізує ваші фінанси\n"
            "⚖️ *Порівняння періодів* — детальне порівняння з візуалізацією\n"
            "📈 *Трендовий аналіз* — прогнози та тенденції витрат\n"
            "💡 *Фінансові інсайти* — глибокі висновки про ваші звички\n"
            "🗓️ *Теплова карта* — візуалізація активності витрат\n"
            "🎯 *Кастомне порівняння* — порівняння будь-яких періодів\n\n"
            "💭 *Підказка:* Використовуйте різні інструменти для повного розуміння ваших фінансів"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_detailed_analysis_menu: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні детального аналізу",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="analytics")]])
        )
