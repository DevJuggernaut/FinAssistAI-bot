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
import re

from database.db_operations import get_or_create_user, get_monthly_stats, get_user_categories, get_user, get_user_transactions
from handlers.setup_callbacks import show_currency_selection, complete_setup
from services.financial_advisor import get_financial_advice
from handlers.budget_callbacks import create_budget_from_recommendations, show_budget_total_input
from services.analytics_service import analytics_service
from handlers.transaction_handler import (
    show_add_transaction_menu, show_manual_transaction_type, 
    show_enhanced_expense_form, show_enhanced_income_form,
    show_upload_statement_form, show_upload_pdf_guide, 
    show_upload_excel_guide, show_upload_csv_guide,
    show_receipt_photo_soon, notify_receipt_ready,
    show_transaction_success, show_manual_transaction_form,
    show_add_expense_form, show_add_income_form,
    show_photo_receipt_form, show_all_transactions,
    handle_transactions_pagination, handle_import_all_transactions,
    handle_edit_transactions, handle_cancel_import,
    handle_remove_duplicates, handle_set_import_period,
    handle_back_to_preview, handle_period_selection
)
from handlers.placeholder_handlers import (
    show_help_menu, show_reports_menu, show_charts_menu,
    generate_monthly_report, export_transactions, show_setup_monthly_budget_form,
    show_setup_categories_form, show_budget_menu, show_create_budget_form,
    show_budget_recommendations, show_past_budgets, show_edit_budget_form,
    show_budget_analysis, show_financial_advice_menu,
    show_notification_settings, show_currency_settings, show_language_settings, show_help
)
from handlers.settings_handler import (
    show_settings_menu, show_categories_management, show_add_category_menu,
    show_delete_category_select, confirm_delete_category, delete_category_confirmed,
    show_currency_settings as show_settings_currency, set_currency, show_export_menu,
    export_csv, show_clear_data_menu, confirm_clear_data, clear_data_confirmed,
    handle_add_category_type, show_all_categories
)
from handlers.help_handler import (
    show_help_menu, show_faq_menu, show_faq_add_transaction, show_faq_upload_statement,
    show_faq_change_category, show_faq_export_data, show_faq_clear_data, show_faq_file_formats,
    show_contacts, show_about_bot, show_changelog, show_privacy_policy
)
from handlers.analytics_handler import (
    show_analytics_main_menu, show_expense_statistics, show_period_statistics,
    show_ai_recommendations, show_period_reports, show_period_comparison,
    show_detailed_categories, show_top_transactions, show_analytics_settings,
    show_ai_savings_tips, show_ai_analysis_for_period, show_period_comparison_detail,
    show_category_limits_settings, show_ai_budget_planning, show_savings_goals,
    show_auto_reports_settings, show_report_format_settings, show_goals_reminders_settings,
    show_export_settings, show_custom_period_comparison, show_trend_analysis,
    show_financial_insights, show_spending_heatmap, show_detailed_analysis_menu
)

logger = logging.getLogger(__name__)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє натискання на інлайн-кнопки"""
    query = None
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
            await show_add_transaction_menu(query, context)
        elif callback_data == "add_expense":
            await show_add_expense_form(query, context)
        elif callback_data == "add_income":
            await show_add_income_form(query, context)
        elif callback_data == "show_help":
            await show_help_menu(query, context)
        elif callback_data == "categories":
            await show_categories_management(query, context)
        elif callback_data == "analytics":
            await show_analytics_main_menu(query, context)
        
        # Аналітичні функції - нова система
        elif callback_data == "analytics_expense_stats":
            await show_expense_statistics(query, context)
        elif callback_data == "analytics_ai_recommendations":
            await show_ai_recommendations(query, context)
        elif callback_data == "analytics_period_reports":
            await show_period_reports(query, context)
        elif callback_data == "analytics_period_comparison":
            await show_period_comparison(query, context)
        elif callback_data == "analytics_detailed_analysis":
            await show_detailed_analysis_menu(query, context)
        elif callback_data == "analytics_settings":
            await show_analytics_settings(query, context)
        
        # Статистика витрат за періоди
        elif callback_data.startswith("expense_stats_"):
            period_type = callback_data.replace("expense_stats_", "")
            await show_period_statistics(query, context, period_type)
        elif callback_data.startswith("detailed_categories_"):
            period_type = callback_data.replace("detailed_categories_", "")
            await show_detailed_categories(query, context, period_type)
        elif callback_data.startswith("top_transactions_"):
            period_type = callback_data.replace("top_transactions_", "")
            await show_top_transactions(query, context, period_type)
        
        # AI рекомендації та поради
        elif callback_data == "ai_savings_tips":
            await show_ai_savings_tips(query, context)
        elif callback_data.startswith("ai_analysis_"):
            period_type = callback_data.replace("ai_analysis_", "")
            await show_ai_analysis_for_period(query, context, period_type)
        elif callback_data.startswith("compare_periods_"):
            period_type = callback_data.replace("compare_periods_", "")
            await show_period_comparison_detail(query, context, period_type)
        
        # Додаткові функції аналітики
        elif callback_data == "set_category_limits":
            await show_category_limits_settings(query, context)
        elif callback_data == "ai_budget_planning":
            await show_ai_budget_planning(query, context)
        elif callback_data == "savings_goals":
            await show_savings_goals(query, context)
        elif callback_data == "analytics_auto_reports":
            await show_auto_reports_settings(query, context)
        elif callback_data == "analytics_report_format":
            await show_report_format_settings(query, context)
        elif callback_data == "analytics_goals_reminders":
            await show_goals_reminders_settings(query, context)
        elif callback_data == "analytics_export_settings":
            await show_export_settings(query, context)
        
        # Додаткові аналітичні функції
        elif callback_data == "custom_comparison":
            await show_custom_period_comparison(query, context)
        elif callback_data == "trend_analysis":
            await show_trend_analysis(query, context)
        elif callback_data == "financial_insights":
            await show_financial_insights(query, context)
        elif callback_data == "spending_heatmap":
            await show_spending_heatmap(query, context)
        
        # Нові функції детального аналізу
        elif callback_data == "ai_analysis_periods":
            await show_ai_analysis_for_period(query, context)
        elif callback_data == "detailed_period_comparison":
            await show_period_comparison_detail(query, context)
        elif callback_data == "custom_period_comparison":
            await show_custom_period_comparison(query, context)
        
        # Порівняння стандартних періодів
        elif callback_data == "compare_current_prev_month":
            await show_period_comparison_detail(query, context, "month")
        elif callback_data == "compare_current_prev_week":
            await show_period_comparison_detail(query, context, "week")
        elif callback_data == "compare_30_days":
            await show_period_comparison_detail(query, context, "30days")
        elif callback_data == "compare_quarters":
            await show_period_comparison_detail(query, context, "quarter")
        elif callback_data == "compare_year_to_year":
            await show_period_comparison_detail(query, context, "year")
        
        # Спеціальні функції аналітики
        elif callback_data == "export_trend_data":
            await query.answer("📊 Функція експорту трендових даних буде додана незабаром", show_alert=True)
        elif callback_data == "financial_forecast":
            await query.answer("🔮 Функція фінансового прогнозування розробляється", show_alert=True)
        elif callback_data == "detailed_trend_analysis":
            await show_trend_analysis(query, context)
        elif callback_data == "trend_period_3months":
            await show_trend_analysis(query, context, period="3months")
        elif callback_data == "trend_period_6months":
            await show_trend_analysis(query, context, period="6months")
        elif callback_data == "trend_period_year":
            await show_trend_analysis(query, context, period="year")
        
        # Аналітичні функції - стара система (для зворотної сумісності)
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
        elif callback_data == "setup_monthly_budget":
            await show_setup_monthly_budget_form(query, context)
        elif callback_data == "setup_categories":
            await show_setup_categories_form(query, context)
        
        # Бюджетування і поради
        elif callback_data == "my_budget":
            from handlers.budget_callbacks import show_my_budget_overview
            await show_my_budget_overview(query, context)
        elif callback_data == "my_budget_overview":
            from handlers.budget_callbacks import show_my_budget_overview
            await show_my_budget_overview(query, context)
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
        
        # Нові налаштування MVP
        elif callback_data == "settings_categories":
            await show_categories_management(query, context)
        elif callback_data == "add_category":
            await show_add_category_menu(query, context)
        elif callback_data == "view_all_categories":
            await show_all_categories(query, context)
        elif callback_data == "add_category_expense":
            await handle_add_category_type(query, context, "expense")
        elif callback_data == "add_category_income":
            await handle_add_category_type(query, context, "income")
        elif callback_data == "delete_category_select":
            await show_delete_category_select(query, context)
        elif callback_data == "edit_category_select":
            await query.answer("✏️ Функція редагування категорій буде додана в наступній версії", show_alert=True)
        elif callback_data.startswith("confirm_delete_cat_"):
            category_id = int(callback_data.replace("confirm_delete_cat_", ""))
            await confirm_delete_category(query, context, category_id)
        elif callback_data.startswith("delete_cat_confirmed_"):
            category_id = int(callback_data.replace("delete_cat_confirmed_", ""))
            await delete_category_confirmed(query, context, category_id)
        elif callback_data == "settings_currency":
            await show_settings_currency(query, context)
        elif callback_data.startswith("set_currency_"):
            currency_code = callback_data.replace("set_currency_", "")
            await set_currency(query, context, currency_code)
        elif callback_data == "settings_export":
            await show_export_menu(query, context)
        elif callback_data == "export_csv":
            await export_csv(query, context)
        elif callback_data == "settings_clear_data":
            await show_clear_data_menu(query, context)
        elif callback_data == "confirm_clear_data":
            await confirm_clear_data(query, context)
        elif callback_data == "clear_data_confirmed":
            await clear_data_confirmed(query, context)
        elif callback_data == "no_data":
            await query.answer("ℹ️ Немає даних для обробки", show_alert=True)
        
        # Навігація - усі варіанти головного меню
        elif callback_data == "back_to_main" or callback_data == "main_menu":
            await back_to_main(query, context)
        elif callback_data == "help":
            await show_help_menu(query, context)
        
        # ==================== ДОПОМОГА (HELP) ====================
        
        # Головне меню допомоги
        elif callback_data == "help_menu":
            await show_help_menu(query, context)
        
        # FAQ
        elif callback_data == "help_faq":
            await show_faq_menu(query, context)
        elif callback_data == "faq_add_transaction":
            await show_faq_add_transaction(query, context)
        elif callback_data == "faq_upload_statement":
            await show_faq_upload_statement(query, context)
        elif callback_data == "faq_change_category":
            await show_faq_change_category(query, context)
        elif callback_data == "faq_export_data":
            await show_faq_export_data(query, context)
        elif callback_data == "faq_clear_data":
            await show_faq_clear_data(query, context)
        elif callback_data == "faq_file_formats":
            await show_faq_file_formats(query, context)
        
        # Контакти та інформація
        elif callback_data == "help_contacts":
            await show_contacts(query, context)
        elif callback_data == "help_about":
            await show_about_bot(query, context)
        elif callback_data == "about_changelog":
            await show_changelog(query, context)
        elif callback_data == "about_privacy":
            await show_privacy_policy(query, context)
        
        # ==================== ТРАНЗАКЦІЇ ====================
        
        # Додавання транзакцій - основне меню
        elif callback_data == "add_transaction":
            await show_transaction_menu_enhanced(query, context)
        elif callback_data == "manual_transaction_type":
            await show_manual_type_enhanced(query, context)
        elif callback_data == "upload_statement":
            await show_upload_statement_form(query, context)
        elif callback_data == "receipt_photo_soon":
            await show_receipt_photo_soon(query, context)
        elif callback_data == "notify_receipt_ready":
            await notify_receipt_ready(query, context)
        
        # Ручне додавання транзакцій
        elif callback_data == "manual_expense":
            await show_enhanced_expense_form(query, context)
        elif callback_data == "manual_income":
            await show_enhanced_income_form(query, context)
        
        # Вибір категорій та сум
        elif callback_data.startswith("expense_cat_") or callback_data.startswith("income_cat_"):
            await handle_enhanced_add_transaction(query, context)
        elif callback_data.startswith("quick_amount_"):
            await handle_quick_amount_selection(query, context)
        elif callback_data.startswith("manual_amount_"):
            transaction_type = callback_data.split("_")[2]
            await show_quick_amount_buttons(query, context, transaction_type)
        elif callback_data == "skip_description":
            await handle_enhanced_add_transaction(query, context)
        elif callback_data.startswith("date_"):
            await handle_enhanced_add_transaction(query, context)
        
        # Завантаження файлів
        elif callback_data == "upload_pdf_guide":
            await show_upload_pdf_guide(query, context)
        elif callback_data == "upload_excel_guide":
            await show_upload_excel_guide(query, context)
        elif callback_data == "upload_csv_guide":
            await show_upload_csv_guide(query, context)
        
        # Застарілі обробники (для сумісності)
        elif callback_data.startswith("add_"):
            if callback_data == "add_expense":
                await show_enhanced_expense_form(query, context)
            elif callback_data == "add_income":
                await show_enhanced_income_form(query, context)
        elif callback_data == "manual_transaction":
            await show_manual_type_enhanced(query, context)
        elif callback_data == "photo_receipt":
            await show_receipt_photo_soon(query, context)
        
        # Перегляд транзакцій
        elif callback_data == "view_all_transactions":
            await show_all_transactions(query, context)
        elif callback_data == "prev_transactions_page":
            await handle_transactions_pagination(query, context, direction="prev")
        elif callback_data == "next_transactions_page":
            await handle_transactions_pagination(query, context, direction="next")
        
        # Обробка імпорту транзакцій з виписок
        elif callback_data == "confirm_parsed_transactions":
            await handle_import_all_transactions(query, context)
        elif callback_data == "edit_parsed_transactions":
            await handle_edit_transactions(query, context)
        elif callback_data == "cancel_import":
            await handle_cancel_import(query, context)
        elif callback_data == "remove_duplicates":
            await handle_remove_duplicates(query, context)
        elif callback_data == "set_import_period":
            await handle_set_import_period(query, context)
        elif callback_data == "back_to_preview":
            await handle_back_to_preview(query, context)
        elif callback_data.startswith("period_"):
            await handle_period_selection(query, context)
        elif callback_data == "back_to_preview":
            await handle_back_to_preview(query, context)
        elif callback_data.startswith("period_"):
            await handle_period_selection(query, context)
        
        # Аналіз
        elif callback_data.startswith('analyze_'):
            await handle_analysis_callback(query, user)
        
        # Створення нових категорій
        elif callback_data == "add_expense_category":
            await show_add_expense_category_form(query, context)
        elif callback_data == "add_income_category":
            await show_add_income_category_form(query, context)
        
        # Додаткові функції, які поки що в розробці
        elif callback_data in ["stats_daily", "stats_weekly", "stats_monthly", "income_analysis", 
                              "expense_analysis", "chart_expense_pie", "chart_income_expense", 
                              "chart_expense_trend", "chart_heatmap", "chart_patterns",
                              "add_category", "edit_categories", "delete_category",
                              "notification_settings", "currency_settings", "language_settings",
                              "report_format_settings", "sync_settings", "other_settings",
                              "budget_detailed_view", "budget_settings"]:
            await query.edit_message_text(
                f"🚧 *Функція в розробці*\n\n"
                f"Дана функція знаходиться в активній розробці та буде доступна в наступних оновленнях.\n\n"
                f"Дякуємо за терпіння! 🙏",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]),
                parse_mode="Markdown"
            )
        
        # Неімплементована функція
        else:
            await query.edit_message_text(
                f"🚧 *Функція '{callback_data}' знаходиться в розробці*\n\n"
                f"Дана функція буде доступна в наступних оновленнях бота.\n\n"
                f"Скористайтеся доступними функціями через головне меню.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")]]),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error handling callback: {str(e)}")
        if query:
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

# ==================== TRANSACTION PROCESSING FUNCTIONS ====================

async def handle_expense_category_selection(query, context, category_id):
    """Обробляє вибір категорії для витрати та запитує суму"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("Користувач не знайдений.")
            return
        
        # Отримуємо інформацію про категорію
        from database.session import Session
        from database.models import Category
        
        with Session() as session:
            category = session.query(Category).filter(
                Category.id == category_id,
                Category.user_id == user.id
            ).first()
            
            if not category:
                await query.edit_message_text("Категорія не знайдена.")
                return
            
            # Зберігаємо дані про транзакцію
            context.user_data['transaction_data'] = {
                'type': 'expense',
                'category_id': category_id,
                'category_name': category.name,
                'category_icon': category.icon,
                'step': 'amount'
            }
            
            text = (
                f"💸 *Додавання витрати*\n\n"
                f"📂 **Категорія:** {category.icon} {category.name}\n\n"
                f"💰 **Введіть суму витрати:**\n"
                f"Наприклад: `250` або `250.50`\n\n"
                f"💡 *Підказка:* Введіть тільки число (валюта додасться автоматично)"
            )
            
            keyboard = [
                [InlineKeyboardButton("❌ Скасувати", callback_data="manual_expense")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Error in handle_expense_category_selection: {str(e)}")
        await query.edit_message_text("Виникла помилка. Спробуйте ще раз.")

async def handle_income_category_selection(query, context, category_id):
    """Обробляє вибір категорії для доходу та запитує суму"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("Користувач не знайдений.")
            return
        
        # Отримуємо інформацію про категорію
        from database.session import Session
        from database.models import Category
        
        with Session() as session:
            category = session.query(Category).filter(
                Category.id == category_id,
                Category.user_id == user.id
            ).first()
            
            if not category:
                await query.edit_message_text("Категорія не знайдена.")
                return
            
            # Зберігаємо дані про транзакцію
            context.user_data['transaction_data'] = {
                'type': 'income',
                'category_id': category_id,
                'category_name': category.name,
                'category_icon': category.icon,
                'step': 'amount'
            }
            
            text = (
                f"💰 *Додавання доходу*\n\n"
                f"📂 **Категорія:** {category.icon} {category.name}\n\n"
                f"💰 **Введіть суму доходу:**\n"
                f"Наприклад: `15000` або `15000.50`\n\n"
                f"💡 *Підказка:* Введіть тільки число (валюта додасться автоматично)"
            )
            
            keyboard = [
                [InlineKeyboardButton("❌ Скасувати", callback_data="manual_income")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Error in handle_income_category_selection: {str(e)}")
        await query.edit_message_text("Виникла помилка. Спробуйте ще раз.")

async def save_transaction_to_db(query, context):
    """Зберігає транзакцію в базу даних"""
    try:
        if 'transaction_data' not in context.user_data:
            await query.edit_message_text("Помилка: дані транзакції втрачено.")
            return
        
        transaction_data = context.user_data['transaction_data']
        user = get_user(query.from_user.id)
        
        if not user:
            await query.edit_message_text("Користувач не знайдений.")
            return
        
        # Імпортуємо необхідні моделі
        from database.db_operations import add_transaction
        from database.models import TransactionType
        
        # Визначаємо тип транзакції
        transaction_type = TransactionType.EXPENSE if transaction_data['type'] == 'expense' else TransactionType.INCOME
        
        # Створюємо транзакцію
        new_transaction = add_transaction(
            user_id=user.id,
            amount=transaction_data['amount'],
            description=transaction_data.get('description', ''),
            category_id=transaction_data['category_id'],
            transaction_type=transaction_type,
            source='manual'
        )
        
        # Отримуємо символ валюти користувача
        currency_symbol = user.currency or "₴"
        
        # Формуємо повідомлення про успіх
        type_emoji = "💸" if transaction_data['type'] == 'expense' else "💰"
        type_text = "витрату" if transaction_data['type'] == 'expense' else "дохід"
        sign = "-" if transaction_data['type'] == 'expense' else "+"
        
        success_text = (
            f"✅ *{type_text.capitalize()} успішно додано!*\n\n"
            f"📂 **Категорія:** {transaction_data['category_icon']} {transaction_data['category_name']}\n"
            f"💰 **Сума:** {sign}{transaction_data['amount']:,.2f} {currency_symbol}\n"
        )
        
        if transaction_data.get('description'):
            success_text += f"📝 **Опис:** {transaction_data['description']}\n"
        
        success_text += f"📅 **Дата:** {new_transaction.transaction_date.strftime('%d.%m.%Y %H:%M')}"
        
        keyboard = [
            [
                InlineKeyboardButton(f"➕ Додати ще {type_text}", 
                                   callback_data=f"manual_{'expense' if transaction_data['type'] == 'expense' else 'income'}"),
                InlineKeyboardButton("📊 Статистика", callback_data="stats")
            ],
            [
                InlineKeyboardButton("🏠 Головне меню", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            success_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Очищаємо дані транзакції
        if 'transaction_data' in context.user_data:
            del context.user_data['transaction_data']
            
    except Exception as e:
        logger.error(f"Error saving transaction: {str(e)}")
        await query.edit_message_text(
            f"❌ Помилка при збереженні транзакції: {str(e)}\n\n"
            f"Спробуйте ще раз або зверніться до підтримки.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]])
        )

async def show_add_expense_category_form(query, context):
    """Показує форму для створення нової категорії витрат"""
    text = (
        "➕ *Створення нової категорії витрат*\n\n"
        "📝 **Введіть назву категорії:**\n"
        "Наприклад: `Спортзал`, `Підписки`, `Домашні тварини`\n\n"
        "💡 *Підказка:* Назва повинна бути короткою та зрозумілою"
    )
    
    keyboard = [
        [InlineKeyboardButton("❌ Скасувати", callback_data="manual_expense")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Зберігаємо стан створення категорії
    context.user_data['category_creation'] = {
        'type': 'expense',
        'step': 'name'
    }
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_add_income_category_form(query, context):
    """Показує форму для створення нової категорії доходів"""
    text = (
        "➕ *Створення нової категорії доходів*\n\n"
        "📝 **Введіть назву категорії:**\n"
        "Наприклад: `Підробіток`, `Cashback`, `Дивіденди`\n\n"
        "💡 *Підказка:* Назва повинна бути короткою та зрозумілою"
    )
    
    keyboard = [
        [InlineKeyboardButton("❌ Скасувати", callback_data="manual_income")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Зберігаємо стан створення категорії
    context.user_data['category_creation'] = {
        'type': 'income',
        'step': 'name'
    }
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== TRANSACTION INPUT HANDLERS ====================

async def handle_transaction_amount_input(update, context):
    """Обробляє введення суми для транзакції"""
    try:
        if 'transaction_data' not in context.user_data:
            await update.message.reply_text("Помилка: дані транзакції втрачено.")
            return
        
        transaction_data = context.user_data['transaction_data']
        amount_text = update.message.text.strip()
        
        # Парсимо суму
        try:
            # Видаляємо всі символи крім цифр, крапок і ком
            amount_text = re.sub(r'[^\d.,]', '', amount_text)
            # Замінюємо кому на крапку
            amount_text = amount_text.replace(',', '.')
            
            amount = float(amount_text)
            if amount <= 0:
                await update.message.reply_text(
                    "❌ Сума повинна бути більше нуля. Спробуйте ще раз:"
                )
                return
            
            if amount > 1000000:
                await update.message.reply_text(
                    "❌ Сума занадто велика. Максимальна сума: 1,000,000. Спробуйте ще раз:"
                )
                return
        
        except ValueError:
            await update.message.reply_text(
                "❌ Невірний формат суми. Введіть число (наприклад: 250 або 250.50):"
            )
            return
        
        # Зберігаємо суму
        transaction_data['amount'] = amount
        transaction_data['step'] = 'description'
        
        # Пропонуємо ввести опис або пропустити
        type_text = "витрати" if transaction_data['type'] == 'expense' else "доходу"
        text = (
            f"💰 **Сума {type_text}:** {amount:,.2f} ₴\n\n"
            f"📝 **Введіть опис транзакції** (необов'язково):\n"
            f"Наприклад: `Покупка продуктів у АТБ`\n\n"
            f"Або натисніть кнопку нижче, щоб пропустити опис."
        )
        
        keyboard = [
            [InlineKeyboardButton("⏭️ Пропустити опис", callback_data="skip_description")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error handling transaction amount input: {str(e)}")
        await update.message.reply_text("Виникла помилка. Спробуйте ще раз.")

async def handle_transaction_description_input(update, context):
    """Обробляє введення опису для транзакції"""
    try:
        if 'transaction_data' not in context.user_data:
            await update.message.reply_text("Помилка: дані транзакції втрачено.")
            return
        
        transaction_data = context.user_data['transaction_data']
        description = update.message.text.strip()
        
        if len(description) > 255:
            await update.message.reply_text(
                "❌ Опис занадто довгий. Максимум 255 символів. Спробуйте ще раз:"
            )
            return
        
        # Зберігаємо опис
        transaction_data['description'] = description
        
        # Зберігаємо транзакцію в базу даних
        await save_transaction_from_message(update, context)
        
    except Exception as e:
        logger.error(f"Error handling transaction description input: {str(e)}")
        await update.message.reply_text("Виникла помилка. Спробуйте ще раз.")

async def save_transaction_from_message(update, context):
    """Зберігає транзакцію в базу даних після введення через повідомлення"""
    try:
        if 'transaction_data' not in context.user_data:
            await update.message.reply_text("Помилка: дані транзакції втрачено.")
            return
        
        transaction_data = context.user_data['transaction_data']
        user = get_user(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("Користувач не знайдений.")
            return
        
        # Імпортуємо необхідні моделі
        from database.db_operations import add_transaction
        from database.models import TransactionType
        
        # Визначаємо тип транзакції
        transaction_type = TransactionType.EXPENSE if transaction_data['type'] == 'expense' else TransactionType.INCOME
        
        # Створюємо транзакцію
        new_transaction = add_transaction(
            user_id=user.id,
            amount=transaction_data['amount'],
            description=transaction_data.get('description', ''),
            category_id=transaction_data['category_id'],
            transaction_type=transaction_type,
            source='manual'
        )
        
        # Отримуємо символ валюти користувача
        currency_symbol = user.currency or "₴"
        
        # Формуємо повідомлення про успіх
        type_emoji = "💸" if transaction_data['type'] == 'expense' else "💰"
        type_text = "витрату" if transaction_data['type'] == 'expense' else "дохід"
        sign = "-" if transaction_data['type'] == 'expense' else "+"
        
        success_text = (
            f"✅ *{type_text.capitalize()} успішно додано!*\n\n"
            f"📂 **Категорія:** {transaction_data['category_icon']} {transaction_data['category_name']}\n"
            f"💰 **Сума:** {sign}{transaction_data['amount']:,.2f} {currency_symbol}\n"
        )
        
        if transaction_data.get('description'):
            success_text += f"📝 **Опис:** {transaction_data['description']}\n"
        
        success_text += f"📅 **Дата:** {new_transaction.transaction_date.strftime('%d.%m.%Y %H:%M')}"
        
        keyboard = [
            [
                InlineKeyboardButton(f"➕ Додати ще {type_text}", 
                                   callback_data=f"manual_{'expense' if transaction_data['type'] == 'expense' else 'income'}"),
                InlineKeyboardButton("📊 Статистика", callback_data="stats")
            ],
            [
                InlineKeyboardButton("🏠 Головне меню", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            success_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Очищаємо дані транзакції
        if 'transaction_data' in context.user_data:
            del context.user_data['transaction_data']
            
    except Exception as e:
        logger.error(f"Error saving transaction from message: {str(e)}")
        await update.message.reply_text(
            f"❌ Помилка при збереженні транзакції: {str(e)}\n\n"
            f"Спробуйте ще раз або зверніться до підтримки."
        )

async def back_to_main(query, context):
    """Повертає до головного меню"""
    from handlers.main_menu import show_main_menu
    await show_main_menu(query, context, is_query=True)

# ==================== CATEGORY SELECTION HANDLERS ====================

async def handle_expense_category_selection(query, context, category_id):
    """Обробляє вибір категорії для витрати"""
    try:
        # Отримуємо інформацію про категорію
        from database.db_operations import get_category_by_id
        category = get_category_by_id(category_id)
        
        if not category:
            await query.edit_message_text("❌ Категорію не знайдено.")
            return
        
        # Зберігаємо дані транзакції
        context.user_data['transaction_data'] = {
            'type': 'expense',
            'category_id': category.id,
            'category_name': category.name,
            'category_icon': category.icon or '💸',
            'step': 'amount'
        }
        
        # Просимо ввести суму
        user = get_user(query.from_user.id)
        currency_symbol = user.currency or "₴"
        
        text = (
            f"💸 **Додавання витрати**\n\n"
            f"📂 **Категорія:** {category.icon or '💸'} {category.name}\n\n"
            f"💰 **Введіть суму витрати** (в {currency_symbol}):\n"
            f"Наприклад: `250` або `250.50`\n\n"
            f"💡 **Підказка:** Введіть лише число, символ валюти додається автоматично"
        )
        
        keyboard = [
            [InlineKeyboardButton("❌ Скасувати", callback_data="manual_expense")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_expense_category_selection: {str(e)}")
        await query.edit_message_text("Виникла помилка. Спробуйте ще раз.")

async def handle_income_category_selection(query, context, category_id):
    """Обробляє вибір категорії для доходу"""
    try:
        # Отримуємо інформацію про категорію
        from database.db_operations import get_category_by_id
        category = get_category_by_id(category_id)
        
        if not category:
            await query.edit_message_text("❌ Категорію не знайдено.")
            return
        
        # Зберігаємо дані транзакції
        context.user_data['transaction_data'] = {
            'type': 'income',
            'category_id': category.id,
            'category_name': category.name,
            'category_icon': category.icon or '💰',
            'step': 'amount'
        }
        
        # Просимо ввести суму
        user = get_user(query.from_user.id)
        currency_symbol = user.currency or "₴"
        
        text = (
            f"💰 **Додавання доходу**\n\n"
            f"📂 **Категорія:** {category.icon or '💰'} {category.name}\n\n"
            f"💰 **Введіть суму доходу** (в {currency_symbol}):\n"
            f"Наприклад: `5000` або `5000.50`\n\n"
            f"💡 **Підказка:** Введіть лише число, символ валюти додається автоматично"
        )
        
        keyboard = [
            [InlineKeyboardButton("❌ Скасувати", callback_data="manual_income")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_income_category_selection: {str(e)}")
        await query.edit_message_text("Виникла помилка. Спробуйте ще раз.")

async def handle_skip_description(query, context):
    """Обробляє пропуск введення опису"""
    try:
        if 'transaction_data' not in context.user_data:
            await query.edit_message_text("Помилка: дані транзакції втрачено.")
            return
        
        transaction_data = context.user_data['transaction_data']
        transaction_data['description'] = ''  # Порожній опис
        
        # Зберігаємо транзакцію в базу даних
        await save_transaction_to_db(query, context)
        
    except Exception as e:
        logger.error(f"Error in handle_skip_description: {str(e)}")
        await query.edit_message_text("Виникла помилка. Спробуйте ще раз.")

async def handle_date_selection(query, context):
    """Обробляє вибір дати для транзакції"""
    try:
        date_option = query.data.split("_")[-1]
        
        if 'transaction_data' not in context.user_data:
            await query.edit_message_text("Помилка: дані транзакції втрачено.")
            return
        
        transaction_data = context.user_data['transaction_data']
        
        from datetime import datetime, timedelta
        
        if date_option == "today":
            selected_date = datetime.now()
        elif date_option == "yesterday":
            selected_date = datetime.now() - timedelta(days=1)
        elif date_option == "custom":
            # Тут можна додати логіку для вибору користувацької дати
            selected_date = datetime.now()
        else:
            selected_date = datetime.now()
        
        transaction_data['transaction_date'] = selected_date
        
        # Зберігаємо транзакцію
        await save_transaction_to_db(query, context)
        
    except Exception as e:
        logger.error(f"Error in handle_date_selection: {str(e)}")
        await query.edit_message_text("Виникла помилка. Спробуйте ще раз.")

# ==================== ENHANCED CALLBACK HANDLERS ====================

async def handle_enhanced_add_transaction(query, context):
    """Розширений обробник для додавання транзакцій з покращеним UX"""
    callback_data = query.data
    
    try:
        # Обробка вибору категорій витрат
        if callback_data.startswith("expense_cat_"):
            category_id = int(callback_data.split("_")[-1])
            await handle_expense_category_selection(query, context, category_id)
        
        # Обробка вибору категорій доходів
        elif callback_data.startswith("income_cat_"):
            category_id = int(callback_data.split("_")[-1])
            await handle_income_category_selection(query, context, category_id)
        
        # Обробка пропуску опису
        elif callback_data == "skip_description":
            await handle_skip_description(query, context)
        
        # Обробка вибору дати
        elif callback_data.startswith("date_"):
            await handle_date_selection(query, context)
        
        # Обробка повторного додавання транзакції того ж типу
        elif callback_data.startswith("manual_"):
            transaction_type = callback_data.split("_")[1]
            if transaction_type == "expense":
                await show_enhanced_expense_form(query, context)
            elif transaction_type == "income":
                await show_enhanced_income_form(query, context)
            else:
                await show_manual_transaction_type(query, context)
        
        else:
            logger.warning(f"Unhandled callback_data: {callback_data}")
    
    except Exception as e:
        logger.error(f"Error in handle_enhanced_add_transaction: {str(e)}")
        await query.edit_message_text("Виникла помилка. Спробуйте ще раз.")

# ==================== VALIDATION AND UTILITY FUNCTIONS ====================

def validate_amount(amount_text):
    """Валідує введену суму"""
    try:
        # Видаляємо всі символи крім цифр, крапок і ком
        amount_text = re.sub(r'[^\d.,]', '', amount_text)
        # Замінюємо кому на крапку
        amount_text = amount_text.replace(',', '.')
        
        amount = float(amount_text)
        
        if amount <= 0:
            return None, "❌ Сума повинна бути більше нуля"
        
        if amount > 1000000:
            return None, "❌ Сума занадто велика (максимум: 1,000,000)"
        
        return amount, None
    
    except ValueError:
        return None, "❌ Невірний формат суми. Введіть число (наприклад: 250 або 250.50)"

async def show_quick_amount_buttons(query, context, transaction_type):
    """Показує швидкі кнопки для вибору суми"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            return
        
        currency_symbol = user.currency or "₴"
        
        # Різні суми для витрат та доходів
        if transaction_type == 'expense':
            amounts = [50, 100, 250, 500, 1000, 2000]
            type_name = "витрати"
            emoji = "💸"
        else:
            amounts = [1000, 2500, 5000, 10000, 15000, 20000]
            type_name = "доходу"
            emoji = "💰"
        
        keyboard = []
        
        # Додаємо кнопки швидкого вибору суми
        for i in range(0, len(amounts), 3):
            row = []
            for j in range(i, min(i + 3, len(amounts))):
                amount = amounts[j]
                row.append(InlineKeyboardButton(
                    f"{amount} {currency_symbol}", 
                    callback_data=f"quick_amount_{transaction_type}_{amount}"
                ))
            keyboard.append(row)
        
        # Додаємо кнопки управління
        keyboard.append([
            InlineKeyboardButton("✏️ Ввести вручну", callback_data=f"manual_amount_{transaction_type}"),
            InlineKeyboardButton("❌ Скасувати", callback_data=f"manual_{transaction_type}")
        ])
        
        text = (
            f"{emoji} **Швидкий вибір суми {type_name}**\n\n"
            f"Оберіть одну з популярних сум або введіть власну:\n\n"
            f"💡 **Підказка:** Натисніть на суму або оберіть 'Ввести вручну'"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_quick_amount_buttons: {str(e)}")

async def handle_quick_amount_selection(query, context):
    """Обробляє швидкий вибір суми"""
    try:
        # Розбираємо callback_data: quick_amount_expense_250
        parts = query.data.split("_")
        transaction_type = parts[2]
        amount = float(parts[3])
        
        if 'transaction_data' not in context.user_data:
            await query.edit_message_text("Помилка: дані транзакції втрачено.")
            return
        
        transaction_data = context.user_data['transaction_data']
        transaction_data['amount'] = amount
        transaction_data['step'] = 'description'
        
        # Пропонуємо ввести опис або пропустити
        user = get_user(query.from_user.id)
        currency_symbol = user.currency or "₴"
        type_text = "витрати" if transaction_type == 'expense' else "доходу"
        
        text = (
            f"💰 **Сума {type_text}:** {amount:,.2f} {currency_symbol}\n\n"
            f"📝 **Введіть опис транзакції** (необов'язково):\n"
            f"Наприклад: `Покупка продуктів у АТБ`\n\n"
            f"Або натисніть кнопку нижче, щоб пропустити опис."
        )
        
        keyboard = [
            [InlineKeyboardButton("⏭️ Пропустити опис", callback_data="skip_description")],
            [InlineKeyboardButton("❌ Скасувати", callback_data=f"manual_{transaction_type}")]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_quick_amount_selection: {str(e)}")
        await query.edit_message_text("Виникла помилка. Спробуйте ще раз.")

# ==================== IMPORT FROM TRANSACTION_HANDLER ====================

from handlers.transaction_handler import (
    show_add_transaction_menu as show_transaction_menu_enhanced,
    show_manual_transaction_type as show_manual_type_enhanced,
    show_enhanced_expense_form, show_enhanced_income_form,
    show_upload_statement_form, show_upload_pdf_guide,
    show_upload_excel_guide, show_upload_csv_guide,
    show_receipt_photo_soon, notify_receipt_ready
)
