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
        message_or_query: Може бути або Message, або CallbackQuery, або Update
        context: Контекст бота
        is_query: Ручне вказування типу (якщо автовизначення не працює)
    """
    try:
        logger.info(f"show_main_menu called with: {type(message_or_query)}, is_query={is_query}")
        
        keyboard = create_main_menu_keyboard()
        text = "◀️ **Головне меню FinAssist**\n\nОберіть дію:"
        
        # Спочатку перевіряємо, чи це Update об'єкт
        if hasattr(message_or_query, 'callback_query') and message_or_query.callback_query:
            # Це Update з CallbackQuery
            query = message_or_query.callback_query
            logger.info(f"Extracted CallbackQuery from Update: {type(query)}")
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        elif hasattr(message_or_query, 'message') and message_or_query.message and not hasattr(message_or_query, 'edit_message_text'):
            # Це Update з Message (але НЕ CallbackQuery)
            message = message_or_query.message
            logger.info(f"Extracted Message from Update: {type(message)}")
            await message.reply_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        
        # Тепер обробляємо прямі CallbackQuery та Message об'єкти
        # Автоматично визначаємо тип об'єкта для CallbackQuery та Message
        if is_query is None:
            is_query = hasattr(message_or_query, 'edit_message_text')
        
        logger.info(f"Determined is_query={is_query} for type {type(message_or_query)}")
        
        if is_query or hasattr(message_or_query, 'edit_message_text'):
            # Це CallbackQuery
            logger.info("Using edit_message_text for CallbackQuery")
            await message_or_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            # Це Message
            logger.info("Using reply_text for Message")
            await message_or_query.reply_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Error in show_main_menu: {str(e)}")
        # Fallback до простого повідомлення
        fallback_text = "◀️ Головне меню\n\nВикористовуйте команди: /add, /budget, /analytics, /settings"
        
        try:
            # Обробляємо Update об'єкт
            if hasattr(message_or_query, 'callback_query') and message_or_query.callback_query:
                await message_or_query.callback_query.edit_message_text(fallback_text)
            elif hasattr(message_or_query, 'message') and message_or_query.message:
                await message_or_query.message.reply_text(fallback_text)
            elif hasattr(message_or_query, 'effective_message') and message_or_query.effective_message:
                await message_or_query.effective_message.reply_text(fallback_text)
            elif hasattr(message_or_query, 'edit_message_text'):
                # Це CallbackQuery
                await message_or_query.edit_message_text(fallback_text)
            elif hasattr(message_or_query, 'reply_text'):
                # Це Message
                await message_or_query.reply_text(fallback_text)
            else:
                logger.error(f"Cannot send fallback message, unknown object type: {type(message_or_query)}")
        except Exception as fallback_error:
            logger.error(f"Even fallback failed: {fallback_error}")

async def back_to_main_menu(update, context):
    """Обробник для повернення до головного меню через callback"""
    logger.info(f"back_to_main_menu called with: {type(update)}")
    
    # Перевіряємо, чи це Update об'єкт з callback_query
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await show_main_menu(query, context, is_query=True)
    elif hasattr(update, 'edit_message_text'):
        # Це CallbackQuery
        await show_main_menu(update, context, is_query=True)
    else:
        # Fallback - відправляємо нове повідомлення через message
        if hasattr(update, 'message') and update.message:
            await show_main_menu(update.message, context, is_query=False)
        else:
            logger.error(f"Cannot handle update type in back_to_main_menu: {type(update)}")
            # Останній fallback - спробуємо отримати effective_message
            if hasattr(update, 'effective_message') and update.effective_message:
                await show_main_menu(update.effective_message, context, is_query=False)

# Альтернативні назви для зворотної сумісності
show_main_menu_callback = back_to_main_menu
back_to_main = back_to_main_menu
main_menu = back_to_main_menu
