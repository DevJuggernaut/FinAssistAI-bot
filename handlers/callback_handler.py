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

from database.db_operations import get_or_create_user, get_monthly_stats, get_user_categories, get_user, get_user_transactions, add_transaction
from database.models import TransactionType
from handlers.setup_callbacks import show_currency_selection, complete_setup
from services.financial_advisor import get_financial_advice
from handlers.budget_callbacks import create_budget_from_recommendations, show_budget_total_input
from services.analytics_service import analytics_service
from handlers.main_menu import back_to_main
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
    handle_start_receipt_photo_upload,
    handle_remove_duplicates, handle_set_import_period,
    show_transaction_filters, reset_transactions_filters,
    handle_period_filter, handle_type_filter, handle_category_filter,
    show_privatbank_excel_guide, show_privatbank_statement_form, 
    show_monobank_statement_form, show_monobank_pdf_guide, show_monobank_excel_guide, show_other_bank_statement_form,
    handle_enhanced_add_transaction, handle_quick_amount_selection, show_quick_amount_buttons,
    show_period_filter_menu, show_type_filter_menu,
    handle_edit_single_transaction, handle_edit_amount, handle_edit_description,
    handle_edit_category, handle_set_category, handle_delete_transaction, handle_confirm_delete,
    handle_view_single_transaction
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
    show_ai_savings_tips,
    show_auto_reports_settings, show_report_format_settings, show_goals_reminders_settings,
    show_export_settings,
    # Нові спрощені функції аналітики
    show_analytics_detailed, show_analytics_charts, show_analytics_insights_simple, show_analytics_forecast,
    show_chart_data_type_selection, show_chart_period_selection, generate_simple_chart,
    generate_pdf_report,
    # Розширені функції аналітики
    show_analytics_visualizations, show_spending_heatmap, show_cash_flow_chart,
    show_analytics_trends, show_trends_analysis, show_financial_health_score, show_personal_insights
)
from handlers.ai_assistant_handler import (
    show_ai_assistant_menu, handle_ai_advice, handle_ai_forecast, start_ai_question
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
            # Перенаправляємо стару кнопку "Статистика" на нову "Аналітика"
            await show_analytics_main_menu(query, context)
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
        
        # AI-помічник
        elif callback_data == "ai_assistant_menu":
            await show_ai_assistant_menu(query, context)
        elif callback_data == "ai_advice":
            await handle_ai_advice(query, context)
        elif callback_data == "ai_forecast":
            await handle_ai_forecast(query, context)
        elif callback_data == "ai_custom_question":
            await start_ai_question(update, context)
        elif callback_data == "accounts_menu":
            from handlers.accounts_handler import show_accounts_menu
            await show_accounts_menu(query, context)
        elif callback_data == "accounts_list":
            from handlers.accounts_handler import show_accounts_list
            await show_accounts_list(query, context)
        elif callback_data == "accounts_add":
            from handlers.accounts_handler import show_add_account_form
            await show_add_account_form(query, context)
        elif callback_data == "accounts_transfer":
            from handlers.accounts_handler import show_account_transfer
            await show_account_transfer(query, context)
        elif callback_data == "accounts_stats":
            from handlers.accounts_handler import show_accounts_stats
            await show_accounts_stats(query, context)
        elif callback_data == "accounts_add_cash":
            from handlers.accounts_handler import create_cash_account
            await create_cash_account(query, context)
        elif callback_data == "accounts_add_card":
            from handlers.accounts_handler import create_card_account
            await create_card_account(query, context)
        elif callback_data == "accounts_add_bank":
            from handlers.accounts_handler import create_bank_account
            await create_bank_account(query, context)
        elif callback_data == "accounts_add_savings":
            from handlers.accounts_handler import create_savings_account
            await create_savings_account(query, context)
        elif callback_data == "accounts_add_investment":
            from handlers.accounts_handler import create_investment_account
            await create_investment_account(query, context)
        elif callback_data == "accounts_add_crypto":
            from handlers.accounts_handler import create_crypto_account
            await create_crypto_account(query, context)
        elif callback_data == "accounts_add_other":
            from handlers.accounts_handler import create_other_account
            await create_other_account(query, context)
        elif callback_data == "accounts_use_default_name":
            from handlers.accounts_handler import use_default_account_name
            await use_default_account_name(query, context)
        
        # Аналітичні функції - нова система
        elif callback_data == "analytics_expense_stats":
            await show_expense_statistics(query, context)
        elif callback_data == "analytics_income_stats":
            # Поки що перенаправляємо на загальну аналітику
            await show_analytics_main_menu(query, context)
        elif callback_data == "analytics_ai_recommendations":
            await show_ai_recommendations(query, context)
        
        # Нові спрощені функції аналітики
        elif callback_data == "analytics_detailed":
            await show_analytics_detailed(query, context)
        elif callback_data == "analytics_charts":
            await show_analytics_charts(query, context)
        elif callback_data == "analytics_insights_simple":
            await show_analytics_insights_simple(query, context)
        elif callback_data == "analytics_forecast":
            await show_analytics_forecast(query, context)
        
        # Прості графіки - перенаправляємо на нову систему вибору
        elif callback_data == "chart_categories":
            await show_chart_data_type_selection(query, context, "pie")
        elif callback_data == "chart_timeline":
            await show_chart_data_type_selection(query, context, "bar")
        elif callback_data == "chart_weekdays":
            await show_chart_data_type_selection(query, context, "bar")
        elif callback_data == "chart_income_expense":
            await show_chart_data_type_selection(query, context, "bar")
        
        # Нові графіки з вибором типу та періоду
        elif callback_data == "chart_type_pie":
            await show_chart_data_type_selection(query, context, "pie")
        elif callback_data == "chart_type_bar":
            await show_chart_data_type_selection(query, context, "bar")
        elif callback_data.startswith("chart_data_"):
            # Обробляємо вибір типу даних: chart_data_expenses_pie, chart_data_income_bar тощо
            parts = callback_data.split("_")
            data_type = parts[2]  # expenses, income, comparison
            chart_type = parts[3]  # pie, bar
            await show_chart_period_selection(query, context, chart_type, data_type)
        elif callback_data.startswith("generate_chart_"):
            # Обробляємо генерацію графіку: generate_chart_pie_expenses_month
            parts = callback_data.split("_")
            chart_type = parts[2]  # pie, bar
            data_type = parts[3]   # expenses, income, comparison
            period = parts[4]      # month, week, day
            await generate_simple_chart(query, context, chart_type, data_type, period)
        
        # PDF звіт
        elif callback_data == "generate_pdf_report":
            await generate_pdf_report(query, context)
        
        # Нові розширені функції аналітики
        elif callback_data == "analytics_visualizations":
            await show_analytics_visualizations(query, context)
        elif callback_data == "analytics_trends":
            await show_analytics_trends(query, context)
        elif callback_data == "analytics_health_score":
            await show_financial_health_score(query, context)
        elif callback_data == "analytics_insights":
            await show_personal_insights(query, context)
        
        # Візуалізації
        elif callback_data == "viz_spending_heatmap":
            await show_spending_heatmap(query, context)
        elif callback_data == "viz_cash_flow":
            await show_cash_flow_chart(query, context)
        elif callback_data == "viz_category_trends":
            # Створюємо графік трендів категорій
            user = get_user(query.from_user.id)
            if user:
                from services.advanced_analytics import advanced_analytics
                from datetime import datetime, timedelta
                now = datetime.now()
                start_date = now - timedelta(days=30)
                transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
                
                transaction_data = [
                    {
                        'transaction_date': t.transaction_date,
                        'amount': t.amount,
                        'type': t.type.value,
                        'category_name': t.category.name if t.category else 'Без категорії'
                    }
                    for t in transactions
                ]
                
                chart_buffer = advanced_analytics.create_category_trends_chart(transaction_data)
                
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=chart_buffer,
                    caption="📊 **Тренди витрат по категоріях**\n\nПоказує зміни витрат у топ-5 категоріях протягом часу.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 До візуалізацій", callback_data="analytics_visualizations")
                    ]])
                )
        elif callback_data == "viz_spending_patterns":
            # Створюємо графік паттернів витрат
            user = get_user(query.from_user.id)
            if user:
                from services.advanced_analytics import advanced_analytics
                from datetime import datetime, timedelta
                now = datetime.now()
                start_date = now - timedelta(days=60)
                transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
                
                transaction_data = [
                    {
                        'transaction_date': t.transaction_date,
                        'amount': t.amount,
                        'type': t.type.value
                    }
                    for t in transactions
                ]
                
                chart_buffer = advanced_analytics.create_spending_patterns_chart(transaction_data)
                
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=chart_buffer,
                    caption="📅 **Паттерни витрат**\n\nАналіз витрат по днях тижня та місяцях для виявлення закономірностей.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 До візуалізацій", callback_data="analytics_visualizations")
                    ]])
                )
        elif callback_data == "viz_expense_donut":
            # Створюємо пончикову діаграму
            user = get_user(query.from_user.id)
            if user:
                from services.advanced_analytics import advanced_analytics
                from datetime import datetime, timedelta
                now = datetime.now()
                start_date = now - timedelta(days=30)
                transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
                
                transaction_data = [
                    {
                        'transaction_date': t.transaction_date,
                        'amount': t.amount,
                        'type': t.type.value,
                        'category_name': t.category.name if t.category else 'Без категорії'
                    }
                    for t in transactions
                ]
                
                chart_buffer = advanced_analytics.create_expense_distribution_donut(transaction_data)
                
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=chart_buffer,
                    caption="🍩 **Розподіл витрат**\n\nПончикова діаграма показує частку кожної категорії у загальних витратах.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 До візуалізацій", callback_data="analytics_visualizations")
                    ]])
                )
        elif callback_data == "viz_budget_vs_actual":
            # Створюємо порівняння бюджету з фактом
            user = get_user(query.from_user.id)
            if user:
                from services.advanced_analytics import advanced_analytics
                from datetime import datetime, timedelta
                now = datetime.now()
                start_date = now - timedelta(days=90)  # 3 місяці для порівняння
                transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
                
                transaction_data = [
                    {
                        'transaction_date': t.transaction_date,
                        'amount': t.amount,
                        'type': t.type.value
                    }
                    for t in transactions
                ]
                
                chart_buffer = advanced_analytics.create_budget_vs_actual_chart(
                    transaction_data, 
                    user.monthly_budget
                )
                
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=chart_buffer,
                    caption="💰 **Бюджет vs Фактичні витрати**\n\nПорівняння планованого бюджету з реальними витратами. Зелений = в межах бюджету, червоний = перевищення.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 До візуалізацій", callback_data="analytics_visualizations")
                    ]])
                )
        
        # Тренди та прогнози
        elif callback_data == "trends_analysis":
            await show_trends_analysis(query, context)
        elif callback_data == "trends_forecast":
            # Показуємо прогноз витрат
            user = get_user(query.from_user.id)
            if user:
                from services.trend_analyzer import trend_analyzer
                from datetime import datetime, timedelta
                now = datetime.now()
                start_date = now - timedelta(days=60)
                transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
                
                transaction_data = [
                    {
                        'transaction_date': t.transaction_date,
                        'amount': t.amount,
                        'type': t.type.value,
                        'category_name': t.category.name if t.category else 'Без категорії'
                    }
                    for t in transactions
                ]
                
                trends_result = trend_analyzer.analyze_spending_trends(transaction_data)
                forecast = trends_result.get("forecast", {})
                
                if "error" in forecast:
                    text = f"❌ {forecast['error']}"
                else:
                    text = "🔮 **Прогноз витрат**\n\n"
                    if "monthly_forecast" in forecast:
                        monthly = forecast["monthly_forecast"]
                        weekly = forecast.get("weekly_forecast", 0)
                        daily = forecast.get("daily_forecast", 0)
                        current_trend = forecast.get("current_trend", "стабільний")
                        
                        text += f"📊 *Поточний тренд:* {current_trend}\n\n"
                        text += f"📅 *Прогноз на день:* {daily:.2f} грн\n"
                        text += f"📈 *Прогноз на тиждень:* {weekly:.2f} грн\n"
                        text += f"📆 *Прогноз на місяць:* {monthly:.2f} грн\n\n"
                        
                        confidence = forecast.get("confidence_interval", {})
                        if confidence:
                            lower = confidence.get("lower", 0)
                            upper = confidence.get("upper", 0)
                            text += f"📏 *Довірчий інтервал:*\n"
                            text += f"   Від {lower:.0f} до {upper:.0f} грн\n\n"
                        
                        text += f"🎯 *Базується на {forecast.get('based_on_days', 0)} днях даних*"
                
                await query.edit_message_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📈 Аналіз трендів", callback_data="trends_analysis")],
                        [InlineKeyboardButton("🔙 До трендів", callback_data="analytics_trends")]
                    ]),
                    parse_mode="Markdown"
                )
        elif callback_data == "trends_anomalies":
            # Показуємо аномалії у витратах
            user = get_user(query.from_user.id)
            if user:
                from services.trend_analyzer import trend_analyzer
                from datetime import datetime, timedelta
                now = datetime.now()
                start_date = now - timedelta(days=60)
                transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
                
                transaction_data = [
                    {
                        'transaction_date': t.transaction_date,
                        'amount': t.amount,
                        'type': t.type.value,
                        'category_name': t.category.name if t.category else 'Без категорії'
                    }
                    for t in transactions
                ]
                
                trends_result = trend_analyzer.analyze_spending_trends(transaction_data)
                anomalies = trends_result.get("anomalies", [])
                
                text = "🔍 **Виявлені аномалії у витратах**\n\n"
                
                if not anomalies:
                    text += "✅ Аномалій у витратах не виявлено!\nВаші витрати стабільні та передбачувані."
                else:
                    text += f"⚠️ Знайдено {len(anomalies)} аномальних днів:\n\n"
                    for i, anomaly in enumerate(anomalies[:7], 1):
                        emoji = "📈" if anomaly["type"] == "висока_витрата" else "📉"
                        text += f"{emoji} *{anomaly['date']}*\n"
                        text += f"   {anomaly['description']}\n\n"
                    
                    if len(anomalies) > 7:
                        text += f"...та ще {len(anomalies) - 7} аномалій"
                
                await query.edit_message_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📈 Аналіз трендів", callback_data="trends_analysis")],
                        [InlineKeyboardButton("🔙 До трендів", callback_data="analytics_trends")]
                    ]),
                    parse_mode="Markdown"
                )
        elif callback_data == "trends_seasonality":
            # Показуємо сезонні паттерни
            user = get_user(query.from_user.id)
            if user:
                from services.trend_analyzer import trend_analyzer
                from datetime import datetime, timedelta
                now = datetime.now()
                start_date = now - timedelta(days=60)
                transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
                
                transaction_data = [
                    {
                        'transaction_date': t.transaction_date,
                        'amount': t.amount,
                        'type': t.type.value,
                        'category_name': t.category.name if t.category else 'Без категорії'
                    }
                    for t in transactions
                ]
                
                trends_result = trend_analyzer.analyze_spending_trends(transaction_data)
                seasonality = trends_result.get("seasonality", {})
                
                text = "📊 **Сезонні паттерни витрат**\n\n"
                
                weekday_data = seasonality.get("weekday", {})
                if weekday_data:
                    most_expensive = weekday_data.get("most_expensive_day", "невідомо")
                    cheapest = weekday_data.get("cheapest_day", "невідомо")
                    
                    text += f"📅 *Аналіз по днях тижня:*\n"
                    text += f"💸 Найдорожчий день: {most_expensive}\n"
                    text += f"💰 Найекономніший день: {cheapest}\n\n"
                    
                    weekend_vs_weekday = weekday_data.get("weekend_vs_weekday", {})
                    if weekend_vs_weekday:
                        weekend_avg = weekend_vs_weekday.get("weekend_avg", 0)
                        weekday_avg = weekend_vs_weekday.get("weekday_avg", 0)
                        
                        if weekend_avg > weekday_avg:
                            text += f"🎉 На вихідних витрачаєте більше: {weekend_avg:.2f} грн vs {weekday_avg:.2f} грн\n\n"
                        else:
                            text += f"💼 У робочі дні витрачаєте більше: {weekday_avg:.2f} грн vs {weekend_avg:.2f} грн\n\n"
                
                hourly_data = seasonality.get("hourly", {})
                if hourly_data:
                    peak_hour = hourly_data.get("peak_spending_hour", "невідомо")
                    text += f"⏰ *Аналіз по годинах:*\n"
                    text += f"🕐 Піковий час витрат: {peak_hour}\n"
                    
                    morning_avg = hourly_data.get("morning_avg", 0)
                    evening_avg = hourly_data.get("evening_avg", 0)
                    
                    if morning_avg > 0 and evening_avg > 0:
                        if morning_avg > evening_avg:
                            text += f"🌅 Вранці витрачаєте більше: {morning_avg:.2f} vs {evening_avg:.2f} грн\n"
                        else:
                            text += f"🌆 Ввечері витрачаєте більше: {evening_avg:.2f} vs {morning_avg:.2f} грн\n"
                
                if not weekday_data and not hourly_data:
                    text += "📭 Недостатньо даних для аналізу сезонності.\nДодайте більше транзакцій для детального аналізу."
                
                await query.edit_message_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📈 Аналіз трендів", callback_data="trends_analysis")],
                        [InlineKeyboardButton("🔙 До трендів", callback_data="analytics_trends")]
                    ]),
                    parse_mode="Markdown"
                )
        elif callback_data == "trends_insights":
            # Показуємо інсайти тенденцій
            user = get_user(query.from_user.id)
            if user:
                from services.trend_analyzer import trend_analyzer
                from datetime import datetime, timedelta
                now = datetime.now()
                start_date = now - timedelta(days=60)
                transactions = get_user_transactions(user.id, start_date=start_date, end_date=now)
                
                transaction_data = [
                    {
                        'transaction_date': t.transaction_date,
                        'amount': t.amount,
                        'type': t.type.value,
                        'category_name': t.category.name if t.category else 'Без категорії'
                    }
                    for t in transactions
                ]
                
                insights = trend_analyzer.get_spending_insights(transaction_data)
                
                text = "💡 **Інсайти про тенденції**\n\n"
                text += "🧠 *Ключові висновки з аналізу ваших витрат:*\n\n"
                
                if insights:
                    for i, insight in enumerate(insights, 1):
                        text += f"{i}. {insight}\n\n"
                else:
                    text += "📭 Недостатньо даних для генерації інсайтів.\nДодайте більше транзакцій для отримання корисних висновків."
                
                await query.edit_message_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📈 Аналіз трендів", callback_data="trends_analysis")],
                        [InlineKeyboardButton("🔙 До трендів", callback_data="analytics_trends")]
                    ]),
                    parse_mode="Markdown"
                )
        
        # Статистика витрат за періоди
        elif callback_data.startswith("expense_stats_"):
            period_type = callback_data.replace("expense_stats_", "")
            await show_period_statistics(query, context, period_type)
        elif callback_data.startswith("income_stats_"):
            # Поки що перенаправляємо на загальну аналітику
            await show_analytics_main_menu(query, context)
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
        elif callback_data == "show_expense_pie_chart":
            from handlers.budget_callbacks import show_expense_pie_chart
            await show_expense_pie_chart(query, context)
        elif callback_data == "show_income_pie_chart":
            from handlers.budget_callbacks import show_income_pie_chart
            await show_income_pie_chart(query, context)
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
            await show_add_transaction_menu(query, context)
        elif callback_data == "manual_transaction_type":
            await show_manual_transaction_type(query, context)
        elif callback_data == "upload_statement":
            await show_upload_statement_form(query, context)
        elif callback_data == "receipt_photo_soon":
            await show_receipt_photo_soon(query, context)
        elif callback_data == "start_receipt_photo_upload":
            await handle_start_receipt_photo_upload(query, context)
        elif callback_data == "notify_receipt_ready":
            await notify_receipt_ready(query, context)
        elif callback_data == "confirm_receipt_add":
            await handle_confirm_receipt_add(query, context)
        elif callback_data == "back_to_main_menu":
            await back_to_main(query, context)
        
        # Ручне додавання транзакцій
        elif callback_data == "manual_expense":
            await show_enhanced_expense_form(query, context)
        elif callback_data == "manual_income":
            await show_enhanced_income_form(query, context)
        
        # Обробка автоматичної категоризації
        elif callback_data == "confirm_auto_category":
            from handlers.transaction_handler import handle_confirm_auto_category
            await handle_confirm_auto_category(query, context)
        elif callback_data == "change_category":
            from handlers.transaction_handler import handle_change_category
            await handle_change_category(query, context)
        elif callback_data.startswith("select_manual_category_"):
            from handlers.transaction_handler import handle_manual_category_selection
            await handle_manual_category_selection(query, context)
        elif callback_data == "cancel_transaction":
            from handlers.transaction_handler import handle_cancel_transaction
            await handle_cancel_transaction(query, context)
        
        # Вибір категорій та сум
        elif callback_data.startswith("expense_cat_") or callback_data.startswith("income_cat_"):
            # Зберігаємо вибрану категорію в user_data
            if callback_data.startswith("expense_cat_"):
                context.user_data['transaction_type'] = 'expense'
                context.user_data['category_id'] = callback_data.replace("expense_cat_", "")
            else:
                context.user_data['transaction_type'] = 'income'
                context.user_data['category_id'] = callback_data.replace("income_cat_", "")
            # Одразу просимо ввести суму вручну
            await query.edit_message_text(
                text="Введіть суму для цієї транзакції (наприклад, 150.50):",
                parse_mode="Markdown"
            )
            context.user_data['awaiting_amount'] = True
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
        elif callback_data == "privatbank_excel_guide":
            await show_privatbank_excel_guide(query, context)
        elif callback_data == "upload_csv_guide":
            await show_upload_csv_guide(query, context)
        elif callback_data == "upload_privatbank_excel_guide":
            await show_upload_excel_guide(query, context)
        # Вибір банку для виписки
        elif callback_data == "select_bank_privatbank":
            await show_privatbank_statement_form(query, context)
        elif callback_data == "select_bank_monobank":
            await show_monobank_statement_form(query, context)
        elif callback_data == "select_bank_other":
            await show_other_bank_statement_form(query, context)
        elif callback_data == "privatbank_pdf_guide":
            # PDF больше не поддерживается для ПриватБанка
            await query.answer("❌ PDF файли більше не підтримуються для ПриватБанку. Будь ласка, використовуйте Excel формат.", show_alert=True)
            await show_privatbank_statement_form(query, context)
        elif callback_data == "monobank_csv_guide":
            await show_upload_csv_guide(query, context)
        elif callback_data == "monobank_pdf_guide":
            await show_monobank_pdf_guide(query, context)
        elif callback_data == "start_excel_upload":
            # Визначаємо джерело файлу (якщо не встановлено, використовуємо ПриватБанк за замовчуванням)
            file_source = context.user_data.get('file_source', 'privatbank')
            
            # Set context that we're expecting an Excel file
            context.user_data['awaiting_file'] = 'excel'
            if 'file_source' not in context.user_data:
                context.user_data['file_source'] = 'privatbank'
            
            # Визначаємо текст та кнопку "Назад" залежно від банку
            if file_source == 'monobank':
                bank_text = "Monobank"
                back_callback = "monobank_excel_guide"
                back_text = "🔙 Назад до Monobank Excel"
            else:  # privatbank або інше
                bank_text = "ПриватБанку"
                back_callback = "privatbank_excel_guide"
                back_text = "🔙 Назад до формату файлу"
            
            # Відправляємо повідомлення з інструкціями
            await query.edit_message_text(
                text=f"📤 **Будь ласка, завантажте Excel файл з випискою**\n\n"
                     f"1. Натисніть на скріпку 📎 або іконку вкладення\n"
                     f"2. Оберіть 'File' або 'Document'\n"
                     f"3. Знайдіть та виберіть файл Excel виписки з {bank_text}\n\n"
                     f"⚠️ Важливо: файл має бути у форматі .xlsx або .xls розміром до 10 МБ\n\n"
                     f"Щойно ви відправите файл, я розпочну його обробку.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(back_text, callback_data=back_callback)]
                ])
            )
        elif callback_data == "start_pdf_upload":
            # Set context that we're expecting a PDF file
            context.user_data['awaiting_file'] = 'pdf'
            
            # Визначаємо банк із контексту
            bank_type = context.user_data.get('file_source', 'other')
            bank_name = "ПриватБанку" if bank_type == 'privatbank' else "МоноБанку" if bank_type == 'monobank' else "вашого банку"
            back_callback = f"{bank_type}_pdf_guide" if bank_type in ['privatbank', 'monobank'] else "upload_pdf_guide"
            
            # Відправляємо повідомлення з інструкціями
            await query.edit_message_text(
                text=f"📤 **Будь ласка, завантажте PDF файл з випискою з {bank_name}**\n\n"
                     "1. Натисніть на скріпку 📎 або іконку вкладення\n"
                     "2. Оберіть 'File' або 'Document'\n"
                     "3. Знайдіть та виберіть PDF файл виписки\n\n"
                     "⚠️ Важливо: файл має бути у форматі .pdf розміром до 10 МБ\n\n"
                     "Щойно ви відправите файл, я розпочну його обробку.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data=back_callback)]
                ])
            )
        elif callback_data == "start_csv_upload":
            # Set context that we're expecting a CSV file from MonoBank
            context.user_data['awaiting_file'] = 'csv'
            context.user_data['file_source'] = 'monobank'
            
            # Відправляємо повідомлення з інструкціями
            await query.edit_message_text(
                text="📤 **Будь ласка, завантажте CSV файл з випискою з МоноБанку**\n\n"
                     "1. Натисніть на скріпку 📎 або іконку вкладення\n"
                     "2. Оберіть 'File' або 'Document'\n"
                     "3. Знайдіть та виберіть CSV файл виписки\n\n"
                     "⚠️ Важливо: файл має бути у форматі .csv розміром до 10 МБ\n\n"
                     "Щойно ви відправите файл, я розпочну його обробку.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="monobank_csv_guide")]
                ])
            )
        elif callback_data == "monobank_excel_guide":
            await show_monobank_excel_guide(query, context)
        elif callback_data == "start_monobank_excel_upload":
            # Set context that we're expecting an Excel file from Monobank
            context.user_data['awaiting_file'] = 'excel'
            context.user_data['file_source'] = 'monobank'
            
            # Відправляємо повідомлення з інструкціями
            await query.edit_message_text(
                text="📤 **Будь ласка, завантажте Excel файл з випискою Monobank**\n\n"
                     "1. Натисніть на скріпку 📎 або іконку вкладення\n"
                     "2. Оберіть 'File' або 'Document'\n"
                     "3. Знайдіть та виберіть файл Excel виписки з Monobank\n\n"
                     "📊 **Підтримувані формати**: .xls, .xlsx\n"
                     "⚠️ **Максимальний розмір**: 5 МБ\n\n"
                     "_Очікую на ваш файл..._",
                parse_mode="Markdown"
            )
        
        # Графіки для витрат
        elif callback_data.startswith("expense_chart_"):
            parts = callback_data.split("_")
            chart_type = parts[2]
            period_type = parts[3]
            await generate_expense_chart(query, context, chart_type, period_type)
            
        # Графіки для доходів
        elif callback_data.startswith("income_chart_"):
            parts = callback_data.split("_")
            chart_type = parts[2]
            period_type = parts[3]
            await generate_income_chart(query, context, chart_type, period_type)
        
        # Застарілі обробники (для сумісності)
        elif callback_data.startswith("add_"):
            if callback_data == "add_expense":
                await show_enhanced_expense_form(query, context)
            elif callback_data == "add_income":
                await show_enhanced_income_form(query, context)
        elif callback_data == "manual_transaction":
            await show_manual_transaction_type(query, context)
        elif callback_data == "photo_receipt":
            await show_receipt_photo_soon(query, context)
        
        # Перегляд транзакцій
        elif callback_data == "view_all_transactions":
            # Використовуємо helper функцію для переадресації
            await show_all_transactions(query, context)
        elif callback_data == "import_all_transactions":
            await handle_import_all_transactions(query, context)
        elif callback_data == "prev_transactions_page":
            await handle_transactions_pagination(query, context, direction="prev")
        elif callback_data == "next_transactions_page":
            await handle_transactions_pagination(query, context, direction="next")
        elif callback_data == "transaction_filters":
            await show_transaction_filters(query, context)
        elif callback_data == "reset_transactions_filters":
            await reset_transactions_filters(query, context)
        elif callback_data == "apply_filters":
            # Застосовуємо фільтри та показуємо відфільтровані транзакції
            # Синхронізуємо фільтри з view_params перед показом
            filters = context.user_data.get('transaction_filters', {})
            view_params = context.user_data.get('transactions_view', {})
            
            # Оновлюємо view_params на основі фільтрів
            view_params['period'] = filters.get('period', 'month')
            view_params['type'] = filters.get('type', 'all') if filters.get('type', 'all') != 'all' else None
            view_params['category_id'] = filters.get('category', 'all') if filters.get('category', 'all') != 'all' else None
            view_params['page'] = 1  # Скидаємо на першу сторінку
            
            context.user_data['transactions_view'] = view_params
            
            await query.answer("✅ Показую транзакції з обраними фільтрами")
            await show_all_transactions(query, context)
        elif callback_data == "filter_period":
            await show_period_filter_menu(query, context)
        elif callback_data == "filter_type":
            await show_type_filter_menu(query, context)
        elif callback_data == "filter_category":
            await handle_category_filter(query, context)
        elif callback_data == "back_to_transactions":
            await show_all_transactions(query, context)
        
        # Обробники періодів
        elif callback_data == "period_day":
            if 'transaction_filters' not in context.user_data:
                context.user_data['transaction_filters'] = {}
            context.user_data['transaction_filters']['period'] = 'day'
            if 'transactions_view' not in context.user_data:
                context.user_data['transactions_view'] = {}
            context.user_data['transactions_view']['period'] = 'day'
            context.user_data['transactions_view']['page'] = 1
            await query.answer("✅ Фільтр періоду застосовано")
            await show_transaction_filters(query, context)
        elif callback_data == "period_week":
            if 'transaction_filters' not in context.user_data:
                context.user_data['transaction_filters'] = {}
            context.user_data['transaction_filters']['period'] = 'week'
            if 'transactions_view' not in context.user_data:
                context.user_data['transactions_view'] = {}
            context.user_data['transactions_view']['period'] = 'week'
            context.user_data['transactions_view']['page'] = 1
            await query.answer("✅ Фільтр періоду застосовано")
            await show_transaction_filters(query, context)
        elif callback_data == "period_month":
            if 'transaction_filters' not in context.user_data:
                context.user_data['transaction_filters'] = {}
            context.user_data['transaction_filters']['period'] = 'month'
            if 'transactions_view' not in context.user_data:
                context.user_data['transactions_view'] = {}
            context.user_data['transactions_view']['period'] = 'month'
            context.user_data['transactions_view']['page'] = 1
            await query.answer("✅ Фільтр періоду застосовано")
            await show_transaction_filters(query, context)
        elif callback_data == "period_year":
            if 'transaction_filters' not in context.user_data:
                context.user_data['transaction_filters'] = {}
            context.user_data['transaction_filters']['period'] = 'year'
            if 'transactions_view' not in context.user_data:
                context.user_data['transactions_view'] = {}
            context.user_data['transactions_view']['period'] = 'year'
            context.user_data['transactions_view']['page'] = 1
            await query.answer("✅ Фільтр періоду застосовано")
            await show_transaction_filters(query, context)
        elif callback_data == "period_all":
            if 'transaction_filters' not in context.user_data:
                context.user_data['transaction_filters'] = {}
            context.user_data['transaction_filters']['period'] = 'all'
            if 'transactions_view' not in context.user_data:
                context.user_data['transactions_view'] = {}
            context.user_data['transactions_view']['period'] = 'all'
            context.user_data['transactions_view']['page'] = 1
            await query.answer("✅ Фільтр періоду застосовано")
            await show_transaction_filters(query, context)
        
        # Обробники типів
        elif callback_data == "type_all":
            if 'transaction_filters' not in context.user_data:
                context.user_data['transaction_filters'] = {}
            context.user_data['transaction_filters']['type'] = 'all'
            if 'transactions_view' not in context.user_data:
                context.user_data['transactions_view'] = {}
            context.user_data['transactions_view']['type'] = None
            context.user_data['transactions_view']['page'] = 1
            await query.answer("✅ Фільтр типу застосовано")
            await show_transaction_filters(query, context)
        elif callback_data == "type_income":
            if 'transaction_filters' not in context.user_data:
                context.user_data['transaction_filters'] = {}
            context.user_data['transaction_filters']['type'] = 'income'
            if 'transactions_view' not in context.user_data:
                context.user_data['transactions_view'] = {}
            context.user_data['transactions_view']['type'] = 'income'
            context.user_data['transactions_view']['page'] = 1
            await query.answer("✅ Фільтр типу застосовано")
            await show_transaction_filters(query, context)
        elif callback_data == "type_expense":
            if 'transaction_filters' not in context.user_data:
                context.user_data['transaction_filters'] = {}
            context.user_data['transaction_filters']['type'] = 'expense'
            if 'transactions_view' not in context.user_data:
                context.user_data['transactions_view'] = {}
            context.user_data['transactions_view']['type'] = 'expense'
            context.user_data['transactions_view']['page'] = 1
            await query.answer("✅ Фільтр типу застосовано")
            await show_transaction_filters(query, context)
        
        # Обробники категорій
        elif callback_data == "category_all":
            if 'transaction_filters' not in context.user_data:
                context.user_data['transaction_filters'] = {}
            context.user_data['transaction_filters']['category'] = 'all'
            if 'transactions_view' not in context.user_data:
                context.user_data['transactions_view'] = {}
            context.user_data['transactions_view']['category_id'] = None
            context.user_data['transactions_view']['page'] = 1
            await query.answer("✅ Фільтр за категорією застосовано")
            await show_transaction_filters(query, context)
        elif callback_data.startswith("category_") and callback_data != "category_all":
            try:
                category_id = int(callback_data.split("_")[1])
                if 'transaction_filters' not in context.user_data:
                    context.user_data['transaction_filters'] = {}
                context.user_data['transaction_filters']['category'] = category_id
                if 'transactions_view' not in context.user_data:
                    context.user_data['transactions_view'] = {}
                context.user_data['transactions_view']['category_id'] = category_id
                context.user_data['transactions_view']['page'] = 1
                await query.answer("✅ Фільтр за категорією застосовано")
                await show_transaction_filters(query, context)
            except ValueError:
                await query.answer("Неправильний формат ID категорії")
        
        # Обробники редагування транзакцій
        elif callback_data == "edit_transactions":
            await handle_edit_transactions(query, context)
        elif callback_data.startswith("view_transaction_"):
            await handle_view_single_transaction(query, context)
        elif callback_data.startswith("edit_transaction_"):
            await handle_edit_single_transaction(query, context)
        elif callback_data.startswith("edit_amount_"):
            await handle_edit_amount(query, context)
        elif callback_data.startswith("edit_description_"):
            await handle_edit_description(query, context)
        elif callback_data.startswith("edit_category_"):
            await handle_edit_category(query, context)
        elif callback_data.startswith("set_category_"):
            await handle_set_category(query, context)
        elif callback_data.startswith("delete_transaction_"):
            await handle_delete_transaction(query, context)
        elif callback_data.startswith("confirm_delete_"):
            await handle_confirm_delete(query, context)
            
        # Загальний обробник для невідомих колбеків
        else:
            await query.edit_message_text(
                f"🚧 *Функція '{callback_data}' знаходиться в розробці*\n\n"
                f"Дана функція буде доступна в наступних оновленнях бота.\n\n"
                f"Скористайтеся доступними функціями через головне меню.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error in handle_callback: {e}")
        await query.answer("Виникла помилка, будь ласка, спробуйте ще раз пізніше.", show_alert=True)


async def handle_confirm_receipt_add(query, context):
    """Обробляє підтвердження додавання транзакції з чека"""
    try:
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("Будь ласка, спочатку налаштуйте бота командою /start")
            return

        # Отримуємо збережені дані чека
        pending_receipt = context.user_data.get('pending_receipt')
        if not pending_receipt:
            await query.edit_message_text(
                "❌ Дані чека не знайдено. Спробуйте завантажити чек ще раз.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")
                ]])
            )
            return

        # Додаємо транзакцію до бази даних
        add_transaction(
            user_id=user.id,
            amount=pending_receipt['amount'],
            description=pending_receipt['description'],
            category_id=pending_receipt['category_id'],
            transaction_type=TransactionType.EXPENSE,
            transaction_date=pending_receipt['transaction_date'],
            source='receipt',
            receipt_image=pending_receipt['file_path']
        )

        # Очищуємо збережені дані
        context.user_data.pop('pending_receipt', None)

        # Показуємо підтвердження
        await query.edit_message_text(
            f"✅ **Транзакцію успішно додано!**\n\n"
            f"🏪 Магазин: {pending_receipt['store_name']}\n"
            f"💰 Сума: {pending_receipt['amount']:.2f} грн\n"
            f"📅 Дата: {pending_receipt['transaction_date'].strftime('%d.%m.%Y')}\n"
            f"📂 Категорія: {pending_receipt['category']}\n\n"
            f"Транзакцію додано до ваших витрат.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Переглянути транзакції", callback_data="view_all_transactions")],
                [InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error in handle_confirm_receipt_add: {e}")
        await query.edit_message_text(
            "❌ Виникла помилка під час додавання транзакції. Спробуйте ще раз.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")
            ]])
        )