from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Надсилає вітальне повідомлення при команді /start."""
    user = update.effective_user
    
    # Створюємо клавіатуру з кнопками для основних дій
    keyboard = [
        [
            InlineKeyboardButton("📊 Моя статистика", callback_data="stats"),
            InlineKeyboardButton("💰 Додати транзакцію", callback_data="add_transaction")
        ],
        [
            InlineKeyboardButton("🗂 Категорії", callback_data="categories"),
            InlineKeyboardButton("📝 Звіти", callback_data="reports")
        ],
        [
            InlineKeyboardButton("❓ Допомога", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_html(
        f"Привіт, {user.mention_html()}! 👋\n\n"
        f"Я ваш персональний фінансовий помічник. Я допоможу вам:\n"
        f"• Відстежувати витрати та доходи\n"
        f"• Аналізувати банківські виписки\n"
        f"• Категоризувати транзакції\n"
        f"• Отримувати персоналізовані рекомендації\n\n"
        f"Оберіть опцію нижче для початку роботи:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Надсилає повідомлення з допомогою при команді /help."""
    help_text = (
        "🤖 *Основні команди:*\n"
        "/start - Запустити бота\n"
        "/help - Показати це повідомлення\n"
        "/stats - Переглянути фінансову статистику\n"
        "/add - Додати нову транзакцію\n"
        "/report - Згенерувати звіт\n\n"
        
        "📋 *Як користуватись:*\n"
        "• Надішліть фото чека для автоматичного розпізнавання\n"
        "• Завантажте банківську виписку (.csv, .pdf, .xlsx)\n"
        "• Напишіть транзакцію текстом, наприклад: 'Кава 45 грн'\n\n"
        
        "🔍 *Додаткові функції:*\n"
        "• Персональні фінансові рекомендації\n"
        "• Автоматична категоризація витрат\n"
        "• Візуальна аналітика ваших фінансів"
    )
    
    await update.message.reply_markdown(help_text)