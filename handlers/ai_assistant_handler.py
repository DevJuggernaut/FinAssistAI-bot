"""
AI Assistant Handler - обробник для AI-помічника з порадами та прогнозами
"""

import logging
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from database.db_operations import get_user_transactions, get_user
from database.models import TransactionType
from services.openai_service import OpenAIService
from database.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)
# Тимчасово встановлюємо DEBUG рівень для детального логування
logger.setLevel(logging.DEBUG)

# Стани для conversation handler
WAITING_AI_QUESTION = 1

# Ініціалізація OpenAI сервісу
openai_service = OpenAIService(OPENAI_API_KEY)

async def show_ai_assistant_menu(query, context):
    """Показує головне меню AI-помічника"""
    try:
        keyboard = [
            [
                InlineKeyboardButton("💡 Персональна порада", callback_data="ai_advice"),
                InlineKeyboardButton("🔮 Прогноз витрат", callback_data="ai_forecast")
            ],
            [
                InlineKeyboardButton("❓ Запитати AI", callback_data="ai_custom_question")
            ],
            [
                InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")
            ]
        ]
        
        text = (
            "🤖 **AI-помічник**\n\n"
            "Ваш розумний фінансовий консультант:\n\n"
            "💡 **Персональна порада**\n"
            "Аналіз ваших витрат і рекомендації\n\n"
            "🔮 **Фінансовий прогноз**\n"
            "Передбачення витрат на наступний місяць\n\n"
            "❓ **Запитати AI**\n"
            "Отримайте відповідь на будь-яке питання\n\n"
            "💡 *Всі поради базуються на ваших даних*"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_ai_assistant_menu: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при відкритті AI-помічника",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main")]
            ])
        )

async def handle_ai_advice(query, context):
    """Обробляє запит на персональну пораду"""
    logger.info("Starting handle_ai_advice")
    try:
        # Показуємо повідомлення про завантаження
        logger.debug("Updating message text to loading state")
        await query.edit_message_text(
            "🤖 **Аналізую ваші фінанси...**\n\n"
            "⏳ *Готую персональні рекомендації*"
        )
        
        logger.debug("Getting user by telegram ID")
        user = get_user(query.from_user.id)
        if not user:
            logger.warning(f"User not found for telegram ID: {query.from_user.id}")
            await query.edit_message_text(
                "❌ Користувач не знайдений",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ AI-помічник", callback_data="ai_assistant_menu")]
                ])
            )
            return
        
        logger.info(f"Found user: {user}")
        
        # Отримуємо транзакції за останні 30 днів
        logger.debug("Getting transactions for last 30 days")
        now = datetime.now()
        start_date = now - timedelta(days=30)
        logger.debug(f"Date range: {start_date} to {now}")
        
        transactions = get_user_transactions(user.id, limit=1000, start_date=start_date, end_date=now)
        logger.info(f"Retrieved {len(transactions)} transactions")
        
        if not transactions:
            logger.info("No transactions found, returning message to user")
            await query.edit_message_text(
                "📊 **Потрібно більше даних**\n\n"
                "Для якісних порад додайте кілька транзакцій.\n\n"
                "💡 *Чим більше даних, тим точніші рекомендації*",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Додати транзакцію", callback_data="add_transaction")],
                    [InlineKeyboardButton("◀️ AI-помічник", callback_data="ai_assistant_menu")]
                ]),
                parse_mode="Markdown"
            )
            return
        
        # Підготовляємо дані для аналізу
        logger.info("Starting transaction data preparation")
        transaction_data = []
        logger.info(f"Processing {len(transactions)} transactions")
        
        for i, t in enumerate(transactions):
            logger.debug(f"=== Processing transaction {i} ===")
            try:
                logger.debug(f"Transaction type: {type(t)}")
                logger.debug(f"Transaction object: {t}")
                
                # Детальне логування полів транзакції
                logger.debug(f"Transaction attributes: {dir(t)}")
                for attr in ['amount', 'transaction_date', 'category', 'type', 'description']:
                    if hasattr(t, attr):
                        value = getattr(t, attr)
                        logger.debug(f"  {attr}: {value} (type: {type(value)})")
                    else:
                        logger.debug(f"  {attr}: MISSING")
                
                # Безпечна конвертація amount
                if hasattr(t, 'amount'):
                    raw_amount = getattr(t, 'amount')
                    logger.debug(f"Raw amount: {raw_amount} (type: {type(raw_amount)})")
                    
                    if isinstance(raw_amount, (int, float)):
                        amount = float(raw_amount)
                        logger.debug(f"Converted amount (int/float): {amount}")
                    elif isinstance(raw_amount, str):
                        try:
                            amount = float(raw_amount)
                            logger.debug(f"Converted amount (str): {amount}")
                        except ValueError as e:
                            logger.warning(f"Cannot convert string amount to float: {raw_amount}, error: {e}")
                            amount = 0.0
                    elif hasattr(raw_amount, '__float__'):
                        try:
                            amount = float(raw_amount)
                            logger.debug(f"Converted amount (__float__): {amount}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Cannot convert amount to float via __float__: {raw_amount}, error: {e}")
                            amount = 0.0
                    elif raw_amount is None:
                        amount = 0.0
                        logger.debug("Amount is None, using 0.0")
                    else:
                        logger.warning(f"Cannot convert amount to float: {type(raw_amount)} = {raw_amount}")
                        amount = 0.0
                else:
                    amount = 0.0
                    logger.debug("No amount attribute, using 0.0")
                
                # Безпечна обробка дати
                if hasattr(t, 'transaction_date'):
                    logger.debug(f"Date type: {type(t.transaction_date)}, value: {t.transaction_date}")
                    if hasattr(t.transaction_date, 'isoformat'):
                        date_str = t.transaction_date.isoformat()
                    elif isinstance(t.transaction_date, str):
                        date_str = t.transaction_date
                    else:
                        date_str = str(t.transaction_date)
                else:
                    date_str = str(datetime.now().date())
                
                # Безпечна обробка категорії
                category_name = 'Без категорії'
                if hasattr(t, 'category') and t.category:
                    if hasattr(t.category, 'name'):
                        category_name = t.category.name
                    else:
                        category_name = str(t.category)
                
                # Безпечна обробка типу
                transaction_type = 'expense'
                if hasattr(t, 'type'):
                    transaction_type = 'expense' if t.type == TransactionType.EXPENSE else 'income'
                
                transaction_data.append({
                    'amount': amount,
                    'category': category_name,
                    'type': transaction_type,
                    'date': date_str,
                    'description': getattr(t, 'description', '') or ''
                })
                
                logger.debug(f"Successfully processed transaction {i}")
                
            except Exception as e:
                logger.error(f"Error processing transaction {i}: {e}")
                logger.error(f"Transaction object: {t}")
                logger.error(f"Transaction dir: {dir(t) if hasattr(t, '__dict__') else 'No __dict__'}")
                continue
        
        logger.info(f"Successfully processed {len(transaction_data)} transactions")
        
        # Перевіряємо, чи є дані для обробки
        if not transaction_data:
            await query.edit_message_text(
                "📊 **Не вдалося обробити транзакції**\n\n"
                "Виникла проблема з обробкою ваших транзакцій. Спробуйте ще раз.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ AI-помічник", callback_data="ai_assistant_menu")]
                ]),
                parse_mode="Markdown"
            )
            return
        
        logger.info("Starting AI advice generation")
        
        # Отримуємо пораду від AI
        advice = await generate_personal_advice(user, transaction_data)
        
        logger.info("AI advice generated successfully")
        
        keyboard = [
            [
                InlineKeyboardButton("🔮 Прогноз витрат", callback_data="ai_forecast"),
                InlineKeyboardButton("❓ Запитати AI", callback_data="ai_custom_question")
            ],
            [
                InlineKeyboardButton("🔄 Оновити пораду", callback_data="ai_advice"),
                InlineKeyboardButton("◀️ AI-помічник", callback_data="ai_assistant_menu")
            ]
        ]
        
        await query.edit_message_text(
            text=advice,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_ai_advice: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при отриманні поради від AI",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ AI-помічник", callback_data="ai_assistant_menu")]
            ])
        )

async def handle_ai_forecast(query, context):
    """Обробляє запит на фінансовий прогноз"""
    try:
        # Показуємо повідомлення про завантаження
        await query.edit_message_text(
            "🔮 **Створюю прогноз витрат...**\n\n"
            "⏳ *Аналізую ваші фінансові паттерни*"
        )
        
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text(
                "❌ Користувач не знайдений",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ AI-помічник", callback_data="ai_assistant_menu")]
                ])
            )
            return
        
        # Отримуємо транзакції за останні 60 днів для більш точного прогнозу
        now = datetime.now()
        start_date = now - timedelta(days=60)
        transactions = get_user_transactions(user.id, limit=1000, start_date=start_date, end_date=now)
        
        if len(transactions) < 5:
            await query.edit_message_text(
                "📊 **Потрібно більше даних**\n\n"
                "Для точного прогнозу додайте ще кілька транзакцій.\n\n"
                "💡 *Мінімум 5 операцій для якісного прогнозу*",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Додати транзакцію", callback_data="add_transaction")],
                    [InlineKeyboardButton("◀️ AI-помічник", callback_data="ai_assistant_menu")]
                ]),
                parse_mode="Markdown"
            )
            return
        
        # Підготовляємо дані для прогнозу
        transaction_data = []
        for t in transactions:
            try:
                # Безпечна конвертація amount
                if hasattr(t, 'amount'):
                    if isinstance(t.amount, (int, float)):
                        amount = float(t.amount)
                    elif isinstance(t.amount, str):
                        try:
                            amount = float(t.amount)
                        except ValueError:
                            amount = 0.0
                    elif hasattr(t.amount, '__float__'):
                        try:
                            amount = float(t.amount)
                        except (ValueError, TypeError):
                            amount = 0.0
                    elif t.amount is None:
                        amount = 0.0
                    else:
                        amount = 0.0
                else:
                    amount = 0.0
                
                # Безпечна обробка дати
                if hasattr(t, 'transaction_date'):
                    if hasattr(t.transaction_date, 'isoformat'):
                        date_str = t.transaction_date.isoformat()
                    elif isinstance(t.transaction_date, str):
                        date_str = t.transaction_date
                    else:
                        date_str = str(t.transaction_date)
                else:
                    date_str = str(datetime.now().date())
                
                transaction_data.append({
                    'amount': amount,
                    'category': t.category.name if t.category else 'Без категорії',
                    'type': 'expense' if t.type == TransactionType.EXPENSE else 'income',
                    'date': date_str,
                    'description': t.description or ''
                })
            except Exception as e:
                logger.warning(f"Error processing transaction {t}: {e}")
                continue
        
        # Отримуємо прогноз від AI
        forecast = await generate_financial_forecast(user, transaction_data)
        
        keyboard = [
            [
                InlineKeyboardButton("💡 Персональна порада", callback_data="ai_advice"),
                InlineKeyboardButton("❓ Запитати AI", callback_data="ai_custom_question")
            ],
            [
                InlineKeyboardButton("🔄 Оновити прогноз", callback_data="ai_forecast"),
                InlineKeyboardButton("◀️ AI-помічник", callback_data="ai_assistant_menu")
            ]
        ]
        
        await query.edit_message_text(
            text=forecast,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_ai_forecast: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при створенні прогнозу",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ AI-помічник", callback_data="ai_assistant_menu")]
            ])
        )

async def start_ai_question(update, context):
    """Починає діалог для кастомного питання до AI"""
    try:
        # Отримуємо query з update
        if hasattr(update, 'callback_query') and update.callback_query:
            query = update.callback_query
        else:
            query = update  # На випадок, якщо передається напряму CallbackQuery
            
        await query.edit_message_text(
            "❓ **Запитайте AI**\n\n"
            "Поставте будь-яке фінансове питання:\n\n"
            "💡 **Приклади:**\n"
            "• Як заощадити на відпустку?\n"
            "• Чи багато витрачаю на їжу?\n"
            "• Як планувати бюджет?\n"
            "• Де можна економити?\n\n"
            "✍️ *Введіть ваше питання:*",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Скасувати", callback_data="ai_assistant_menu")]
            ]),
            parse_mode="Markdown"
        )
        
        return WAITING_AI_QUESTION
        
    except Exception as e:
        logger.error(f"Error in start_ai_question: {str(e)}")
        # Спробуємо отримати query різними способами
        query = None
        if hasattr(update, 'callback_query') and update.callback_query:
            query = update.callback_query
        elif hasattr(update, 'edit_message_text'):
            query = update
            
        if query:
            await query.edit_message_text(
                "❌ Помилка при започаткуванні діалогу",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ AI-помічник", callback_data="ai_assistant_menu")]
                ])
            )
        return ConversationHandler.END

async def handle_ai_question(update, context):
    """Обробляє кастомне питання до AI"""
    try:
        user_question = update.message.text
        user = get_user(update.effective_user.id)
        
        if not user:
            await update.message.reply_text(
                "❌ Користувач не знайдений",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ AI-помічник", callback_data="ai_assistant_menu")]
                ])
            )
            return ConversationHandler.END
        
        # Показуємо повідомлення про обробку
        processing_msg = await update.message.reply_text(
            "⌛ **Обробляю питання...**\n\n"
            "⏳ *Готую персональну відповідь*"
        )
        
        # Отримуємо транзакції для контексту
        now = datetime.now()
        start_date = now - timedelta(days=30)
        transactions = get_user_transactions(user.id, limit=1000, start_date=start_date, end_date=now)
        
        # Підготовляємо дані
        transaction_data = []
        for t in transactions:
            try:
                # Безпечна конвертація amount
                if hasattr(t, 'amount'):
                    if isinstance(t.amount, (int, float)):
                        amount = float(t.amount)
                    elif isinstance(t.amount, str):
                        try:
                            amount = float(t.amount)
                        except ValueError:
                            amount = 0.0
                    elif hasattr(t.amount, '__float__'):
                        try:
                            amount = float(t.amount)
                        except (ValueError, TypeError):
                            amount = 0.0
                    elif t.amount is None:
                        amount = 0.0
                    else:
                        amount = 0.0
                else:
                    amount = 0.0
                
                # Безпечна обробка дати
                if hasattr(t, 'transaction_date'):
                    if hasattr(t.transaction_date, 'isoformat'):
                        date_str = t.transaction_date.isoformat()
                    elif isinstance(t.transaction_date, str):
                        date_str = t.transaction_date
                    else:
                        date_str = str(t.transaction_date)
                else:
                    date_str = str(datetime.now().date())
                
                transaction_data.append({
                    'amount': amount,
                    'category': t.category.name if t.category else 'Без категорії',
                    'type': 'expense' if t.type == TransactionType.EXPENSE else 'income',
                    'date': date_str,
                    'description': t.description or ''
                })
            except Exception as e:
                logger.warning(f"Error processing transaction {t}: {e}")
                continue
        
        # Отримуємо відповідь від AI
        answer = await answer_custom_question(user_question, user, transaction_data)
        
        keyboard = [
            [
                InlineKeyboardButton("❓ Ще питання", callback_data="ai_custom_question"),
                InlineKeyboardButton("💡 Порада", callback_data="ai_advice")
            ],
            [
                InlineKeyboardButton("◀️ AI-помічник", callback_data="ai_assistant_menu")
            ]
        ]
        
        await processing_msg.edit_text(
            text=answer,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in handle_ai_question: {str(e)}")
        await update.message.reply_text(
            "❌ Помилка при обробці питання",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ AI-помічник", callback_data="ai_assistant_menu")]
            ])
        )
        return ConversationHandler.END

# AI функції для генерації контенту

async def generate_personal_advice(user, transactions):
    """Генерує персональну пораду на основі даних користувача"""
    try:
        logger.info(f"Generating advice for {len(transactions)} transactions")
        
        # Аналіз витрат з детальним логуванням
        total_expenses = 0
        total_income = 0
        
        for i, t in enumerate(transactions):
            try:
                logger.debug(f"Processing transaction {i} for advice: {t}")
                
                if not isinstance(t, dict):
                    logger.error(f"Transaction {i} is not a dict: {type(t)} = {t}")
                    continue
                
                amount = t.get('amount', 0)
                trans_type = t.get('type', 'unknown')
                
                logger.debug(f"Transaction {i}: amount={amount} ({type(amount)}), type={trans_type}")
                
                if not isinstance(amount, (int, float)):
                    logger.error(f"Amount is not numeric: {type(amount)} = {amount}")
                    continue
                
                if trans_type == 'expense':
                    total_expenses += amount
                elif trans_type == 'income':
                    total_income += amount
                    
            except Exception as e:
                logger.error(f"Error processing transaction {i} in advice: {e}")
                continue
        
        logger.info(f"Calculated totals: expenses={total_expenses}, income={total_income}")
        
        # Категорії витрат
        expense_categories = {}
        for i, t in enumerate(transactions):
            try:
                if t.get('type') == 'expense':
                    cat = t.get('category', 'Без категорії')
                    amount = t.get('amount', 0)
                    expense_categories[cat] = expense_categories.get(cat, 0) + amount
            except Exception as e:
                logger.error(f"Error processing category for transaction {i}: {e}")
                continue
        
        # Створюємо промпт
        logger.info(f"Creating prompt with user data")
        logger.debug(f"User object: {user}")
        logger.debug(f"User type: {type(user)}")
        
        # Безпечна обробка користувача
        try:
            monthly_budget = getattr(user, 'monthly_budget', None) or 'не вказано'
            currency = getattr(user, 'currency', None) or 'UAH'
            logger.debug(f"User budget: {monthly_budget}, currency: {currency}")
        except Exception as e:
            logger.error(f"Error accessing user attributes: {e}")
            monthly_budget = 'не вказано'
            currency = 'UAH'
        
        prompt = f"""
        Проаналізуй фінансову ситуацію українського користувача та дай персональні поради українською мовою.
        
        Дані користувача:
        - Місячний бюджет: {monthly_budget} грн
        - Валюта: {currency}
        
        Транзакції за останні 30 днів:
        - Загальні витрати: {total_expenses:.2f} грн
        - Загальні доходи: {total_income:.2f} грн
        - Баланс: {total_income - total_expenses:.2f} грн
        
        Витрати по категоріях: {expense_categories}
        
        Дай 3-4 конкретні поради у форматі:
        💡 **Персональні поради:**
        
        1. [конкретна порада]
        2. [конкретна порада]
        3. [конкретна порада]
        
        🎯 **Головна рекомендація:** [найважливіша порада]
        
        Поради мають бути практичними, конкретними та корисними для українського користувача.
        """
        
        response = openai_service.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ти персональний фінансовий консультант для українських користувачів. Давай поради українською мовою, враховуючи специфіку українського ринку та економіки."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating advice: {str(e)}")
        return (
            "💡 **Персональні поради:**\n\n"
            "1. Відстежуйте всі витрати для кращого розуміння фінансової картини\n"
            "2. Встановіть місячний бюджет та старайтесь його дотримуватись\n"
            "3. Створіть фонд на непередбачені витрати (10-15% від доходу)\n\n"
            "🎯 **Головна рекомендація:** Регулярно аналізуйте свої фінанси для прийняття кращих рішень"
        )

async def generate_financial_forecast(user, transactions):
    """Генерує фінансовий прогноз на наступний місяць"""
    try:
        # Аналіз тенденцій
        monthly_expenses = {}
        for t in transactions:
            try:
                # Безпечна обробка дати
                if isinstance(t['date'], str):
                    if 'T' in t['date']:
                        date = datetime.fromisoformat(t['date'])
                    else:
                        date = datetime.strptime(t['date'], '%Y-%m-%d')
                else:
                    date = t['date'] if isinstance(t['date'], datetime) else datetime.now()
                
                month_key = date.strftime('%Y-%m')
                if t['type'] == 'expense':
                    monthly_expenses[month_key] = monthly_expenses.get(month_key, 0) + t['amount']
            except Exception as e:
                logger.warning(f"Error processing date {t['date']}: {e}")
                continue
        
        # Середні витрати
        avg_monthly_expenses = sum(monthly_expenses.values()) / max(len(monthly_expenses), 1)
        
        # Категорії
        category_analysis = {}
        for t in transactions:
            if t['type'] == 'expense':
                cat = t['category']
                category_analysis[cat] = category_analysis.get(cat, 0) + t['amount']
        
        prompt = f"""
        Створи прогноз фінансів на наступний місяць для українського користувача.
        
        Історичні дані (останні 60 днів):
        - Середні місячні витрати: {avg_monthly_expenses:.2f} грн
        - Витрати по місяцях: {monthly_expenses}
        - Витрати по категоріях: {category_analysis}
        - Місячний бюджет користувача: {user.monthly_budget or 'не встановлено'} грн
        
        Створи прогноз у форматі:
        🔮 **Прогноз на наступний місяць:**
        
        📊 **Очікувані витрати:** [сума] грн
        
        📈 **Прогноз по категоріях:**
        • [категорія]: [сума] грн
        • [категорія]: [сума] грн
        
        ⚠️ **Рекомендації:**
        • [рекомендація 1]
        • [рекомендація 2]
        
        🎯 **Фінансова ціль на місяць:** [конкретна ціль]
        
        Прогноз має бути реалістичним та базуватись на історичних даних.
        """
        
        response = openai_service.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ти експерт з фінансового планування для українських користувачів. Створюй реалістичні прогнози українською мовою."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating forecast: {str(e)}")
        return (
            "🔮 **Прогноз на наступний місяць:**\n\n"
            f"📊 **Очікувані витрати:** {avg_monthly_expenses:.2f} грн\n\n"
            "📈 **Прогноз базується на ваших попередніх витратах**\n\n"
            "⚠️ **Рекомендації:**\n"
            "• Відстежуйте витрати протягом місяця\n"
            "• Порівнюйте фактичні витрати з прогнозом\n\n"
            "🎯 **Фінансова ціль на місяць:** Дотримуватись запланованого бюджету"
        )

async def answer_custom_question(question, user, transactions):
    """Відповідає на кастомне питання користувача"""
    try:
        # Аналіз даних
        total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        
        expense_categories = {}
        for t in transactions:
            if t['type'] == 'expense':
                cat = t['category']
                expense_categories[cat] = expense_categories.get(cat, 0) + t['amount']
        
        prompt = f"""
        Користувач запитує: "{question}"
        
        Контекст фінансових даних користувача:
        - Місячний бюджет: {user.monthly_budget or 'не вказано'} грн
        - Витрати за 30 днів: {total_expenses:.2f} грн
        - Доходи за 30 днів: {total_income:.2f} грн
        - Витрати по категоріях: {expense_categories}
        
        Дай детальну персональну відповідь українською мовою, використовуючи реальні дані користувача.
        Відповідь має бути корисною, конкретною та практичною.
        
        Формат відповіді:
        ❓ **Ваше питання:** {question}
        
        💬 **Відповідь:**
        [детальна відповідь з аналізом даних]
        
        💡 **Практичні поради:**
        • [порада 1]
        • [порада 2]
        """
        
        response = openai_service.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ти персональний фінансовий консультант, який допомагає українським користувачам з їхніми фінансовими питаннями. Завжди відповідай українською мовою та базуй поради на реальних даних користувача."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error answering custom question: {str(e)}")
        return (
            f"❓ **Ваше питання:** {question}\n\n"
            "💬 **Відповідь:**\n"
            "Вибачте, виникла помилка при обробці вашого питання. "
            "Спробуйте переформулювати питання або скористайтесь готовими порадами.\n\n"
            "💡 **Альтернатива:** Скористайтесь функцією 'Персональна порада' для отримання загальних рекомендацій."
        )
