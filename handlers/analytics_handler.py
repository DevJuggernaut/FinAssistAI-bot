"""
Модуль аналітики для бота FinAssist.
Включає статистику витрат, AI рекомендації та звіти за період.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
import calendar
import logging
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Налаштування бек-енду для роботи без графічного інтерфейсу
import io
import numpy as np
import io
import matplotlib.pyplot as plt
import numpy as np

from database.db_operations import get_user, get_monthly_stats, get_user_transactions, get_user_categories
from database.models import TransactionType
from services.financial_advisor import get_financial_advice
# Нові імпорти для розширеної аналітики
from services.advanced_analytics import advanced_analytics
from services.trend_analyzer import trend_analyzer
from services.financial_insights import insights_engine

logger = logging.getLogger(__name__)

# ==================== ГОЛОВНЕ МЕНЮ АНАЛІТИКИ ====================

async def show_analytics_main_menu(query, context):
    """Показує головне меню аналітики з інформацією про доступні опції"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Формуємо текст з інформацією про доступні опції
        text = "📊 **Ваша фінансова аналітика**\n\n"
        text += "Отримайте детальну картину своїх фінансів:\n\n"
        
        text += "📈 **Графіки** — візуалізація даних\n"
        text += "Діаграми витрат, доходів та трендів\n\n"
        
        text += "📊 **Статистика** — числа та факти\n"
        text += "Детальні показники за період\n\n"
        
        text += "📄 **PDF Звіт** — готовий документ\n"
        text += "Повний аналіз з рекомендаціями\n\n"
        
        text += "👆 *Оберіть формат аналізу*"
        
        # Меню з 3 кнопками: графіки, статистика та PDF звіт
        keyboard = [
            [
                InlineKeyboardButton("� Графіки", callback_data="analytics_charts"),
                InlineKeyboardButton("� Статистика", callback_data="analytics_detailed")
            ],
            [
                InlineKeyboardButton("📄 PDF Звіт", callback_data="generate_pdf_report")
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
        logger.error(f"Error in show_analytics_main_menu: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні аналітики",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]])
        )

# ==================== СТАТИСТИКА ВИТРАТ ====================

async def show_expense_statistics(query, context):
    """Показує статистику витрат з вибором періоду (тільки тиждень, місяць, квартал)"""
    keyboard = [
        [
            InlineKeyboardButton("📅 Тиждень", callback_data="expense_stats_week"),
            InlineKeyboardButton("📆 Місяць", callback_data="expense_stats_month")
        ],
        [
            InlineKeyboardButton("📊 Квартал", callback_data="expense_stats_quarter")
        ],
        [
            InlineKeyboardButton("◀️ Аналітика", callback_data="analytics")
        ]
    ]
    
    text = (
        "📈 **Статистика витрат**\n\n"
        "Оберіть період для аналізу:\n\n"
        "📅 **Тиждень** — останні 7 днів\n"
        "📆 **Місяць** — поточний календарний місяць\n"
        "📊 **Квартал** — останні 3 місяці\n\n"
        "👆 *Натисніть на потрібний період*"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_period_statistics(query, context, period_type, chart_type=None):
    """Показує статистику за обраний період з опціональними графіками"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Визначаємо період
        now = datetime.now()
        if period_type == "week":
            start_date = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
            period_name = "останні 7 днів"
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
        transactions = get_user_transactions(
            user.id,
            limit=1000,
            start_date=start_date,
            end_date=now
        )
        
        # Розраховуємо статистику
        total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
        total_expenses = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)
        balance = total_income - total_expenses
        
        # Статистика по категоріях
        categories_stats = {}
        for transaction in transactions:
            if transaction.type == TransactionType.EXPENSE and getattr(transaction, 'category_name', None):
                cat_name = transaction.category_name
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
        
        # Додаємо кнопки для графіків і розподілу
        keyboard = [
            [
                InlineKeyboardButton("📊 Стовпчиковий графік", callback_data=f"expense_chart_bar_{period_type}"),
                InlineKeyboardButton("📋 Розподіл по категоріях", callback_data=f"detailed_categories_{period_type}")
            ],
            [
                InlineKeyboardButton("📈 Лінійний графік", callback_data=f"expense_chart_line_{period_type}"),
                InlineKeyboardButton("◀️ Назад", callback_data="analytics")
            ]
        ]
        
        try:
            if hasattr(query, 'message') and getattr(query.message, 'text', None) is None:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
        except Exception as e:
            # Якщо це помилка "Message is not modified" — ігноруємо
            if "Message is not modified" in str(e):
                pass
            elif "There is no text in the message to edit" in str(e):
                # fallback: надіслати нове повідомлення
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                logger.error(f"Error in show_period_statistics: {str(e)}")
                await query.edit_message_text(
                    "❌ Помилка при формуванні статистики",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
                )
        
    except Exception as e:
        logger.error(f"Error in show_period_statistics: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при формуванні статистики",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
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
                InlineKeyboardButton("◀️ Назад", callback_data="analytics")
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
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
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
            InlineKeyboardButton("◀️ Назад", callback_data="analytics")
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
            InlineKeyboardButton("◀️ Назад", callback_data="analytics")
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
            start_date = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
            period_name = "7 днів"
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
                InlineKeyboardButton("◀️ Назад", callback_data=f"expense_stats_{period_type}")
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
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"expense_stats_{period_type}")]])
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
            start_date = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
            period_name = "7 днів"
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
                InlineKeyboardButton("◀️ Назад", callback_data=f"expense_stats_{period_type}")
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
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"expense_stats_{period_type}")]])
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
                InlineKeyboardButton("◀️ Назад", callback_data="analytics_ai_recommendations")
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
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics_ai_recommendations")]])
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
            InlineKeyboardButton("◀️ Назад", callback_data="analytics")
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
            InlineKeyboardButton("◀️ Назад", callback_data="analytics_settings")
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
            InlineKeyboardButton("◀️ Назад", callback_data="analytics_settings")
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
            InlineKeyboardButton("◀️ Назад", callback_data="analytics_settings")
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
            InlineKeyboardButton("◀️ Назад", callback_data="analytics_settings")
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
            start_date = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
            period_name = "7 днів"
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
                InlineKeyboardButton("◀️ Назад", callback_data="analytics_ai_recommendations")
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
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics_ai_recommendations")]])
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
            # Поточний тиждень - останні 7 днів
            current_start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
            current_end = now
            # Попередній тиждень - 7 днів перед поточним
            prev_start = (now - timedelta(days=13)).replace(hour=0, minute=0, second=0, microsecond=0)
            prev_end = (now - timedelta(days=7)).replace(hour=23, minute=59, second=59, microsecond=999999)
            period_name = "7 днів"
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
                InlineKeyboardButton("◀️ Назад", callback_data="analytics_period_comparison")
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
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics_period_comparison")]])
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
            InlineKeyboardButton("◀️ Назад", callback_data="analytics_ai_recommendations")
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
                InlineKeyboardButton("◀️ Назад", callback_data="analytics_ai_recommendations")
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
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics_ai_recommendations")]])
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
            InlineKeyboardButton("◀️ Назад", callback_data="analytics_ai_recommendations")
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

# ==================== НОВІ РОЗШИРЕНІ ФУНКЦІЇ АНАЛІТИКИ ====================

async def show_analytics_visualizations(query, context):
    """Показує меню візуалізацій"""
    try:
        keyboard = [
            [
                InlineKeyboardButton("🔥 Теплова карта витрат", callback_data="viz_spending_heatmap"),
                InlineKeyboardButton("💸 Грошовий потік", callback_data="viz_cash_flow")
            ],
            [
                InlineKeyboardButton("📊 Тренди категорій", callback_data="viz_category_trends"),
                InlineKeyboardButton("📅 Паттерни витрат", callback_data="viz_spending_patterns")
            ],
            [
                InlineKeyboardButton("🍩 Пончикова діаграма", callback_data="viz_expense_donut"),
                InlineKeyboardButton("💰 Бюджет vs Факт", callback_data="viz_budget_vs_actual")
            ],
            [
                InlineKeyboardButton("◀️ До аналітики", callback_data="analytics")
            ]
        ]
        
        text = (
            "📊 **Візуалізації даних**\n\n"
            "🎨 *Вибір красивих та інформативних графіків:*\n\n"
            "🔥 *Теплова карта* — активність витрат по годинах і днях\n"
            "💸 *Грошовий потік* — динаміка доходів і витрат\n"
            "📊 *Тренди категорій* — зміни витрат по категоріях\n"
            "📅 *Паттерни витрат* — аналіз по днях тижня та місяцях\n"
            "🍩 *Пончикова діаграма* — розподіл витрат\n"
            "💰 *Бюджет vs Факт* — порівняння планів і реальності\n\n"
            "💡 *Кожен графік містить детальну інформацію та інсайти!*"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_analytics_visualizations: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні візуалізацій",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
        )

async def show_spending_heatmap(query, context):
    """Показує теплову карту витрат"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Отримуємо транзакції за останні 30 днів
        now = datetime.now()
        start_date = now - timedelta(days=30)
        transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
        
        # Підготовка даних для теплової карти
        transaction_data = [
            {
                'transaction_date': t.transaction_date,
                'amount': t.amount,
                'type': t.type.value
            }
            for t in transactions
        ]
        
        # Створюємо теплову карту
        heatmap_buffer = advanced_analytics.create_spending_heatmap(transaction_data)
        
        # Відправляємо графік
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=heatmap_buffer,
            caption="🔥 **Теплова карта ваших витрат**\n\nПоказує найактивніші години та дні для витрат. Чим темніше колір, тим більше витрат.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ До візуалізацій", callback_data="analytics_visualizations")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error in show_spending_heatmap: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка створення теплової карти",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics_visualizations")]])
        )

async def show_cash_flow_chart(query, context):
    """Показує графік грошового потоку"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Отримуємо транзакції за останні 30 днів
        now = datetime.now()
        start_date = now - timedelta(days=30)
        transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
        
        # Підготовка даних
        transaction_data = [
            {
                'transaction_date': t.transaction_date,
                'amount': t.amount,
                'type': t.type.value
            }
            for t in transactions
        ]
        
        if not transaction_data:
            await query.edit_message_text(
                "📭 Немає транзакцій за останній місяць для створення графіку",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics_charts")]])
            )
            return
        
        # Створюємо графік грошового потоку
        chart_buffer = advanced_analytics.create_cash_flow_chart(transaction_data)
        
        # Відправляємо графік
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=chart_buffer,
            caption="💸 **Аналіз грошового потоку**\n\nВерхня частина: щоденні доходи та витрати\nНижня частина: кумулятивний баланс\n\n📈 Зелена зона = профіцит\n📉 Червона зона = дефіцит",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ До візуалізацій", callback_data="analytics_visualizations")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error in show_cash_flow_chart: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка створення графіку грошового потоку",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics_visualizations")]])
        )

async def show_analytics_trends(query, context):
    """Показує меню трендів та прогнозів"""
    try:
        keyboard = [
            [
                InlineKeyboardButton("📈 Аналіз трендів", callback_data="trends_analysis"),
                InlineKeyboardButton("🔮 Прогноз витрат", callback_data="trends_forecast")
            ],
            [
                InlineKeyboardButton("🔍 Виявлення аномалій", callback_data="trends_anomalies"),
                InlineKeyboardButton("📊 Сезонні паттерни", callback_data="trends_seasonality")
            ],
            [
                InlineKeyboardButton("💡 Інсайти тенденцій", callback_data="trends_insights"),
                InlineKeyboardButton("◀️ До аналітики", callback_data="analytics")
            ]
        ]
        
        text = (
            "🔍 **Тренди та прогнози**\n\n"
            "🧠 *Розумний аналіз ваших фінансових паттернів:*\n\n"
            "📈 *Аналіз трендів* — напрямок зміни витрат і доходів\n"
            "🔮 *Прогноз витрат* — передбачення майбутніх витрат\n"
            "🔍 *Виявлення аномалій* — незвичні транзакції\n"
            "📊 *Сезонні паттерни* — регулярні зміни в поведінці\n"
            "💡 *Інсайти тенденцій* — корисні висновки\n\n"
            "🎯 *Використовуйте для планування та оптимізації фінансів!*"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_analytics_trends: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні трендів",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
        )

async def show_trends_analysis(query, context):
    """Показує детальний аналіз трендів"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Отримуємо транзакції за останні 60 днів для аналізу
        now = datetime.now()
        start_date = now - timedelta(days=60)
        transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
        
        # Підготовка даних
        transaction_data = [
            {
                'transaction_date': t.transaction_date,
                'amount': t.amount,
                'type': t.type.value,
                'category_name': t.category.name if t.category else 'Без категорії'
            }
            for t in transactions
        ]
        
        # Аналізуємо тренди
        trends_result = trend_analyzer.analyze_spending_trends(transaction_data)
        
        if "error" in trends_result:
            await query.edit_message_text(
                f"❌ {trends_result['error']}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics_trends")]])
            )
            return
        
        # Формуємо текст аналізу
        overall_trend = trends_result.get("overall_trend", {})
        text = "📈 **Аналіз трендів витрат**\n\n"
        
        # Загальний тренд
        if overall_trend:
            direction = overall_trend.get("direction", "невизначений")
            strength = overall_trend.get("strength", "невизначена")
            avg_daily = overall_trend.get("avg_daily", 0)
            growth_per_day = overall_trend.get("growth_per_day", 0)
            
            trend_emoji = {
                "зростаючий": "📈",
                "спадний": "📉", 
                "стабільний": "📊"
            }.get(direction, "📊")
            
            text += f"{trend_emoji} *Загальний тренд:* {direction} ({strength})\n"
            text += f"💰 *Середньо щодня:* {avg_daily:.2f} грн\n"
            
            if abs(growth_per_day) > 1:
                text += f"📊 *Зміна щодня:* {growth_per_day:+.2f} грн\n"
        
        # Тренди по категоріях
        category_trends = trends_result.get("category_trends", {})
        if category_trends:
            text += f"\n🏷️ **Тренди по категоріях:**\n"
            for category, data in list(category_trends.items())[:5]:
                trend = data.get("trend", "стабільний")
                change = data.get("change_percent", 0)
                trend_emoji = "📈" if "зростає" in trend else "📉" if "спадає" in trend else "📊"
                text += f"{trend_emoji} *{category}:* {trend}"
                if abs(change) > 5:
                    text += f" ({change:+.1f}%)"
                text += "\n"
        
        # Прогноз
        forecast = trends_result.get("forecast", {})
        if "monthly_forecast" in forecast:
            monthly_forecast = forecast["monthly_forecast"]
            current_trend = forecast.get("current_trend", "стабільний")
            text += f"\n🔮 **Прогноз на місяць:**\n"
            text += f"💸 *Очікувані витрати:* {monthly_forecast:.2f} грн\n"
            text += f"📊 *Поточний тренд:* {current_trend}\n"
            
            confidence = forecast.get("confidence_interval", {})
            if confidence:
                lower = confidence.get("lower", 0)
                upper = confidence.get("upper", 0)
                text += f"📏 *Діапазон:* {lower:.0f} - {upper:.0f} грн\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🔮 Прогноз", callback_data="trends_forecast"),
                InlineKeyboardButton("🔍 Аномалії", callback_data="trends_anomalies")
            ],
            [
                InlineKeyboardButton("📊 Сезонність", callback_data="trends_seasonality"),
                InlineKeyboardButton("◀️ Назад", callback_data="analytics_trends")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_trends_analysis: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка аналізу трендів",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics_trends")]])
        )

async def show_financial_health_score(query, context):
    """Показує оцінку фінансового здоров'я"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Отримуємо транзакції за останній місяць
        now = datetime.now()
        start_date = now - timedelta(days=30)
        transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
        
        # Підготовка даних для аналізу
        total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
        total_expenses = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)
        
        # Щоденні витрати для аналізу стабільності
        daily_expenses = {}
        for t in transactions:
            if t.type == TransactionType.EXPENSE:
                date_key = t.transaction_date.strftime("%Y-%m-%d")
                daily_expenses[date_key] = daily_expenses.get(date_key, 0) + t.amount
        
        # Джерела доходів
        income_sources = []
        for t in transactions:
            if t.type == TransactionType.INCOME and t.category:
                income_sources.append(t.category.name)
        
        user_data = {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "monthly_income": total_income,
            "monthly_expenses": total_expenses,
            "monthly_budget": user.monthly_budget,
            "daily_expenses": list(daily_expenses.values()),
            "income_sources": income_sources
        }
        
        # Генеруємо оцінку здоров'я
        health_score = insights_engine.generate_financial_health_score(user_data)
        
        if "error" in health_score:
            await query.edit_message_text(
                f"❌ {health_score['error']}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
            )
            return
        
        # Формуємо текст результату
        score = health_score.get("overall_score", 0)
        level = health_score.get("health_level", "Невизначений")
        emoji = health_score.get("emoji", "❓")
        
        text = f"{emoji} **Оцінка фінансового здоров'я**\n\n"
        text += f"🎯 *Загальна оцінка:* {score:.1f}/100\n"
        text += f"📊 *Рівень:* {level}\n\n"
        
        # Детальна розбивка
        components = health_score.get("components", {})
        
        if "savings" in components:
            savings = components["savings"]
            text += f"💰 *Заощадження:* {savings.get('score', 0):.0f}/100\n"
            text += f"   {savings.get('description', 'Немає даних')}\n\n"
        
        if "stability" in components:
            stability = components["stability"]
            text += f"📊 *Стабільність:* {stability.get('score', 0):.0f}/100\n"
            text += f"   {stability.get('description', 'Немає даних')}\n\n"
        
        if "budget" in components:
            budget = components["budget"]
            text += f"🎯 *Бюджет:* {budget.get('score', 0):.0f}/100\n"
            text += f"   {budget.get('description', 'Немає даних')}\n\n"
        
        if "income" in components:
            income = components["income"]
            text += f"💼 *Доходи:* {income.get('score', 0):.0f}/100\n"
            text += f"   {income.get('description', 'Немає даних')}\n\n"
        
        # Рекомендації
        recommendations = health_score.get("recommendations", [])
        if recommendations:
            text += "💡 **Рекомендації для покращення:**\n"
            for rec in recommendations[:3]:
                text += f"• {rec}\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🎯 Персональні інсайти", callback_data="analytics_insights"),
                InlineKeyboardButton("🔄 Оновити оцінку", callback_data="analytics_health_score")
            ],
            [
                InlineKeyboardButton("◀️ До аналітики", callback_data="analytics")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_financial_health_score: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка розрахунку фінансового здоров'я",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
        )

async def show_personal_insights(query, context):
    """Показує персональні інсайти"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Отримуємо транзакції за останні 30 днів
        now = datetime.now()
        start_date = now - timedelta(days=30)
        transactions = get_user_transactions(user.id, start_date, now)
        
        # Підготовка даних
        transaction_data = [
            {
                'transaction_date': t.transaction_date,
                'amount': t.amount,
                'type': t.type.value,
                'category_name': t.category.name if t.category else 'Без категорії'
            }
            for t in transactions
        ]
        
        # Генеруємо інсайти
        insights = insights_engine.generate_spending_insights(transaction_data, period_days=30)
        
        if not insights or (len(insights) == 1 and "Немає даних" in insights[0]):
            await query.edit_message_text(
                "📭 Недостатньо даних для генерації персональних інсайтів.\n\nДодайте більше транзакцій для отримання корисних рекомендацій.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
            )
            return
        
        # Формуємо текст з інсайтами
        text = "🎯 **Ваші персональні інсайти**\n\n"
        text += "🔍 *На основі аналізу останніх 30 днів:*\n\n"
        
        for i, insight in enumerate(insights, 1):
            text += f"{i}. {insight}\n\n"
        
        # Додаємо загальну статистику
        total_expenses = sum(t['amount'] for t in transaction_data if t['type'] == 'expense')
        total_income = sum(t['amount'] for t in transaction_data if t['type'] == 'income')
        transaction_count = len([t for t in transaction_data if t['type'] == 'expense'])
        
        text += "📊 **Загальна статистика:**\n"
        text += f"💸 Витрат: {total_expenses:.2f} грн\n"
        text += f"💰 Доходів: {total_income:.2f} грн\n"
        text += f"🔢 Операцій: {transaction_count}\n"
        
        if total_income > 0:
            savings_rate = ((total_income - total_expenses) / total_income) * 100
            text += f"💾 Заощадження: {savings_rate:.1f}%\n"
        
        keyboard = [
            [
                InlineKeyboardButton("💡 Фінансове здоров'я", callback_data="analytics_health_score"),
                InlineKeyboardButton("🔍 Тренди", callback_data="analytics_trends")
            ],
            [
                InlineKeyboardButton("🔄 Оновити інсайти", callback_data="analytics_insights"),
                InlineKeyboardButton("◀️ До аналітики", callback_data="analytics")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_personal_insights: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка генерації персональних інсайтів",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
        )

# ==================== СПРОЩЕНІ ФУНКЦІЇ АНАЛІТИКИ ====================

async def show_analytics_detailed(query, context):
    """Показує корисну статистику з висновками та порадами"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Аналіз за останні 30 днів
        now = datetime.now()
        start_date = now - timedelta(days=30)
        transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
        
        # Базова статистика
        total_expenses = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)
        total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
        balance = total_income - total_expenses
        
        # Аналіз категорій
        category_expenses = {}
        for t in transactions:
            if t.type == TransactionType.EXPENSE and t.category:
                cat_name = t.category.name
                category_expenses[cat_name] = category_expenses.get(cat_name, 0) + t.amount
        
        # Топ категорія
        top_category = max(category_expenses.items(), key=lambda x: x[1]) if category_expenses else ("Немає даних", 0)
        top_category_percent = (top_category[1] / total_expenses * 100) if total_expenses > 0 else 0
        
        # Середні витрати на день
        daily_avg = total_expenses / 30
        
        # Аналіз тенденцій (порівняння з попередніми 30 днями)
        prev_start = start_date - timedelta(days=30)
        prev_end = start_date
        prev_transactions = get_user_transactions(user.id, start_date=prev_start, end_date=prev_end)
        prev_expenses = sum(t.amount for t in prev_transactions if t.type == TransactionType.EXPENSE)
        
        # Розрахунок тренду
        trend = "стабільний"
        trend_emoji = "📊"
        if prev_expenses > 0:
            change_percent = ((total_expenses - prev_expenses) / prev_expenses) * 100
            if change_percent > 10:
                trend = "зростаючий"
                trend_emoji = "📈"
            elif change_percent < -10:
                trend = "спадний"
                trend_emoji = "📉"
        
        # Коефіцієнт заощаджень
        savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0
        
        # Формуємо текст з висновками
        text = "� **Детальна статистика**\n\n"
        
        # Основні показники
        text += "💰 **За останні 30 днів:**\n"
        text += f"💵 Доходи: `{total_income:.2f} грн`\n"
        text += f"💸 Витрати: `{total_expenses:.2f} грн`\n"
        text += f"📊 Баланс: `{balance:.2f} грн`\n"
        text += f"📅 На день: `{daily_avg:.2f} грн`\n\n"
        
        # Аналіз заощаджень
        text += "💎 **Заощадження:**\n"
        if savings_rate >= 20:
            text += f"🎉 Відмінно! `{savings_rate:.1f}%` від доходу\n"
            text += "✅ Ви фінансово стабільні\n\n"
        elif savings_rate >= 10:
            text += f"👍 Добре! `{savings_rate:.1f}%` заощаджень\n"
            text += "💡 Можна покращити до 20%\n\n"
        elif savings_rate >= 0:
            text += f"� Заощадження: `{savings_rate:.1f}%`\n"
            text += "⚠️ Рекомендуємо 10-20%\n\n"
        else:
            text += f"🚨 Перевитрата `{abs(savings_rate):.1f}%`\n"
            text += "💡 Потрібно скоротити витрати\n\n"
        
        # Аналіз витрат
        text += "🎯 **Найбільші витрати:**\n"
        if top_category[1] > 0:
            text += f"🏆 **{top_category[0]}**\n"
            text += f"💰 `{top_category[1]:.2f} грн` ({top_category_percent:.1f}%)\n"
            
            if top_category_percent > 40:
                text += "⚠️ Забагато для однієї категорії\n"
            elif top_category_percent > 25:
                text += "📊 Помірна концентрація\n"
            else:
                text += "✅ Збалансовано\n"
        text += "\n"
        
        # Тренд витрат
        text += f"📈 **Тенденція:** {trend_emoji} {trend}\n"
        if prev_expenses > 0:
            change_amount = total_expenses - prev_expenses
            text += f"Зміна: `{change_amount:+.2f} грн` за місяць\n\n"
        
        # Персональні висновки та поради
        text += "💡 **Рекомендації:**\n"
        
        conclusions = []
        if savings_rate < 0:
            conclusions.append("🚨 Скоротіть витрати негайно")
        elif savings_rate < 10:
            conclusions.append("📈 Збільшіть заощадження")
        
        if top_category_percent > 35:
            conclusions.append(f"🎯 Оптимізуйте '{top_category[0]}'")
        
        if trend == "зростаючий":
            conclusions.append("⚡ Контролюйте зростання витрат")
        elif trend == "спадний":
            conclusions.append("✅ Ви економите - так тримати!")
        
        weekly_budget = daily_avg * 7
        conclusions.append(f"📅 Тижневий бюджет: ~{weekly_budget:.0f} грн")
        
        if not conclusions:
            conclusions.append("📊 Фінанси в нормі")
        
        for conclusion in conclusions[:4]:  # Показуємо максимум 4 рекомендації
            text += f"• {conclusion}\n"
        
        keyboard = [
            [
                InlineKeyboardButton("� Графіки", callback_data="analytics_charts"),
                InlineKeyboardButton("💡 AI Поради", callback_data="analytics_insights_simple")
            ],
            [
                InlineKeyboardButton("◀️ Аналітика", callback_data="analytics")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_analytics_detailed: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні статистики",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
        )

async def show_analytics_charts(query, context):
    """Показує меню з двома основними типами графіків"""
    try:
        text = (
            "📊 **Візуалізація ваших фінансів**\n\n"
            "Оберіть тип діаграми для аналізу:\n\n"
            "🍩 **Кругова діаграма**\n"
            "• Розподіл витрат по категоріях\n"
            "• Наочно показує де найбільше трат\n"
            "• Відсотки та суми для кожної категорії\n\n"
            "📊 **Стовпчастий графік**\n"
            "• Порівняння доходів та витрат\n"
            "• Динаміка змін за період\n"
            "• Детальний аналіз трендів\n\n"
            "� *Після вибору діаграми оберете період для аналізу*"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🍩 Кругова діаграма", callback_data="chart_type_pie"),
                InlineKeyboardButton("📊 Стовпчастий", callback_data="chart_type_bar")
            ],
            [
                InlineKeyboardButton("◀️ Аналітика", callback_data="analytics")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_analytics_charts: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні графіків",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
        )

async def show_analytics_insights_simple(query, context):
    """Показує прості та корисні поради на основі аналізу"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Отримуємо дані за останній місяць
        now = datetime.now()
        start_date = now - timedelta(days=30)
        transactions = get_user_transactions(user.id, start_date, now)
        
        if not transactions:
            await query.edit_message_text(
                "📭 Недостатньо даних для аналізу.\n\nДодайте кілька транзакцій, щоб отримати корисні поради.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
            )
            return
        
        # Основні розрахунки
        total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
        total_expenses = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)
        
        # Аналіз категорій
        category_totals = {}
        for t in transactions:
            if t.type == TransactionType.EXPENSE and t.category:
                cat_name = t.category.name
                category_totals[cat_name] = category_totals.get(cat_name, 0) + t.amount
        
        insights = []
        
        # 1. Аналіз заощаджень
        if total_income > 0:
            savings_rate = ((total_income - total_expenses) / total_income) * 100
            if savings_rate >= 20:
                insights.append("🎉 Відмінно! Ви заощаджуєте понад 20% доходів")
            elif savings_rate >= 10:
                insights.append("👍 Добре! Намагайтесь збільшити заощадження до 20%")
            elif savings_rate >= 0:
                insights.append("💪 Ви тримаєте баланс. Спробуйте заощаджувати хоча б 10%")
            else:
                insights.append("⚠️ Витрати перевищують доходи. Потрібно оптимізувати витрати")
        
        # 2. Аналіз найбільшої категорії
        if category_totals:
            top_category = max(category_totals.items(), key=lambda x: x[1])
            top_percentage = (top_category[1] / total_expenses) * 100
            
            if top_percentage > 40:
                insights.append(f"🎯 Ваша найбільша категорія витрат — {top_category[0]} ({top_percentage:.1f}%). Спробуйте зменшити витрати тут на 10-15%.")
            elif top_percentage > 25:
                insights.append(f"📊 Найбільша категорія: {top_category[0]} ({top_percentage:.1f}%)")
        
        # 3. Аналіз середніх витрат
        avg_daily = total_expenses / 30
        if user.monthly_budget:
            target_daily = user.monthly_budget / 30
            if avg_daily > target_daily:
                insights.append(f"📉 Середні витрати {avg_daily:.0f} грн/день перевищують цільові {target_daily:.0f} грн/день")
            else:
                insights.append(f"✅ Середні витрати {avg_daily:.0f} грн/день в межах бюджету")
        else:
            insights.append(f"📊 Середні витрати: {avg_daily:.0f} грн на день")
        
        # 4. Рекомендація по бюджету
        if not user.monthly_budget:
            recommended_budget = total_expenses * 1.1  # +10% для подушки
            insights.append(f"💡 Рекомендуємо встановити бюджет: {recommended_budget:.0f} грн/місяць")
        
        # Формуємо текст
        text = "💡 **Ваші персональні поради**\n\n"
        text += "🧠 На основі аналізу ваших фінансів:\n\n"
        
        for i, insight in enumerate(insights[:4], 1):
            text += f"{i}. {insight}\n\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🔮 Прогноз", callback_data="analytics_forecast"),
                InlineKeyboardButton("📊 Графіки", callback_data="analytics_charts")
            ],
            [
                InlineKeyboardButton("◀️ До аналітики", callback_data="analytics")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_analytics_insights_simple: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при генерації порад",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
        )

async def show_analytics_forecast(query, context):
    """Показує простий прогноз витрат"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Отримуємо дані за останні 30 днів
        now = datetime.now()
        start_date = now - timedelta(days=30)
        transactions = get_user_transactions(user.id, start_date, now)
        
        expense_transactions = [t for t in transactions if t.type == TransactionType.EXPENSE]
        
        if len(expense_transactions) < 7:
            await query.edit_message_text(
                "📭 Недостатньо даних для прогнозу.\n\nДодайте більше транзакцій (мінімум 7) для отримання прогнозу.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
            )
            return
        
        # Простий прогноз на основі середніх
        total_expenses = sum(t.amount for t in expense_transactions)
        avg_daily = total_expenses / 30
        
        # Прогноз на тиждень та місяць
        weekly_forecast = avg_daily * 7
        monthly_forecast = avg_daily * 30
        
        # Тренд (останні 15 днів vs попередні 15 днів)
        mid_point = len(expense_transactions) // 2
        if mid_point > 3:
            recent_expenses = expense_transactions[mid_point:]
            older_expenses = expense_transactions[:mid_point]
            
            recent_avg = sum(t.amount for t in recent_expenses) / len(recent_expenses) if recent_expenses else 0
            older_avg = sum(t.amount for t in older_expenses) / len(older_expenses) if older_expenses else 0
            
            if recent_avg > older_avg * 1.1:
                trend = "зростаючий"
                trend_emoji = "📈"
            elif recent_avg < older_avg * 0.9:
                trend = "спадний"
                trend_emoji = "📉"
            else:
                trend = "стабільний"
                trend_emoji = "📊"
        else:
            trend = "стабільний"
            trend_emoji = "📊"
        
        text = "🔮 **Прогноз витрат**\n\n"
        text += f"📊 *Поточний тренд:* Витрати {trend}\n\n"
        
        text += "📈 **Прогнози:**\n"
        text += f"📅 На наступний тиждень: `{weekly_forecast:.2f} грн`\n"
        text += f"📆 На наступний місяць: `{monthly_forecast:.2f} грн`\n\n"
        
        text += f"📊 **Деталі:**\n"
        text += f"💸 Середньо на день: `{avg_daily:.2f} грн`\n"
        text += f"📝 Базується на {len(expense_transactions)} операціях\n\n"
        
        # Порівняння з бюджетом
        if user.monthly_budget:
            if monthly_forecast > user.monthly_budget:
                over_budget = monthly_forecast - user.monthly_budget
                text += f"⚠️ Прогноз перевищує бюджет на `{over_budget:.2f} грн`\n"
                text += f"💡 Рекомендуємо зменшити витрати на `{over_budget/30:.2f} грн/день`"
            else:
                under_budget = user.monthly_budget - monthly_forecast
                text += f"✅ Прогноз в межах бюджету\n"
                text += f"💰 Залишиться `{under_budget:.2f} грн` від бюджету"
        else:
            text += f"💡 Встановіть бюджет для порівняння з прогнозом"
        
        keyboard = [
            [
                InlineKeyboardButton("💡 Поради", callback_data="analytics_insights_simple"),
                InlineKeyboardButton("📊 Графіки", callback_data="analytics_charts")
            ],
            [
                InlineKeyboardButton("◀️ До аналітики", callback_data="analytics")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_analytics_forecast: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при створенні прогнозу",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics")]])
        )

async def show_chart_data_type_selection(query, context, chart_type):
    """Показує меню вибору типу даних (витрати/доходи) для графіку"""
    try:
        # Зберігаємо тип графіку в контексті
        context.user_data['selected_chart_type'] = chart_type
        
        chart_name = "🍩 Кругової діаграми" if chart_type == "pie" else "📊 Стовпчастого графіку"
        
        if chart_type == "pie":
            text = (
                f"📊 **Налаштування {chart_name}**\n\n"
                "Що ви хочете проаналізувати?\n\n"
                "💸 **Витрати** — де найбільше трат?\n"
                "• Покаже топ категорій витрат\n"
                "• Відсотки та суми для кожної категорії\n\n"
                "💰 **Доходи** — звідки надходять кошти?\n"
                "• Структура ваших джерел доходу\n"
                "• Розподіл по типах надходжень\n\n"
                "👆 *Оберіть тип аналізу*"
            )
        else:
            text = (
                f"📊 **Налаштування {chart_name}**\n\n"
                "Оберіть тип даних для відображення:\n\n"
                "💸 **Витрати** — розподіл ваших трат по категоріях\n"
                "💰 **Доходи** — розподіл ваших доходів по джерелах\n"
                "📊 **Порівняння** — доходи та витрати разом\n"
            )
        
        keyboard = [
            [
                InlineKeyboardButton("💸 Витрати", callback_data=f"chart_data_expenses_{chart_type}"),
                InlineKeyboardButton("💰 Доходи", callback_data=f"chart_data_income_{chart_type}")
            ]
        ]
        
        if chart_type == "bar":
            keyboard.insert(1, [InlineKeyboardButton("📊 Порівняння", callback_data=f"chart_data_comparison_{chart_type}")])
        
        keyboard.append([InlineKeyboardButton("◀️ До графіків", callback_data="analytics_charts")])
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_chart_data_type_selection: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні меню",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics_charts")]])
        )

async def show_chart_period_selection(query, context, chart_type, data_type):
    """Показує меню вибору періоду для графіку"""
    try:
        # Зберігаємо тип даних в контексті
        context.user_data['selected_data_type'] = data_type
        
        chart_name = "🍩 Кругової діаграми" if chart_type == "pie" else "📊 Стовпчастого графіку"
        data_name = {
            "expenses": "💸 Витрати",
            "income": "💰 Доходи", 
            "comparison": "📊 Порівняння"
        }.get(data_type, "Дані")
        
        if chart_type == "pie":
            text = (
                f"📊 **Період для {chart_name}**\n\n"
                f"Аналіз: {data_name}\n\n"
                "За який період створити діаграму?\n\n"
                "📅 **Місяць** — найповніша картина\n"
                "• Всі категорії за 30 днів\n\n"
                "📆 **Тиждень** — поточні тренди\n"
                "• Актуальні витрати за 7 днів\n\n"
                " *Рекомендуємо 'Місяць' для повного аналізу*"
            )
        else:
            text = (
                f"📊 **{chart_name} - {data_name}**\n\n"
                "Оберіть період для аналізу:\n\n"
                "📅 **Місяць** — останні 30 днів\n"
                "📆 **Тиждень** — останні 7 днів\n\n"
                "Після вибору періоду буде створено графік 📈"
            )
        
        keyboard = [
            [
                InlineKeyboardButton("📅 Місяць", callback_data=f"generate_chart_{chart_type}_{data_type}_month"),
                InlineKeyboardButton("📆 Тиждень", callback_data=f"generate_chart_{chart_type}_{data_type}_week")
            ]
        ]
        
        # Логіка кнопки "Назад" залежить від типу графіку
        if chart_type == "bar":
            # Для стовпчастих графіків — назад до вибору графіків (оскільки ми пропускаємо вибір типу даних)
            keyboard.append([InlineKeyboardButton("◀️ До графіків", callback_data="analytics_charts")])
        else:
            # Для кругових діаграм — назад до вибору типу даних
            keyboard.append([InlineKeyboardButton("◀️ До типу даних", callback_data=f"chart_type_{chart_type}")])
        
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_chart_period_selection: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні меню",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics_charts")]])
        )

async def generate_simple_chart(query, context, chart_type, data_type, period):
    """Генерує простий та зрозумілий графік"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Визначаємо період
        now = datetime.now()
        if period == "week":
            start_date = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
            period_name = "Останні 7 днів"
        else:  # month
            start_date = now - timedelta(days=30)
            period_name = "Останні 30 днів"
        
        # Отримуємо транзакції
        transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
        
        if not transactions:
            await query.edit_message_text(
                f"📊 Немає даних за період: {period_name}\n\n"
                "Додайте транзакції для створення графіків.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Додати транзакцію", callback_data="add_transaction")],
                    [InlineKeyboardButton("◀️ До графіків", callback_data="analytics_charts")]
                ])
            )
            return
        
        # Показуємо повідомлення про створення графіку
        loading_msg = await query.edit_message_text(
            f"📊 Створюю {chart_type} графік...\n"
            f"📅 Період: {period_name}\n"
            f"💾 Обробляю {len(transactions)} транзакцій..."
        )
        
        # Фільтруємо транзакції за типом
        if data_type == "expenses":
            filtered_transactions = [t for t in transactions if t.type == TransactionType.EXPENSE]
            chart_title = f"Витрати - {period_name}"
        elif data_type == "income":
            filtered_transactions = [t for t in transactions if t.type == TransactionType.INCOME]
            chart_title = f"Доходи - {period_name}"
        else:  # comparison
            filtered_transactions = transactions
            chart_title = f"Доходи vs Витрати - {period_name}"
        
        if not filtered_transactions and data_type != "comparison":
            data_name = "витрат" if data_type == "expenses" else "доходів"
            await loading_msg.edit_text(
                f"📊 Немає {data_name} за період: {period_name}\n\n"
                "Спробуйте інший період або додайте транзакції.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ До періодів", callback_data=f"chart_data_{data_type}_{chart_type}")],
                    [InlineKeyboardButton("◀️ До графіків", callback_data="analytics_charts")]
                ])
            )
            return
        
        # Створюємо графік
        try:
            if chart_type == "pie":
                chart_buffer = await create_pie_chart(filtered_transactions, data_type, chart_title)
            else:  # bar
                chart_buffer = await create_bar_chart(transactions, data_type, chart_title, period)
            
            # Створюємо підпис для діаграми
            if chart_type == "pie":
                # Розрахуємо деякі цікаві факти для кругової діаграми
                total_amount = sum(abs(t.amount) for t in filtered_transactions)
                num_categories = len(set(t.category.name if t.category else "Без категорії" for t in filtered_transactions))
                
                if data_type == "expenses":
                    caption_text = (
                        f"🍩 **Аналіз витрат за {period_name.lower()}**\n\n"
                        f"💰 Загальна сума: **{total_amount:,.0f} грн**\n"
                        f"🏷️ Категорій: **{num_categories}**\n"
                        f"📊 Транзакцій: **{len(filtered_transactions)}**\n\n"
                        f"💡 *Найбільші сектори показують основні статті витрат*"
                    )
                else:  # income
                    caption_text = (
                        f"🍩 **Аналіз доходів за {period_name.lower()}**\n\n"
                        f"💰 Загальна сума: **{total_amount:,.0f} грн**\n"
                        f"🏷️ Джерел: **{num_categories}**\n"
                        f"📊 Надходжень: **{len(filtered_transactions)}**\n\n"
                        f"💡 *Діаграма показує структуру ваших доходів*"
                    )
            else:
                caption_text = (
                    f"📊 **{chart_title}**\n\n"
                    f"📈 Графік створено на основі {len(filtered_transactions) if data_type != 'comparison' else len(transactions)} транзакцій"
                )
            
            # Відправляємо графік
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=chart_buffer,
                caption=caption_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 Інший період", callback_data=f"chart_data_{data_type}_{chart_type}")
                    ],
                    [InlineKeyboardButton("◀️ До вибору графіків", callback_data="analytics_charts")]
                ])
            )
            
        except Exception as chart_error:
            logger.error(f"Error creating chart: {str(chart_error)}")
            await loading_msg.edit_text(
                "❌ Помилка при створенні графіку\n\n"
                "Спробуйте ще раз або оберіть інший тип графіку.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ До графіків", callback_data="analytics_charts")]
                ])
            )
        
    except Exception as e:
        logger.error(f"Error in generate_simple_chart: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при створенні графіку",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="analytics_charts")]])
        )

async def create_pie_chart(transactions, data_type, title):
    """Створює сучасну кругову діаграму з покращеним дизайном"""
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import io
    
    # Налаштовуємо українські шрифти - спрощуємо для кращої сумісності
    plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
    
    # Групуємо транзакції по категоріях
    category_totals = {}
    
    for transaction in transactions:
        category_name = transaction.category.name if transaction.category else "Без категорії"
        category_totals[category_name] = category_totals.get(category_name, 0) + abs(transaction.amount)
    
    if not category_totals:
        raise Exception("Немає даних для створення діаграми")
    
    # Сортуємо категорії за сумою
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    
    # Беремо топ-7 категорій, решту об'єднуємо в "Інше"
    if len(sorted_categories) > 7:
        top_categories = sorted_categories[:6]
        other_sum = sum(amount for _, amount in sorted_categories[6:])
        if other_sum > 0:
            top_categories.append(("Інше", other_sum))
        categories, amounts = zip(*top_categories)
    else:
        categories, amounts = zip(*sorted_categories)
    
    # Створюємо фігуру з правильними пропорціями - збільшуємо розмір
    fig, ax = plt.subplots(figsize=(14, 12), facecolor='white')  # Збільшили з (12, 10) до (14, 12)
    
    # Сучасна кольорова палітра
    modern_colors = [
        '#FF6B8A',  # Рожевий
        '#4ECDC4',  # Бірюзовий  
        '#45B7D1',  # Блакитний
        '#96CEB4',  # М'ятний
        '#FECA57',  # Жовтий
        '#A55EEA',  # Фіолетовий
        '#26D0CE',  # Аквамарин
        '#FF9FF3'   # Лавандовий
    ]
    
    # Розрахунок загальної суми
    total_amount = sum(amounts)
    
    # Створюємо кругову діаграму без підписів
    wedges, texts, autotexts = plt.pie(
        amounts, 
        labels=None,  # Не показуємо підписи на діаграмі
        autopct=lambda pct: f'{pct:.1f}%' if pct > 5 else '',  # Показуємо відсотки тільки для великих секторів
        startangle=90,
        colors=modern_colors[:len(categories)],
        wedgeprops=dict(width=0.7, edgecolor='white', linewidth=2),  # Робимо пончикову діаграму
        pctdistance=0.85
    )
    
    # Налаштування відсотків - збільшуємо розмір
    for autotext in autotexts:
        autotext.set_color('#2C3E50')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(24)  # Збільшили з 11 до 16
    
    # Додаємо центральний текст із загальною сумою
    centre_circle = plt.Circle((0,0), 0.4, fc='white', linewidth=2, edgecolor='#E8E8E8')
    ax.add_artist(centre_circle)
    
    # Центральний текст - збільшуємо розміри
    plt.text(0, 0.1, f'{total_amount:,.0f}', ha='center', va='center', 
             fontsize=32, fontweight='bold', color='#2C3E50')  # Збільшили з 16 до 24
    plt.text(0, -0.1, 'грн', ha='center', va='center', 
             fontsize=28, color='#7F8C8D')  # Збільшили з 12 до 18
    
    # Створюємо красиву легенду
    legend_elements = []
    for i, (category, amount) in enumerate(zip(categories, amounts)):
        percentage = (amount / total_amount) * 100
        label = f"{category}: {amount:,.0f} грн ({percentage:.1f}%)"
        legend_elements.append(mpatches.Patch(color=modern_colors[i], label=label))
    
    # Розміщуємо легенду поза діаграмою - збільшуємо розмір тексту
    plt.legend(
        handles=legend_elements,
        loc='center left',
        bbox_to_anchor=(1.1, 0.5),
        fontsize=26,  # Збільшили з 10 до 14
        frameon=False
    )
    
    # Налаштовуємо заголовок - збільшуємо розмір
    plt.title(title, fontsize=32, fontweight='bold', pad=30, color='#2C3E50')  # Збільшили з 16 до 20
    plt.axis('equal')
    
    # Зберігаємо в буфер з покращеними налаштуваннями
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none', pad_inches=0.3)
    buffer.seek(0)
    plt.close()
    
    return buffer

async def create_bar_chart(transactions, data_type, title, period):
    """Створює сучасний стовпчастий графік з покращеним дизайном"""
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import io
    from collections import defaultdict
    
    # Налаштовуємо українські шрифти
    plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
    
    if data_type == "comparison":
        # Групуємо доходи та витрати по періодах
        income_data = defaultdict(float)
        expense_data = defaultdict(float)
        
        for transaction in transactions:
            if period == "week":
                # Для тижня показуємо останні 7 днів з правильними днями тижня
                weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
                weekday_name = weekdays[transaction.transaction_date.weekday()]
                key = f"{weekday_name} ({transaction.transaction_date.strftime('%d.%m')})"
            else:  # month
                # Для місяця показуємо по тижнях
                week_number = (transaction.transaction_date.day - 1) // 7 + 1
                key = f"Тиждень {week_number}"
            
            if transaction.type == TransactionType.INCOME:
                income_data[key] += transaction.amount
            else:
                expense_data[key] += transaction.amount
        
        # Підготовка даних для графіку
        if period == "week":
            # Для тижня створюємо ключі для останніх 7 днів з правильними днями тижня
            from datetime import datetime, timedelta
            now = datetime.now()
            all_keys = []
            
            for i in range(6, -1, -1):  # від 6 днів тому до сьогодні
                date = now - timedelta(days=i)
                weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
                weekday_name = weekdays[date.weekday()]
                key = f"{weekday_name} ({date.strftime('%d.%m')})"
                all_keys.append(key)
        else:  # month
            all_keys = [f"Тиждень {i}" for i in range(1, 5)]
        
        # Фільтруємо тільки ті ключі, де є дані
        filtered_keys = [key for key in all_keys if income_data[key] > 0 or expense_data[key] > 0]
        if not filtered_keys:
            filtered_keys = all_keys  # Показуємо всі, навіть якщо немає даних
        
        incomes = [income_data.get(key, 0) for key in filtered_keys]
        expenses = [expense_data.get(key, 0) for key in filtered_keys]
        
        # Створюємо сучасний графік - збільшуємо розмір
        fig, ax = plt.subplots(figsize=(14, 10), facecolor='white')
        
        x = range(len(filtered_keys))
        width = 0.35
        
        # Сучасні кольори
        income_color = '#4ECDC4'  # Бірюзовий для доходів
        expense_color = '#FF6B8A'  # Рожевий для витрат
        
        # Створюємо стовпці з покращеним дизайном
        bars1 = ax.bar([i - width/2 for i in x], incomes, width, 
                      label='💰 Доходи', color=income_color, 
                      edgecolor='white', linewidth=2, alpha=0.9)
        bars2 = ax.bar([i + width/2 for i in x], expenses, width, 
                      label='💸 Витрати', color=expense_color, 
                      edgecolor='white', linewidth=2, alpha=0.9)
        
        # Додаємо значення на стовпці з великими шрифтами
        for bar, amount in zip(bars1, incomes):
            if amount > 0:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + max(incomes + expenses)*0.01,
                       f'{amount:,.0f}', ha='center', va='bottom', 
                       fontweight='bold', fontsize=16, color='#2C3E50')
        
        for bar, amount in zip(bars2, expenses):
            if amount > 0:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + max(incomes + expenses)*0.01,
                       f'{amount:,.0f}', ha='center', va='bottom', 
                       fontweight='bold', fontsize=16, color='#2C3E50')
        
        # Налаштовуємо осі з великими шрифтами
        ax.set_xlabel('Період', fontsize=24, fontweight='bold', color='#2C3E50')
        ax.set_ylabel('Сума (грн)', fontsize=24, fontweight='bold', color='#2C3E50')
        ax.set_title(title, fontsize=28, fontweight='bold', pad=30, color='#2C3E50')
        
        # Налаштовуємо мітки осей
        ax.set_xticks(x)
        ax.set_xticklabels(filtered_keys, fontsize=20, rotation=0 if len(filtered_keys) <= 4 else 45)
        ax.tick_params(axis='y', labelsize=18)
        
        # Створюємо красиву легенду
        ax.legend(fontsize=22, loc='upper left', frameon=True, 
                 fancybox=True, shadow=True, framealpha=0.9)
        
        # Додаємо сітку
        ax.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=1)
        ax.set_axisbelow(True)
        
        # Встановлюємо межі осей
        max_value = max(max(incomes) if incomes else [0], max(expenses) if expenses else [0])
        if max_value > 0:
            ax.set_ylim(0, max_value * 1.15)
        
    else:
        # Стовпчастий графік по категоріях
        category_totals = {}
        
        for transaction in transactions:
            category_name = transaction.category.name if transaction.category else "Без категорії"
            category_totals[category_name] = category_totals.get(category_name, 0) + abs(transaction.amount)
        
        if not category_totals:
            raise Exception("Немає даних для створення графіку")
        
        # Сортуємо категорії за сумою
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        
        # Беремо топ-8 категорій для кращого відображення
        if len(sorted_categories) > 8:
            top_categories = sorted_categories[:7]
            other_sum = sum(amount for _, amount in sorted_categories[7:])
            if other_sum > 0:
                top_categories.append(("Інше", other_sum))
            sorted_categories = top_categories
        
        categories, amounts = zip(*sorted_categories)
        
        # Створюємо сучасний графік - збільшуємо розмір
        fig, ax = plt.subplots(figsize=(14, 10), facecolor='white')
        
        # Вибираємо колір залежно від типу даних
        if data_type == "expenses":
            colors = ['#FF6B8A', '#FF8A9B', '#FFA8AB', '#FFC7BB', '#FFE5CB']
            main_color = '#FF6B8A'
        else:  # income
            colors = ['#4ECDC4', '#6DD5C7', '#8BDDCA', '#A9E5CE', '#C7EDD1']
            main_color = '#4ECDC4'
        
        # Розширюємо палітру при потребі
        while len(colors) < len(categories):
            colors.extend(colors)
        
        # Створюємо стовпці з градієнтом кольорів
        bars = ax.bar(range(len(categories)), amounts, 
                     color=colors[:len(categories)], 
                     edgecolor='white', linewidth=2, alpha=0.9)
        
        # Додаємо значення на стовпці з великими шрифтами
        for bar, amount in zip(bars, amounts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(amounts)*0.01,
                   f'{amount:,.0f}', ha='center', va='bottom', 
                   fontweight='bold', fontsize=16, color='#2C3E50')
        
        # Налаштовуємо осі з великими шрифтами
        ax.set_xlabel('Категорії', fontsize=24, fontweight='bold', color='#2C3E50')
        ax.set_ylabel('Сума (грн)', fontsize=24, fontweight='bold', color='#2C3E50')
        ax.set_title(title, fontsize=28, fontweight='bold', pad=30, color='#2C3E50')
        
        # Налаштовуємо мітки категорій
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, fontsize=18, rotation=45, ha='right')
        ax.tick_params(axis='y', labelsize=18)
        
        # Додаємо сітку
        ax.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=1)
        ax.set_axisbelow(True)
        
        # Встановлюємо межі осей
        ax.set_ylim(0, max(amounts) * 1.15)
    
    # Покращуємо загальний вигляд
    plt.tight_layout()
    
    # Зберігаємо в буфер з високою якістю
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none', pad_inches=0.3)
    buffer.seek(0)
    plt.close()
    
    return buffer

# ==================== PDF ЗВІТ ====================

async def generate_pdf_report(query, context):
    """Генерує повний PDF звіт з фінансовою аналітикою"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ Користувач не знайдений")
            return
        
        # Показуємо повідомлення про початок генерації
        await query.edit_message_text(
            "📄 **Генерація PDF звіту**\n\n"
            "⏳ Збираємо ваші фінансові дані...\n"
            "📊 Аналізуємо статистику...\n"
            "📈 Створюємо графіки...\n\n"
            "Це може зайняти кілька секунд, будь ласка, зачекайте.",
            parse_mode="Markdown"
        )
        
        # Збираємо дані за останні 30 днів
        now = datetime.now()
        start_date = now - timedelta(days=30)
        transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
        
        # Базова статистика
        total_expenses = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)
        total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
        balance = total_income - total_expenses
        
        # Аналіз категорій
        category_expenses = {}
        for t in transactions:
            if t.type == TransactionType.EXPENSE and t.category:
                cat_name = t.category.name
                category_expenses[cat_name] = category_expenses.get(cat_name, 0) + t.amount
        
        # Створюємо PDF документ
        pdf_buffer = create_pdf_report(user, transactions, {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'balance': balance,
            'category_expenses': category_expenses,
            'period': '30 днів'
        })
        
        # Відправляємо PDF файл
        filename = f"financial_report_{user.username or user.telegram_id}_{now.strftime('%Y%m%d')}.pdf"
        
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=pdf_buffer,
            filename=filename,
            caption="📄 **Ваш персональний фінансовий звіт**\n\n"
                   "📊 Включає повний аналіз ваших фінансів за останні 30 днів\n"
                   "💡 З персональними рекомендаціями та висновками\n\n"
                   "💾 Збережіть цей файл для подальшого використання!",
            parse_mode="Markdown"
        )
        
        # Показуємо меню після відправки - БЕЗ кнопки "Новий звіт"
        keyboard = [
            [
                InlineKeyboardButton("� До аналітики", callback_data="analytics"),
            ],
            [
                InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
            ]
        ]
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="✅ **PDF звіт успішно створено!**\n\n"
                 "📄 Документ містить:\n"
                 "• Повну статистику доходів та витрат\n"
                 "• Графіки розподілу по категоріях\n"
                 "• Аналіз тренду витрат\n"
                 "• Персональні рекомендації\n"
                 "• Коефіцієнт заощаджень\n\n"
                 "💡 Використовуйте цей звіт для планування бюджету!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in generate_pdf_report: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при створенні PDF звіту\n\n"
            "Спробуйте ще раз або зверніться до підтримки.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Спробувати знову", callback_data="generate_pdf_report"),
                InlineKeyboardButton("◀️ Назад", callback_data="analytics")
            ]])
        )

def create_pdf_report(user, transactions, stats):
    """Створює сучасний PDF документ з фінансовим звітом з підтримкою кирилиці"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, mm
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import io
        
        # Створюємо буфер для PDF
        buffer = io.BytesIO()
        
        # Реєструємо шрифт DejaVu для підтримки кирилиці
        try:
            import os
            from reportlab.pdfbase.pdfmetrics import registerFontFamily
            
            # Шлях до наших локальних шрифтів
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            font_dir = os.path.join(base_dir, 'fonts')
            
            regular_font_path = os.path.join(font_dir, 'DejaVuSans.ttf')
            bold_font_path = os.path.join(font_dir, 'DejaVuSans-Bold.ttf')
            
            if os.path.exists(regular_font_path):
                # Реєструємо основний шрифт
                pdfmetrics.registerFont(TTFont('DejaVuSans', regular_font_path))
                
                # Реєструємо жирний варіант, якщо він є
                if os.path.exists(bold_font_path):
                    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', bold_font_path))
                    # Реєструємо сім'ю шрифтів
                    registerFontFamily('DejaVuSans', normal='DejaVuSans', bold='DejaVuSans-Bold')
                
                font_name = 'DejaVuSans'
                logger.info(f"Successfully registered DejaVu Sans font from {regular_font_path}")
            else:
                # Fallback - використовуємо стандартний шрифт
                font_name = 'Helvetica'
                logger.warning(f"DejaVu Sans font not found at {regular_font_path}, using Helvetica")
                
        except Exception as e:
            font_name = 'Helvetica'
            logger.error(f"Error registering font: {str(e)}")
        
        # Створюємо документ з кращими налаштуваннями
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=25*mm,
            bottomMargin=20*mm
        )
        story = []
        
        # Сучасні стилі з підтримкою кирилиці
        styles = getSampleStyleSheet()
        
        # Визначаємо жирний шрифт
        bold_font_name = 'DejaVuSans-Bold' if font_name == 'DejaVuSans' else font_name
        
        # Заголовок
        title_style = ParagraphStyle(
            'ModernTitle',
            parent=styles['Title'],
            fontName=bold_font_name,
            fontSize=28,
            textColor=colors.HexColor('#1e3a8a'),  # Глибокий синій
            alignment=TA_CENTER,
            spaceBefore=10,
            spaceAfter=30,
            leading=36
        )
        
        # Підзаголовки
        section_style = ParagraphStyle(
            'ModernSection',
            parent=styles['Heading2'],
            fontName=bold_font_name,
            fontSize=16,
            textColor=colors.HexColor('#059669'),  # Зелений
            spaceBefore=20,
            spaceAfter=12,
            borderWidth=0,
            borderColor=colors.HexColor('#d1fae5'),
            borderPadding=8,
            backColor=colors.HexColor('#f0fdf4')
        )
        
        # Основний текст
        body_style = ParagraphStyle(
            'ModernBody',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            textColor=colors.HexColor('#374151'),  # Темно-сірий
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            leading=16
        )
        
        # Стиль для важливої інформації
        highlight_style = ParagraphStyle(
            'Highlight',
            parent=body_style,
            backColor=colors.HexColor('#fef3c7'),  # Жовтий фон
            borderWidth=1,
            borderColor=colors.HexColor('#f59e0b'),
            borderPadding=12,
            spaceBefore=12,
            spaceAfter=12,
            leading=16
        )
        
        # ЗАГОЛОВОК ЗВІТУ
        story.append(Paragraph("ПЕРСОНАЛЬНИЙ ФІНАНСОВИЙ ЗВІТ", title_style))
        
        # Інформаційний блок
        current_date = datetime.now()
        info_text = f"""
        <b>Період аналізу:</b> останні {stats['period']}<br/>
        <b>Користувач:</b> {user.username or f'ID: {user.telegram_id}'}<br/>
        <b>Дата створення:</b> {current_date.strftime('%d.%m.%Y о %H:%M')}<br/>
        <b>Валюта:</b> українська гривня (грн)
        """
        story.append(Paragraph(info_text, body_style))
        story.append(Spacer(1, 20))
        
        # ОСНОВНІ ПОКАЗНИКИ
        story.append(Paragraph("ФІНАНСОВИЙ ПІДСУМОК", section_style))
        
        # Розрахунок додаткових метрик
        daily_avg = stats['total_expenses'] / 30
        savings_rate = ((stats['total_income'] - stats['total_expenses']) / stats['total_income'] * 100) if stats['total_income'] > 0 else 0
        
        # Таблиця основних показників з сучасним дизайном
        main_data = [
            ['ПОКАЗНИК', 'СУМА', 'ДЕТАЛІ'],
            ['Загальні доходи', f"{stats['total_income']:,.2f} грн", 'За період'],
            ['Загальні витрати', f"{stats['total_expenses']:,.2f} грн", f"≈ {daily_avg:.0f} грн/день"],
            ['Чистий результат', f"{stats['balance']:+,.2f} грн", f"{'Профіцит' if stats['balance'] >= 0 else 'Дефіцит'}"],
            ['Коефіцієнт заощаджень', f"{savings_rate:.1f}%", f"{'Відмінно' if savings_rate >= 20 else 'Потрібно покращити' if savings_rate < 10 else 'Непогано'}"]
        ]
        
        main_table = Table(main_data, colWidths=[55*mm, 40*mm, 60*mm])
        main_table.setStyle(TableStyle([
            # Заголовок
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), bold_font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Дані
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            
            # Сітка
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#1e40af')),
            # Запобігання розриву таблиці
            ('SPLITLONGWORDS', (0, 0), (-1, -1), True),
        ]))
        
        # Додаємо таблицю з запобіганням розриву
        main_table.hAlign = 'CENTER'
        story.append(KeepTogether([main_table]))
        story.append(Spacer(1, 20))
        
        # АНАЛІЗ ЗАОЩАДЖЕНЬ
        savings_section = []
        savings_section.append(Paragraph("Аналіз ваших заощаджень", section_style))
        
        if savings_rate >= 20:
            savings_analysis = f"""
            <b>Чудові результати!</b><br/>
            Ви заощаджуєте <b>{savings_rate:.1f}%</b> від вашого доходу. Це відмінний показник, який свідчить про високий рівень фінансової дисципліни.<br/><br/>
            <b>Порівняння з рекомендаціями:</b><br/>
            • Мінімальний рівень заощаджень: 10% [ВИКОНАНО]<br/>
            • Оптимальний рівень: 20% [ВИКОНАНО]<br/>
            • Ваш результат: {savings_rate:.1f}% [ВІДМІННО]<br/>
            """
        elif savings_rate >= 10:
            savings_analysis = f"""
            <b>Хороший початок!</b><br/>
            Ви заощаджуєте <b>{savings_rate:.1f}%</b> від доходу. Це хороший результат, але є простір для покращення.<br/><br/>
            <b>Поради для росту:</b><br/>
            • Поточний рівень: {savings_rate:.1f}% [ВИКОНАНО]<br/>
            • Ціль: 20% [ЦІЛЬ]<br/>
            • Потрібно збільшити на: {20-savings_rate:.1f}%<br/>
            """
        elif savings_rate >= 0:
            savings_analysis = f"""
            <b>Потрібна увага</b><br/>
            Заощадження складають лише <b>{savings_rate:.1f}%</b> від доходу. Це нижче рекомендованого рівня.<br/><br/>
            <b>План дій:</b><br/>
            • Поточний рівень: {savings_rate:.1f}% [НИЗЬКИЙ]<br/>
            • Мінімальна ціль: 10% [ЦІЛЬ]<br/>
            • Оптимальна ціль: 20% [ІДЕАЛ]<br/>
            """
        else:
            deficit_amount = abs(stats['balance'])
            savings_analysis = f"""
            <b>КРИТИЧНА СИТУАЦІЯ!</b><br/>
            Витрати перевищують доходи на <b>{deficit_amount:,.2f} грн</b> ({abs(savings_rate):.1f}%).<br/><br/>
            <b>ТЕРМІНОВІ ДІЇ:</b><br/>
            • Негайно переглянути всі витрати<br/>
            • Скоротити необов'язкові витрати<br/>
            • Знайти додаткові джерела доходу<br/>
            """
        
        savings_section.append(Paragraph(savings_analysis, highlight_style))
        story.append(KeepTogether(savings_section))
        story.append(Spacer(1, 15))
        
        # АНАЛІЗ КАТЕГОРІЙ ВИТРАТ
        if stats['category_expenses']:
            story.append(Paragraph("СТРУКТУРА ВАШИХ ВИТРАТ", section_style))
            
            sorted_categories = sorted(stats['category_expenses'].items(), key=lambda x: x[1], reverse=True)
            
            # Таблиця топ-5 категорій
            category_data = [['КАТЕГОРІЯ', 'СУМА', 'ЧАСТКА', 'ОЦІНКА']]
            
            for i, (category, amount) in enumerate(sorted_categories[:5]):
                percentage = (amount / stats['total_expenses'] * 100) if stats['total_expenses'] > 0 else 0
                
                if percentage > 40:
                    evaluation = "Занадто багато"
                elif percentage > 25:
                    evaluation = "Помірно"
                elif percentage > 15:
                    evaluation = "Нормально"
                else:
                    evaluation = "Добре"
                
                category_data.append([
                    f"{i+1}. {category}",
                    f"{amount:,.2f} грн",
                    f"{percentage:.1f}%",
                    evaluation
                ])
            
            category_table = Table(category_data, colWidths=[45*mm, 25*mm, 18*mm, 30*mm])
            category_table.setStyle(TableStyle([
                # Заголовок
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), bold_font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                
                # Дані
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fef2f2')]),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (2, -1), 'RIGHT'),
                ('ALIGN', (3, 1), (3, -1), 'CENTER'),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                
                # Сітка
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#f3f4f6')),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#dc2626')),
                # Запобігання розриву таблиці
                ('SPLITLONGWORDS', (0, 0), (-1, -1), True),
            ]))
            
            # Центруємо таблицю і додаємо з запобіганням розриву
            category_table.hAlign = 'CENTER'
            story.append(KeepTogether([category_table]))
            story.append(Spacer(1, 15))
        
        # ПЕРСОНАЛЬНІ РЕКОМЕНДАЦІЇ
        recommendations_section = []
        recommendations_section.append(Paragraph("ПЕРСОНАЛЬНІ РЕКОМЕНДАЦІЇ", section_style))
        
        recommendations = []
        
        # Аналіз топ категорії
        if stats['category_expenses']:
            top_category = max(stats['category_expenses'].items(), key=lambda x: x[1])
            top_percentage = (top_category[1] / stats['total_expenses'] * 100) if stats['total_expenses'] > 0 else 0
            
            if top_percentage > 40:
                recommendations.append(f"<b>Оптимізація витрат:</b> Категорія '{top_category[0]}' займає {top_percentage:.1f}% бюджету. Спробуйте зменшити витрати тут на 10-15%.")
            elif top_percentage > 25:
                recommendations.append(f"<b>Контроль категорії:</b> '{top_category[0]}' складає {top_percentage:.1f}% витрат - слідкуйте за цією категорією.")
            else:
                recommendations.append("<b>Збалансованість:</b> У вас добрий розподіл витрат по категоріях.")
        
        # Поради по заощадженням
        if savings_rate < 0:
            recommendations.append("<b>Термінова дія:</b> Скоротіть витрати на 20-30% найближчим часом.")
        elif savings_rate < 10:
            recommendations.append("<b>Ціль заощаджень:</b> Спробуйте досягти рівня 10% заощаджень від доходу.")
        elif savings_rate < 20:
            recommendations.append("<b>Покращення:</b> Чудово! Тепер ціль - 20% заощаджень.")
        
        # Планування бюджету
        weekly_budget = daily_avg * 7
        monthly_budget = daily_avg * 30
        recommendations.append(f"<b>Планування:</b> Ваш поточний ритм витрат: {daily_avg:.0f} грн/день, {weekly_budget:.0f} грн/тиждень.")
        
        # Загальні поради
        recommendations.append("<b>Регулярність:</b> Перевіряйте статистику щотижня для кращого контролю.")
        recommendations.append("<b>Цілі:</b> Встановіть конкретні цілі заощаджень на наступний місяць.")
        
        for i, rec in enumerate(recommendations, 1):
            rec_paragraph = Paragraph(f"{i}. {rec}", body_style)
            recommendations_section.append(rec_paragraph)
            recommendations_section.append(Spacer(1, 4))
        
        story.append(KeepTogether(recommendations_section))
        story.append(Spacer(1, 20))
        
        # ПІДВАЛ ДОКУМЕНТУ
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=9,
            textColor=colors.HexColor('#6b7280'),
            alignment=TA_CENTER,
            spaceBefore=20,
            borderWidth=1,
            borderColor=colors.HexColor('#e5e7eb'),
            borderPadding=8,
            backColor=colors.HexColor('#f9fafb')
        )
        
        footer_text = f"""
        <b>FinAssistAI Bot</b> | Розумний фінансовий помічник<br/>
        Звіт створено автоматично • {current_date.strftime('%d.%m.%Y о %H:%M')}<br/>
        Використовуйте функції бота для отримання актуальної інформації
        """
        
        story.append(Paragraph(footer_text, footer_style))
        
        # Створюємо PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
        
    except ImportError as e:
        logger.error(f"ReportLab not available: {str(e)}")
        # Якщо reportlab не встановлений, створюємо покращений текстовий звіт
        return create_simple_text_report(user, transactions, stats)
    except Exception as e:
        logger.error(f"Error creating PDF report: {str(e)}")
        return create_simple_text_report(user, transactions, stats)

def create_simple_text_report(user, transactions, stats):
    """Створює покращений текстовий звіт як fallback"""
    buffer = io.BytesIO()
    
    current_date = datetime.now()
    savings_rate = ((stats['total_income'] - stats['total_expenses']) / stats['total_income'] * 100) if stats['total_income'] > 0 else 0
    daily_avg = stats['total_expenses'] / 30
    
    report_text = f"""
┌─────────────────────────────────────────────────────────────┐
│               ПЕРСОНАЛЬНИЙ ФІНАНСОВИЙ ЗВІТ                  │
└─────────────────────────────────────────────────────────────┘

Користувач: {user.username or f'ID: {user.telegram_id}'}
Період аналізу: останні {stats['period']}
Створено: {current_date.strftime('%d.%m.%Y о %H:%M')}
Валюта: українська гривня (грн)

┌─────────────────────────────────────────────────────────────┐
│                    ФІНАНСОВИЙ ПІДСУМОК                      │
└─────────────────────────────────────────────────────────────┘

Загальні доходи:      {stats['total_income']:>12,.2f} грн
Загальні витрати:     {stats['total_expenses']:>12,.2f} грн
Чистий результат:     {stats['balance']:>+12,.2f} грн
Середньо на день:     {daily_avg:>12,.0f} грн

┌─────────────────────────────────────────────────────────────┐
│                      АНАЛІЗ ЗАОЩАДЖЕНЬ                      │
└─────────────────────────────────────────────────────────────┘

Коефіцієнт заощаджень: {savings_rate:>6.1f}%

"""

    if savings_rate >= 20:
        report_text += "ЧУДОВІ РЕЗУЛЬТАТИ!\n"
        report_text += f"Ви заощаджуєте {savings_rate:.1f}% від доходу - це відмінний показник!\n"
        report_text += "Високий рівень фінансової дисципліни. Так тримати!\n"
    elif savings_rate >= 10:
        report_text += "ХОРОШИЙ ПОЧАТОК!\n"
        report_text += f"Заощадження {savings_rate:.1f}% - це добре, але є простір для росту.\n"
        report_text += f"Ціль: збільшити до 20% (потрібно +{20-savings_rate:.1f}%)\n"
    elif savings_rate >= 0:
        report_text += "ПОТРІБНА УВАГА!\n"
        report_text += f"Заощадження лише {savings_rate:.1f}% - нижче рекомендованого.\n"
        report_text += "Рекомендовано: мінімум 10%, оптимально 20%\n"
    else:
        deficit_amount = abs(stats['balance'])
        report_text += "КРИТИЧНА СИТУАЦІЯ!\n"
        report_text += f"Дефіцит {deficit_amount:,.2f} грн ({abs(savings_rate):.1f}%)\n"
        report_text += "Потрібні термінові дії для балансування бюджету!\n"

    if stats['category_expenses']:
        report_text += f"\n┌─────────────────────────────────────────────────────────────┐\n"
        report_text += f"│                  СТРУКТУРА ВИТРАТ                          │\n"
        report_text += f"└─────────────────────────────────────────────────────────────┘\n\n"
        
        sorted_categories = sorted(stats['category_expenses'].items(), key=lambda x: x[1], reverse=True)
        
        report_text += "┌─────┬─────────────────────────┬────────────┬─────────┬──────────┐\n"
        report_text += "│  №  │       Категорія         │    Сума    │ Частка  │  Оцінка  │\n"
        report_text += "├─────┼─────────────────────────┼────────────┼─────────┼──────────┤\n"
        
        for i, (category, amount) in enumerate(sorted_categories[:5], 1):
            percentage = (amount / stats['total_expenses'] * 100) if stats['total_expenses'] > 0 else 0
            
            if percentage > 40:
                evaluation = " Багато"
            elif percentage > 25:
                evaluation = " Помірно"
            elif percentage > 15:
                evaluation = " Норма"
            else:
                evaluation = " Добре"
            
            # Обрізаємо довгі назви категорій
            display_category = category[:22] + "..." if len(category) > 22 else category
            
            report_text += f"│ {i:>2}. │ {display_category:<23} │ {amount:>8,.0f} │ {percentage:>5.1f}% │{evaluation:<9} │\n"
        
        report_text += "└─────┴─────────────────────────┴────────────┴─────────┴──────────┘\n"
    
    report_text += f"\n┌─────────────────────────────────────────────────────────────┐\n"
    report_text += f"│                ПЕРСОНАЛЬНІ РЕКОМЕНДАЦІЇ                     │\n"
    report_text += f"└─────────────────────────────────────────────────────────────┘\n\n"
    
    recommendations = []
    
    # Аналіз топ категорії
    if stats['category_expenses']:
        top_category = max(stats['category_expenses'].items(), key=lambda x: x[1])
        top_percentage = (top_category[1] / stats['total_expenses'] * 100) if stats['total_expenses'] > 0 else 0
        
        if top_percentage > 40:
            recommendations.append(f"Оптимізація: '{top_category[0]}' займає {top_percentage:.1f}% бюджету")
        elif top_percentage > 25:
            recommendations.append(f"Контроль: '{top_category[0]}' - {top_percentage:.1f}% витрат")
        else:
            recommendations.append("Збалансованість: добрий розподіл по категоріях")
    
    # Поради по заощадженням
    if savings_rate < 0:
        recommendations.append("Термінова дія: скоротити витрати на 20-30%")
    elif savings_rate < 10:
        recommendations.append("Ціль: досягти 10% заощаджень від доходу")
    elif savings_rate < 20:
        recommendations.append("Покращення: наступна ціль - 20% заощаджень")
    
    # Планування
    weekly_budget = daily_avg * 7
    recommendations.append(f"Планування: {daily_avg:.0f} грн/день, {weekly_budget:.0f} грн/тиждень")
    
    # Загальні поради
    recommendations.append("Регулярність: перевіряйте статистику щотижня")
    recommendations.append("Цілі: встановіть конкретні цілі на наступний місяць")
    
    for i, rec in enumerate(recommendations, 1):
        report_text += f"{i}. {rec}\n"
    
    report_text += f"\n┌─────────────────────────────────────────────────────────────┐\n"
    report_text += f"│ FinAssistAI Bot | Розумний фінансовий помічник              │\n"
    report_text += f"│ Звіт створено автоматично • {current_date.strftime('%d.%m.%Y о %H:%M'):>27} │\n"
    report_text += f"└─────────────────────────────────────────────────────────────┘\n"
    
    buffer.write(report_text.encode('utf-8'))
    buffer.seek(0)
    
    return buffer
