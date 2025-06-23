import re
import os
import logging
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from database.models import User, Transaction, TransactionType
from database.session import Session
from database.db_operations import (
    get_user,
    add_transaction,
    get_user_transactions,
    update_user_settings,
    get_user_categories
)
from services.statement_parser import statement_parser, receipt_processor
from services.ml_categorizer import transaction_categorizer
from services.openai_service import openai_service
from services.analytics_service import analytics_service
from services.mida_receipt_parser import mida_receipt_parser
from services.free_receipt_parser import free_receipt_parser

# Налаштування логування
logger = logging.getLogger(__name__)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка текстових повідомлень"""
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Будь ласка, спочатку налаштуйте бота командою /start")
            return
        
        # Перевіряємо, чи очікуємо введення транзакції з автоматичною категоризацією
        if context.user_data.get('awaiting_transaction_input'):
            from handlers.transaction_handler import process_transaction_input
            await process_transaction_input(update, context)
            return
        
        # Перевіряємо, чи користувач редагує транзакцію
        if 'editing_transaction_id' in context.user_data and 'editing_field' in context.user_data:
            await handle_transaction_edit_input(update, context)
            return
        
        # Перевіряємо, чи користувач вводить дані для транзакції
        if 'transaction_data' in context.user_data:
            transaction_data = context.user_data['transaction_data']
            
            if transaction_data.get('step') == 'amount':
                # Імпортуємо функцію з callback_handler
                from handlers.callback_handler import handle_transaction_amount_input
                await handle_transaction_amount_input(update, context)
                return
            elif transaction_data.get('step') == 'description':
                # Імпортуємо функцію з callback_handler
                from handlers.callback_handler import handle_transaction_description_input
                await handle_transaction_description_input(update, context)
                return
        
        # Перевіряємо, чи користувач створює нову категорію
        if 'category_creation' in context.user_data:
            from handlers.callback_handler import handle_category_creation_input
            await handle_category_creation_input(update, context)
            return
        
        # Перевіряємо, чи користувач додає нову категорію (нова система)
        if 'adding_category' in context.user_data:
            from handlers.settings_handler import handle_category_name_input
            await handle_category_name_input(update, context)
            return
        
        # Перевіряємо, чи користувач створює новий рахунок
        if context.user_data.get('awaiting_account_name'):
            from handlers.accounts_handler import handle_account_name_input
            handled = await handle_account_name_input(update.message, context)
            if handled:
                return
        
        # Якщо очікуємо введення суми після вибору категорії
        if context.user_data.get('awaiting_amount'):
            try:
                amount = float(update.message.text.replace(',', '.'))
                context.user_data['transaction_amount'] = amount
                context.user_data.pop('awaiting_amount', None)
                ttype = context.user_data.get('transaction_type', 'expense').upper()
                if ttype not in ('EXPENSE', 'INCOME'):
                    ttype = 'EXPENSE'
                add_transaction(
                    user_id=user.id,
                    amount=amount,
                    description="",
                    category_id=int(context.user_data.get('category_id')) if context.user_data.get('category_id') else None,
                    transaction_type=ttype
                )
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = [[InlineKeyboardButton("🏠 Головне меню", callback_data="add_transaction")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"✅ Транзакцію додано!\nСума: {amount} грн",
                    reply_markup=reply_markup
                )
                context.user_data.pop('transaction_type', None)
                context.user_data.pop('category_id', None)
                context.user_data.pop('transaction_amount', None)
                return
            except ValueError:
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = [[InlineKeyboardButton("🏠 Головне меню", callback_data="add_transaction")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "❌ Введіть коректну суму (наприклад, 150.50)",
                    reply_markup=reply_markup
                )
                return
        
        # Перевіряємо чи це транзакція у форматі "сума опис"
        match = re.match(r'^(\d+(?:\.\d+)?)\s+(.+)$', update.message.text)
        if match:
            amount = float(match.group(1))
            description = match.group(2)
            
            add_transaction(
                user_id=user.id,
                amount=amount,
                description=description,
                category_id=None,  # Без категорії для швидкого додавання
                transaction_type='expense'
            )
            
            await update.message.reply_text(
                f"✅ Транзакцію додано!\n"
                f"Сума: {amount} грн\n"
                f"Опис: {description}"
            )
            return
        
        # Якщо це не транзакція, відправляємо підказку
        await update.message.reply_text(
            "📝 Щоб додати транзакцію, напишіть суму та опис.\n"
            "Наприклад: 100 Продукти\n\n"
            "Або використовуйте команду /add"
        )
    except Exception as e:
        logger.error(f"Error handling text message: {str(e)}")
        await update.message.reply_text("Виникла помилка при обробці повідомлення.")

async def handle_financial_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка фінансового запитання з використанням OpenAI"""
    question = update.message.text.strip()
    
    thinking_message = await update.message.reply_text(
        "🤔 Обдумую відповідь на ваше запитання..."
    )
    
    try:
        from database.db_operations import get_or_create_user
        from services.financial_advisor import answer_user_question
        
        # Отримуємо дані про користувача
        telegram_id = update.effective_user.id
        user = get_or_create_user(
            telegram_id=telegram_id, 
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name
        )
        
        # Отримуємо відповідь на запитання
        answer = answer_user_question(user.id, question)
        
        # Відправляємо відповідь
        await thinking_message.edit_text(
            f"💡 Відповідь на ваше запитання:\n\n{answer}"
        )
    except Exception as e:
        await thinking_message.edit_text(
            f"❌ На жаль, сталася помилка при обробці вашого запитання: {str(e)}\n"
            "Будь ласка, спробуйте переформулювати запитання або зверніться до команди підтримки."
        )

async def handle_advice_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє запити на фінансову пораду"""
    await update.message.reply_text("🤔 Аналізую ваші фінансові дані для надання поради...")
    
    try:
        from database.db_operations import get_or_create_user
        from services.financial_advisor import FinancialAdvisor
        
        # Отримуємо дані про користувача
        telegram_id = update.effective_user.id
        user = get_or_create_user(
            telegram_id=telegram_id, 
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name
        )
        
        # Створюємо об'єкт фінансового радника
        advisor = FinancialAdvisor(user.id)
        
        # Визначаємо тип поради на основі тексту запиту
        text = update.message.text.lower()
        
        if any(keyword in text for keyword in ['заощадити', 'заощадження', 'економити', 'економія']):
            advice_type = 'savings'
        elif any(keyword in text for keyword in ['інвестиції', 'інвестувати', 'вкладати', 'вкладення']):
            advice_type = 'investment'
        elif any(keyword in text for keyword in ['бюджет', 'планувати', 'витрати', 'витрачати']):
            advice_type = 'budget'
        else:
            advice_type = 'general'
        
        # Генеруємо пораду
        advice = advisor.generate_financial_advice(advice_type)
        
        # Відправляємо пораду
        await update.message.reply_text(
            f"💡 Фінансова порада:\n\n{advice}"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ На жаль, сталася помилка при генерації поради: {str(e)}\n"
            "Будь ласка, спробуйте пізніше або зверніться до команди /help."
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка фотографій чеків"""
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Будь ласка, спочатку налаштуйте бота командою /start")
            return
        
        # Отримуємо фото
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Створюємо директорію для збереження, якщо її немає
        os.makedirs('uploads', exist_ok=True)
        
        # Зберігаємо фото
        file_path = f'uploads/receipt_{user.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
        await file.download_to_drive(file_path)
        
        # Показуємо повідомлення про обробку
        processing_message = await update.message.reply_text(
            "🔍 Розпізнаю чек...\nЦе може зайняти кілька секунд"
        )
        
        # Спочатку пробуємо розпізнати як MIDA чек
        receipt_data = mida_receipt_parser.parse_receipt(file_path)
        
        # Якщо MIDA парсер не впорався, використовуємо загальний безкоштовний парсер
        if not receipt_data:
            receipt_data = free_receipt_parser.parse_receipt(file_path)
        
        if not receipt_data or receipt_data.get('total_amount', 0) <= 0:
            await processing_message.edit_text(
                "❌ Не вдалося розпізнати чек. Переконайтеся, що:\n"
                "• Фото чітке і добре освітлене\n"
                "• Весь чек поміщається в кадр\n"
                "• Текст на чеку добре читається"
            )
            return
        
        # Перевіряємо, чи це MIDA чек з категоризованими товарами
        if 'categorized_items' in receipt_data and receipt_data['categorized_items']:
            await processing_message.edit_text("✅ Чек MIDA успішно розпізнано!")
            
            # Показуємо детальний результат для MIDA
            await send_mida_receipt_summary(update, receipt_data, user)
        else:
            # Звичайна обробка для інших чеків
            try:
                category, confidence = transaction_categorizer.predict_category(
                    receipt_data.get('raw_text', '') or receipt_data.get('store_name', 'Покупка')
                )
            except:
                # Якщо модель не навчена, використовуємо стандартну категорію
                category = 'groceries'
                confidence = 0.5
            
            # Знаходимо категорію або створюємо "Інше"
            user_categories = get_user_categories(user.id)
            category_id = None
            for cat in user_categories:
                if cat.name.lower() == category.lower():
                    category_id = cat.id
                    break
            
            # Якщо категорію не знайдено, використовуємо першу доступну або None
            if not category_id and user_categories:
                category_id = user_categories[0].id
            
            # Зберігаємо дані чека в контекст для подальшого підтвердження
            context.user_data['pending_receipt'] = {
                'amount': receipt_data['total_amount'],
                'description': f"Покупка в {receipt_data.get('store_name', 'магазині')}",
                'category_id': category_id,
                'transaction_date': receipt_data.get('date', datetime.now()),
                'file_path': file_path,
                'store_name': receipt_data.get('store_name', 'Невідомо'),
                'category': category,
                'confidence': confidence
            }
            
            # Створюємо кнопки для підтвердження
            keyboard = [
                [
                    InlineKeyboardButton("✅ Додати", callback_data="confirm_receipt_add"),
                    InlineKeyboardButton("❌ Назад", callback_data="back_to_main_menu")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await processing_message.edit_text(
                f"✅ Чек оброблено!\n\n"
                f"🏪 Магазин: {receipt_data.get('store_name', 'Невідомо')}\n"
                f"💰 Сума: {receipt_data['total_amount']:.2f} грн\n"
                f"📅 Дата: {receipt_data.get('date', datetime.now()).strftime('%d.%m.%Y')}\n"
                f"📂 Категорія: {category}\n"
                f"🎯 Впевненість: {confidence:.1%}",
                reply_markup=reply_markup
            )
            
    except Exception as e:
        logger.error(f"Error handling photo: {str(e)}")
        await update.message.reply_text("❌ Виникла помилка при обробці чека. Спробуйте ще раз.")


async def send_mida_receipt_summary(update: Update, receipt_data: Dict, user):
    """Відправляє детальний звіт по чеку MIDA з категоризованими товарами"""
    try:
        categorized_items = receipt_data.get('categorized_items', {})
        
        # Формуємо повідомлення
        message_parts = [
            "🛒 **Чек MIDA розпізнано успішно!**\n",
            f"💰 **Загальна сума:** {receipt_data['total_amount']:.2f} грн",
            f"📅 **Дата:** {receipt_data.get('date', datetime.now()).strftime('%d.%m.%Y')}\n"
        ]
        
        # Додаємо категорії товарів
        total_saved = 0
        for category, data in categorized_items.items():
            if isinstance(data, dict) and 'items' in data:
                items = data['items']
                category_total = data['total_amount']
                item_count = data['item_count']
                
                message_parts.append(f"📂 **{category.title()}** ({item_count} поз.): {category_total:.2f} грн")
                
                # Додаємо список товарів (максимум 3 для економії місця)
                for i, item in enumerate(items[:3]):
                    message_parts.append(f"   • {item['name']}: {item['price']:.2f} грн")
                
                if len(items) > 3:
                    message_parts.append(f"   • ... та ще {len(items) - 3} товарів")
                
                message_parts.append("")  # Порожній рядок для розділення
                
                # Знаходимо або створюємо категорію
                user_categories = get_user_categories(user.id)
                category_id = None
                for cat in user_categories:
                    if cat.name.lower() == category.lower():
                        category_id = cat.id
                        break
                
                # Якщо категорію не знайдено, використовуємо першу доступну
                if not category_id and user_categories:
                    category_id = user_categories[0].id
                
                # Додаємо транзакцію для кожної категорії
                add_transaction(
                    user_id=user.id,
                    amount=category_total,
                    description=f"MIDA - {category} ({item_count} товарів)",
                    category_id=category_id,
                    transaction_type=TransactionType.EXPENSE,  # Використовуємо enum значення
                    transaction_date=receipt_data.get('date', datetime.now()),
                    source='mida_receipt'
                )
                total_saved += category_total
        
        # Додаємо підсумок
        message_parts.append(f"✅ **Створено транзакцій на суму:** {total_saved:.2f} грн")
        message_parts.append(f"📊 **Категорій:** {len(categorized_items)}")
        
        # Відправляємо повідомлення
        await update.message.reply_text(
            "\n".join(message_parts),
            parse_mode="Markdown"
        )
        
        # Пропонуємо додаткові дії
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [
                InlineKeyboardButton("📊 Переглянути статистику", callback_data="show_stats"),
                InlineKeyboardButton("📈 Аналітика витрат", callback_data="show_charts")
            ],
            [
                InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Що бажаєте зробити далі?",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error sending MIDA receipt summary: {str(e)}")
        await update.message.reply_text("❌ Помилка при формуванні звіту по чеку")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка банківських виписок"""
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Будь ласка, спочатку налаштуйте бота командою /start")
            return
        
        # Перевіряємо, чи очікуємо файл виписки
        if context.user_data.get('waiting_for_statement', False):
            # Використовуємо функцію з callback_handler
            from handlers.callback_handler import handle_statement_upload
            await handle_statement_upload(update, context)
            return
        
        # Отримуємо документ
        document = update.message.document
        file = await context.bot.get_file(document.file_id)
        
        # Створюємо директорію для збереження, якщо її немає
        os.makedirs('uploads', exist_ok=True)
        
        # Зберігаємо файл
        file_path = f'uploads/statement_{user.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}{os.path.splitext(document.file_name)[1]}'
        await file.download_to_drive(file_path)
        
        # Обробляємо виписку
        transactions = statement_parser.parse_bank_statement(file_path)
        
        # Додаємо транзакції
        added_count = 0
        for transaction in transactions:
            # Категорізуємо транзакцію
            category, confidence = transaction_categorizer.predict_category(transaction['description'])
            
            transaction_data = {
                'user_id': user.id,
                'amount': transaction['amount'],
                'description': transaction['description'],
                'category': category,
                'type': transaction['type'],
                'date': transaction['date'],
                'source': 'bank_statement'
            }
            
            add_transaction(transaction_data)
            added_count += 1
        
        await update.message.reply_text(
            f"Виписку оброблено!\n"
            f"Додано {added_count} транзакцій."
        )
    except Exception as e:
        logger.error(f"Error handling document: {str(e)}")
        await update.message.reply_text("Виникла помилка при обробці виписки.")

async def handle_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /report"""
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Будь ласка, спочатку налаштуйте бота командою /start")
            return
        
        # Отримуємо транзакції за останній місяць
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        transactions = get_user_transactions(user.id, start_date, end_date)
        
        # Генеруємо звіт
        report = analytics_service.generate_monthly_report(transactions)
        
        # Відправляємо підсумок
        summary = report['summary']
        await update.message.reply_text(
            f"📊 Місячний звіт\n\n"
            f"Доходи: {summary['total_income']:.2f}\n"
            f"Витрати: {summary['total_expenses']:.2f}\n"
            f"Заощадження: {summary['net_savings']:.2f}\n"
            f"Норма заощадження: {summary['savings_rate']:.1f}%"
        )
        
        # Відправляємо графіки
        for viz_type, viz_data in report['visualizations'].items():
            if viz_data:  # Перевіряємо, чи є дані для візуалізації
                await update.message.reply_photo(
                    photo=viz_data,
                    caption=f"Графік: {viz_type}"
                )
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        await update.message.reply_text("Виникла помилка при генерації звіту.")

async def handle_advice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /advice"""
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Будь ласка, спочатку налаштуйте бота командою /start")
            return
        
        # Отримуємо транзакції за останні 3 місяці
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        transactions = get_user_transactions(user.id, start_date, end_date)
        
        # Генеруємо поради
        advice = openai_service.generate_financial_advice(transactions)
        
        # Відправляємо поради
        await update.message.reply_text(
            f"💡 Фінансові поради\n\n"
            f"Аналіз ситуації:\n{advice['analysis']}\n\n"
            f"Рекомендації:\n" + "\n".join(f"• {rec}" for rec in advice['recommendations']) + "\n\n"
            f"Області для покращення:\n" + "\n".join(f"• {area}" for area in advice['improvement_areas'])
        )
        
        # Відправляємо плани
        await update.message.reply_text(
            f"📅 Плани\n\n"
            f"Короткостроковий план:\n{advice['short_term_plan']}\n\n"
            f"Довгостроковий план:\n{advice['long_term_plan']}"
        )
    except Exception as e:
        logger.error(f"Error generating advice: {str(e)}")
        await update.message.reply_text("Виникла помилка при генерації порад.")

async def handle_analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /analyze"""
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Будь ласка, спочатку налаштуйте бота командою /start")
            return
        
        # Створюємо клавіатуру для вибору типу аналізу
        keyboard = [
            [
                InlineKeyboardButton("Аналіз категорій", callback_data="analyze_categories"),
                InlineKeyboardButton("Тренди витрат", callback_data="analyze_trends")
            ],
            [
                InlineKeyboardButton("Аналіз бюджету", callback_data="analyze_budget"),
                InlineKeyboardButton("Повний аналіз", callback_data="analyze_full")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Виберіть тип аналізу:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error handling analyze command: {str(e)}")
        await update.message.reply_text("Виникла помилка при обробці команди аналізу.")

async def handle_document_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка документів (виписок)"""
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Будь ласка, спочатку налаштуйте бота командою /start")
            return
        
        # Перевіряємо, чи очікуємо файл
        awaiting_file = context.user_data.get('awaiting_file')
        logger.info(f"Document received. Awaiting file type: {awaiting_file}, Context data: {context.user_data}")
        
        if not awaiting_file:
            await update.message.reply_text(
                "📄 Файл отримано, але я не очікував його.\n\n"
                "Щоб завантажити виписку, спочатку перейдіть до:\n"
                "💳 Додати транзакцію → 📤 Завантажити виписку"
            )
            return
        
        document = update.message.document
        if not document:
            await update.message.reply_text("❌ Помилка: файл не знайдено.")
            return
        
        # Перевіряємо розмір файлу
        max_size = 10 * 1024 * 1024  # 10 МБ
        if document.file_size > max_size:
            await update.message.reply_text(
                f"❌ Файл занадто великий: {document.file_size / 1024 / 1024:.1f} МБ\n"
                f"Максимальний розмір: {max_size / 1024 / 1024:.0f} МБ"
            )
            return
        
        # Перевіряємо тип файлу
        file_name = document.file_name.lower()
        bank_type = context.user_data.get('file_source', 'unknown')
        
        logger.info(f"Received document: {file_name}, awaiting type: {awaiting_file}, bank: {bank_type}")
        
        # Спеціальна перевірка для ПриватБанку: не приймаємо PDF
        if bank_type == 'privatbank' and file_name.endswith('.pdf'):
            await update.message.reply_text(
                "❌ **PDF файли не підтримуються для ПриватБанку**\n\n"
                "🏦 **ПриватБанк підтримує лише Excel файли (.xlsx)**\n\n"
                "💡 **Як отримати Excel виписку:**\n"
                "1️⃣ Увійдіть в Приват24\n"
                "2️⃣ Перейдіть до картки/рахунку\n"
                "3️⃣ Виберіть 'Виписка'\n"
                "4️⃣ Встановіть потрібний період\n"
                "5️⃣ **Обов'язково виберіть формат 'Excel'**\n\n"
                "Спробуйте знову з Excel файлом.",
                parse_mode="Markdown"
            )
            return
        
        if awaiting_file == 'pdf' and not file_name.endswith('.pdf'):
            await update.message.reply_text(
                "❌ **Невідповідний формат файлу**\n\n"
                f"Очікується: PDF файл (.pdf)\n"
                f"Отримано: {document.file_name}\n\n"
                "Спробуйте знову з правильним файлом.",
                parse_mode="Markdown"
            )
            return
        elif awaiting_file == 'excel' and not (file_name.endswith('.xlsx') or file_name.endswith('.xls')):
            await update.message.reply_text(
                "❌ **Невідповідний формат файлу**\n\n"
                f"Очікується: Excel файл (.xlsx або .xls)\n"
                f"Отримано: {document.file_name}\n\n"
                "Спробуйте знову з правильним файлом.",
                parse_mode="Markdown"
            )
            return
        elif awaiting_file == 'csv' and not file_name.endswith('.csv'):
            await update.message.reply_text(
                "❌ **Невідповідний формат файлу**\n\n"
                f"Очікується: CSV файл (.csv)\n"
                f"Отримано: {document.file_name}\n\n"
                "Спробуйте знову з правильним файлом.",
                parse_mode="Markdown"
            )
            return
        
        # Відправляємо повідомлення про початок обробки
        processing_message = await update.message.reply_text(
            "🔄 **Обробка файлу...**\n\n"
            "⏳ Завантажую та аналізую виписку\n"
            "📊 Розпізнаю транзакції\n"
            "🏷️ Визначаю категорії\n\n"
            "_Це може зайняти кілька секунд_",
            parse_mode="Markdown"
        )
        
        try:
            # Завантажуємо файл
            file = await context.bot.get_file(document.file_id)
            file_path = os.path.join("uploads", "statements", f"{user.id}_{document.file_name}")
            
            # Створюємо директорію якщо не існує
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Завантажуємо файл
            await file.download_to_drive(file_path)
            
            # Обробляємо файл в залежності від типу та банку
            from services.statement_parser import StatementParser
            parser = StatementParser()
            
            # Отримуємо банк з контексту
            bank_type = context.user_data.get('file_source', None)
            logger.info(f"Processing {awaiting_file} file from {bank_type} bank")
            
            # Відображаємо користувачу інформацію про процес
            await processing_message.edit_text(
                f"🔄 **Обробка {awaiting_file} файлу від {bank_type if bank_type else 'невідомого'} банку...**\n\n"
                "⏳ Аналізую виписку\n"
                "📊 Розпізнаю транзакції\n\n"
                "_Будь ласка, зачекайте..._",
                parse_mode="Markdown"
            )
            
            # Використовуємо parse_bank_statement з вказанням банку
            try:
                # Перевіряємо, чи існує файл
                if not os.path.exists(file_path):
                    logger.error(f"File does not exist: {file_path}")
                    raise FileNotFoundError(f"Файл не знайдено: {file_path}")
                
                # Перевіряємо розмір файлу
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    logger.error(f"File is empty: {file_path}")
                    raise ValueError("Файл порожній.")
                
                # Визначаємо метод парсингу в залежності від типу файлу
                logger.info(f"Using parser for file type: {awaiting_file} from bank: {bank_type}")
                
                # Оновлюємо повідомлення про статус
                await processing_message.edit_text(
                    f"🔄 **Аналізую {awaiting_file.upper()} файл {bank_type or ''}**\n\n"
                    "⚙️ Розпізнавання структури даних...\n"
                    "📊 Пошук транзакцій...\n\n"
                    "_Це може зайняти кілька секунд_",
                    parse_mode="Markdown"
                )
                
                # Викликаємо відповідний метод парсингу
                if awaiting_file == 'excel':
                    logger.info(f"Using Excel parser for bank: {bank_type}")
                    if bank_type == 'monobank':
                        # Для Monobank XLS використовуємо спеціальний метод
                        transactions = parser._parse_monobank_xls(file_path)
                    else:
                        transactions = await parser.parse_excel(file_path)
                elif awaiting_file == 'pdf':
                    logger.info(f"Using PDF parser for bank: {bank_type}")
                    transactions = await parser.parse_pdf(file_path)
                elif awaiting_file == 'csv':
                    logger.info(f"Using CSV parser for bank: {bank_type}")
                    if bank_type == 'monobank':
                        # Оскільки parse_csv це вже асинхронна функція, використовуємо безпосередньо_parse_monobank_csv
                        transactions = parser._parse_monobank_csv(file_path)
                    else:
                        transactions = await parser.parse_csv(file_path)
                else:
                    logger.info(f"Using general bank statement parser")
                    transactions = parser.parse_bank_statement(file_path, bank_type=bank_type)
                
                logger.info(f"Successfully parsed {len(transactions)} transactions")
            except Exception as e:
                logger.error(f"Error parsing statement: {str(e)}", exc_info=True)
                transactions = []
            
            # Видаляємо тимчасовий файл
            if os.path.exists(file_path):
                os.remove(file_path)
            
            if not transactions:
                await processing_message.edit_text(
                    "❌ **Не вдалося розпізнати транзакції**\n\n"
                    "Можливі причини:\n"
                    "• Невірний формат файлу\n"
                    "• Файл пошкоджений\n"
                    "• Нестандартна структура даних\n\n"
                    "Спробуйте інший файл або скористайтеся ручним додаванням.",
                    parse_mode="Markdown"
                )
                return
            
            # Зберігаємо транзакції в контексті для перегляду
            context.user_data['parsed_transactions'] = transactions
            context.user_data['awaiting_file'] = None
            
            # Показуємо попередній перегляд
            await show_transactions_preview(processing_message, context, transactions)
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            await processing_message.edit_text(
                f"❌ **Помилка при обробці файлу**\n\n"
                f"Деталі: {str(e)}\n\n"
                "Спробуйте інший файл або скористайтеся ручним додаванням.",
                parse_mode="Markdown"
            )
    
    except Exception as e:
        logger.error(f"Error in handle_document_message: {str(e)}")
        await update.message.reply_text("Виникла помилка при обробці файлу.")

async def show_transactions_preview(message, context, transactions):
    """Показує попередній перегляд розпізнаних транзакцій"""
    try:
        if len(transactions) > 10:
            preview_transactions = transactions[:10]
            more_count = len(transactions) - 10
        else:
            preview_transactions = transactions
            more_count = 0
        
        text = f"📊 **Знайдено {len(transactions)} транзакцій**\n\n"
        text += "Ось попередній перегляд ваших операцій з файлу. Перевірте дані перед імпортом.\n\n"
        for i, trans in enumerate(preview_transactions, 1):
            date_str = trans.get('date', 'Невідома дата')
            amount = trans.get('amount', 0)
            description = trans.get('description', 'Без опису')[:30]
            trans_type = trans.get('type', 'expense')
            type_emoji = "💸" if trans_type == 'expense' else "💰"
            sign = "-" if trans_type == 'expense' else "+"
            text += f"{i}. {type_emoji} {sign}{amount:,.2f} ₴\n"
            text += f"   📅 {date_str} • 📝 {description}\n\n"
        if more_count > 0:
            text += f"➕ _І ще {more_count} транзакцій..._\n\n"
        text += "Що далі?\n"
        text += "• Перевірте та відредагуйте транзакції\n"
        text += "• Підтвердьте імпорт, якщо все вірно\n\n"
        text += "Оберіть дію нижче:"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Додати всі", callback_data="import_all_transactions"),
                InlineKeyboardButton("✏️ Редагувати", callback_data="edit_transactions")
            ],
            [
                InlineKeyboardButton("❌ Скасувати", callback_data="cancel_import")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in show_transactions_preview: {e}")
        await message.edit_text("❌ Помилка при попередньому перегляді транзакцій.")

async def handle_transaction_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє введення нових значень при редагуванні транзакції"""
    from database.db_operations import update_transaction, get_transaction_by_id
    from handlers.transaction_handler import handle_edit_single_transaction
    
    try:
        transaction_id = context.user_data.get('editing_transaction_id')
        editing_field = context.user_data.get('editing_field')
        user_input = update.message.text.strip()
        
        if not transaction_id or not editing_field:
            await update.message.reply_text("Помилка: не знайдені дані для редагування.")
            return
        
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Користувач не знайдений.")
            return
        
        # Перевіряємо, що транзакція існує
        transaction = get_transaction_by_id(transaction_id, user.id)
        if not transaction:
            await update.message.reply_text("Транзакція не знайдена.")
            return
        
        success = False
        
        if editing_field == 'amount':
            # Перевіряємо валідність суми
            try:
                amount = float(user_input.replace(',', '.'))
                if amount <= 0:
                    await update.message.reply_text(
                        "❌ Сума повинна бути більше нуля. Спробуйте ще раз:",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("❌ Скасувати", callback_data=f"edit_transaction_{transaction_id}")
                        ]])
                    )
                    return
                
                result = update_transaction(transaction_id, user.id, amount=amount)
                if result:
                    success = True
                    await update.message.reply_text(f"✅ Сума оновлена на {amount:.2f} ₴")
                
            except ValueError:
                await update.message.reply_text(
                    "❌ Неправильний формат суми. Введіть число (наприклад: 150.50):",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ Скасувати", callback_data=f"edit_transaction_{transaction_id}")
                    ]])
                )
                return
        
        elif editing_field == 'description':
            if len(user_input) > 255:
                await update.message.reply_text(
                    "❌ Опис занадто довгий (максимум 255 символів). Спробуйте ще раз:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ Скасувати", callback_data=f"edit_transaction_{transaction_id}")
                    ]])
                )
                return
            
            result = update_transaction(transaction_id, user.id, description=user_input)
            if result:
                success = True
                await update.message.reply_text(f"✅ Опис оновлено: {user_input}")
        
        if success:
            # Очищуємо дані редагування
            context.user_data.pop('editing_transaction_id', None)
            context.user_data.pop('editing_field', None)
            
            # Показуємо оновлене меню транзакції
            keyboard = [[
                InlineKeyboardButton("📝 Показати оновлену транзакцію", 
                                   callback_data=f"edit_transaction_{transaction_id}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "Оберіть дію:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("❌ Помилка при оновленні транзакції.")
            
    except Exception as e:
        logger.error(f"Error in handle_transaction_edit_input: {e}")
        await update.message.reply_text("Виникла помилка при обробці введення.")

async def handle_transaction_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка введення суми транзакції"""
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Будь ласка, спочатку налаштуйте бота командою /start")
            return
        
        amount_text = update.message.text.strip().replace(',', '.')
        if not re.match(r'^\d+(\.\d{1,2})?$', amount_text):
            await update.message.reply_text("❌ Введіть коректну суму (наприклад, 150.50)")
            return
        
        amount = float(amount_text)
        context.user_data['transaction_data']['amount'] = amount
        
        # Запитуємо опис транзакції
        await update.message.reply_text(
            "📝 Введіть опис транзакції (наприклад, 'Продукти, кафе')"
        )
        
        # Оновлюємо крок на введення опису
        context.user_data['transaction_data']['step'] = 'description'
    except Exception as e:
        logger.error(f"Error handling transaction amount input: {str(e)}")
        await update.message.reply_text("Виникла помилка при обробці суми транзакції.")

async def handle_transaction_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка введення опису транзакції"""
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Будь ласка, спочатку налаштуйте бота командою /start")
            return
        
        description = update.message.text.strip()
        context.user_data['transaction_data']['description'] = description
        
        transaction_data = context.user_data['transaction_data']
        amount = transaction_data.get('amount')
        
        # Додаємо транзакцію
        transaction = Transaction(
            user_id=user.id,
            amount=amount,
            type=TransactionType.EXPENSE,
            description=description
        )
        
        add_transaction(transaction)
        
        await update.message.reply_text(
            f"✅ Транзакцію додано!\n"
            f"Сума: {amount} грн\n"
            f"Опис: {description}"
        )
        
        # Очищаємо дані транзакції
        context.user_data.pop('transaction_data', None)
    except Exception as e:
        logger.error(f"Error handling transaction description input: {str(e)}")
        await update.message.reply_text("Виникла помилка при обробці опису транзакції.")

async def handle_category_creation_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка введення нової категорії"""
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Будь ласка, спочатку налаштуйте бота командою /start")
            return
        
        category_name = update.message.text.strip()
        context.user_data['new_category_name'] = category_name
        
        # Додаємо нову категорію
        from database.db_operations import add_category
        category = add_category(user.id, category_name)
        
        await update.message.reply_text(f"✅ Категорію '{category_name}' додано!")
        
        # Очищаємо дані категорії
        context.user_data.pop('new_category_name', None)
    except Exception as e:
        logger.error(f"Error handling category creation input: {str(e)}")
        await update.message.reply_text("Виникла помилка при додаванні категорії.")

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка вибору категорії з кнопок"""
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Будь ласка, спочатку налаштуйте бота командою /start")
            return
        
        query = update.callback_query
        await query.answer()
        
        category_id = query.data.split('_')[-1]
        context.user_data['category_id'] = category_id
        
        # Отримуємо назву категорії для підтвердження
        from database.db_operations import get_category_by_id
        category = get_category_by_id(category_id, user.id)
        
        if not category:
            await query.edit_message_text("❌ Категорію не знайдено.")
            return
        
        # Підтверджуємо вибір категорії
        await query.edit_message_text(
            f"✅ Ви обрали категорію: {category.name}\n\n"
            "Тепер введіть суму транзакції:"
        )
        
        context.user_data['awaiting_amount'] = True
    except Exception as e:
        logger.error(f"Error handling category selection: {str(e)}")
        await update.message.reply_text("Виникла помилка при обробці вибору категорії.")

async def handle_transaction_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка введення суми транзакції"""
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Будь ласка, спочатку налаштуйте бота командою /start")
            return
        
        amount_text = update.message.text.strip().replace(',', '.')
        if not re.match(r'^\d+(\.\d{1,2})?$', amount_text):
            await update.message.reply_text("❌ Введіть коректну суму (наприклад, 150.50)")
            return
        
        amount = float(amount_text)
        context.user_data['transaction_amount'] = amount
        context.user_data.pop('awaiting_amount', None)
        # Тут можна одразу додати транзакцію або запросити опис, якщо потрібно
        # Додаємо транзакцію з категорією та сумою
        from database.db_operations import add_transaction
        from database.models import Transaction
        transaction = Transaction(
            user_id=user.id,
            amount=amount,
            type=context.user_data.get('transaction_type', 'expense'),
            category_id=int(context.user_data.get('category_id')) if context.user_data.get('category_id') else None
        )
        add_transaction(transaction)
        await update.message.reply_text(f"✅ Транзакцію додано!\nСума: {amount} грн")
        # Очищаємо user_data
        context.user_data.pop('transaction_type', None)
        context.user_data.pop('category_id', None)
        context.user_data.pop('transaction_amount', None)
        return
    except Exception as e:
        await update.message.reply_text("❌ Введіть коректну суму (наприклад, 150.50)")
        return