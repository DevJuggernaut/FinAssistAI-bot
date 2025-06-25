"""
Модуль для створення та відображення головного меню бота.
Централізує всі варіанти головного меню для забезпечення консистентності.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging

logger = logging.getLogger(__name__)

def create_main_menu_keyboard():
    """Створює єдину версію клавіатури головного меню"""
    keyboard = [
        [
            InlineKeyboardButton("💰 Огляд фінансів", callback_data="my_budget"),
            InlineKeyboardButton("➕ Додати транзакцію", callback_data="add_transaction")
        ],
        [
            InlineKeyboardButton("📈 Аналітика", callback_data="analytics"),
            InlineKeyboardButton("🤖 AI-помічник", callback_data="ai_assistant_menu")
        ],
        [
            InlineKeyboardButton("💳 Рахунки", callback_data="accounts_menu"),
            InlineKeyboardButton("⚙️ Налаштування", callback_data="settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def show_main_menu(message_or_query, context, is_query=None):
    """
    Універсальна функція для показу головного меню.
    
    Args:
        message_or_query: Може бути або Message, або CallbackQuery
        context: Контекст бота
        is_query: Ручне вказування типу (якщо автовизначення не працює)
    """
    try:
        keyboard = create_main_menu_keyboard()
        text = "◀️ **Головне меню FinAssist**\n\nОберіть дію:"
        
        # Автоматично визначаємо тип об'єкта
        if is_query is None:
            is_query = hasattr(message_or_query, 'edit_message_text')
        
        if is_query:
            # Це CallbackQuery
            await message_or_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            # Це Message
            await message_or_query.reply_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Error in show_main_menu: {str(e)}")
        # Fallback до простого повідомлення
        fallback_text = "◀️ Головне меню\n\nВикористовуйте команди: /add, /budget, /analytics, /settings"
        
        if is_query or hasattr(message_or_query, 'edit_message_text'):
            try:
                await message_or_query.edit_message_text(fallback_text)
            except:
                await message_or_query.message.reply_text(fallback_text)
        else:
            await message_or_query.reply_text(fallback_text)

async def back_to_main_menu(query, context):
    """Обробник для повернення до головного меню через callback"""
    await show_main_menu(query, context, is_query=True)

# Альтернативні назви для зворотної сумісності
show_main_menu_callback = back_to_main_menu
back_to_main = back_to_main_menu
main_menu = back_to_main_menu
