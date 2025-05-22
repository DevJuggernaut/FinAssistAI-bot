from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import calendar

from database.db_operations import get_or_create_user

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
