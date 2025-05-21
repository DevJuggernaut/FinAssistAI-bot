from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє натискання на інлайн-кнопки"""
    query = update.callback_query
    await query.answer()  # Відповідаємо на колбек, щоб прибрати "годинник" з кнопки
    
    callback_data = query.data
    
    if callback_data == "stats":
        await show_stats(query, context)
    elif callback_data == "add_transaction":
        await show_add_transaction_form(query, context)
    elif callback_data == "categories":
        await show_categories(query, context)
    elif callback_data == "reports":
        await show_reports_menu(query, context)
    elif callback_data == "help":
        await show_help(query, context)
    else:
        await query.edit_message_text(
            text="🔄 Функція в розробці. Спробуйте пізніше."
        )

async def show_stats(query, context):
    """Показує базову статистику"""
    # В майбутньому тут буде справжня статистика
    stats_text = (
        "📊 *Фінансова статистика*\n\n"
        "💸 *Витрати за місяць:* 0 грн\n"
        "💰 *Доходи за місяць:* 0 грн\n"
        "💹 *Баланс:* 0 грн\n\n"
        "🔝 *Топ категорій витрат:*\n"
        "Дані відсутні - додайте свою першу транзакцію!\n\n"
    )
    
    keyboard = [[InlineKeyboardButton("« Назад", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=stats_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_add_transaction_form(query, context):
    """Показує форму для додавання транзакції"""
    text = (
        "💰 *Додати нову транзакцію*\n\n"
        "Виберіть тип транзакції:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("💸 Витрата", callback_data="add_expense"),
            InlineKeyboardButton("💵 Дохід", callback_data="add_income")
        ],
        [InlineKeyboardButton("« Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )