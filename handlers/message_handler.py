import re
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from database.models import User, Transaction, TransactionType
from database.session import Session
from database.db_operations import (
    get_user,
    add_transaction,
    get_user_transactions,
    update_user_settings
)
from services.statement_parser import statement_parser, receipt_processor
from services.ml_categorizer import transaction_categorizer
from services.openai_service import openai_service
from services.analytics_service import analytics_service

# Налаштування логування
logger = logging.getLogger(__name__)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка текстових повідомлень"""
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("Будь ласка, спочатку налаштуйте бота командою /start")
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
        
        # Перевіряємо чи це транзакція у форматі "сума опис"
        match = re.match(r'^(\d+(?:\.\d+)?)\s+(.+)$', update.message.text)
        if match:
            amount = float(match.group(1))
            description = match.group(2)
            
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
        
        # Обробляємо чек
        receipt_data = receipt_processor.process_receipt_image(file_path)
        
        # Категорізуємо транзакцію
        category, confidence = transaction_categorizer.predict_category(receipt_data['raw_text'])
        
        # Додаємо транзакцію
        transaction = {
            'user_id': user.id,
            'amount': receipt_data['total_amount'],
            'description': 'Receipt scan',
            'category': category,
            'type': 'expense',
            'date': receipt_data['date'],
            'source': 'receipt',
            'receipt_image': file_path
        }
        
        add_transaction(transaction)
        
        # Відправляємо підтвердження
        await update.message.reply_text(
            f"Чек оброблено!\n"
            f"Сума: {receipt_data['total_amount']}\n"
            f"Дата: {receipt_data['date'].strftime('%Y-%m-%d')}\n"
            f"Категорія: {category} (впевненість: {confidence:.2%})"
        )
    except Exception as e:
        logger.error(f"Error handling photo: {str(e)}")
        await update.message.reply_text("Виникла помилка при обробці чека.")

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
        if awaiting_file == 'pdf' and not file_name.endswith('.pdf'):
            await update.message.reply_text("❌ Очікується PDF файл")
            return
        elif awaiting_file == 'excel' and not (file_name.endswith('.xlsx') or file_name.endswith('.xls')):
            await update.message.reply_text("❌ Очікується Excel файл (.xlsx або .xls)")
            return
        elif awaiting_file == 'csv' and not file_name.endswith('.csv'):
            await update.message.reply_text("❌ Очікується CSV файл")
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
            
            # Обробляємо файл в залежності від типу
            from services.statement_parser import StatementParser
            parser = StatementParser()
            
            if awaiting_file == 'pdf':
                transactions = await parser.parse_pdf(file_path)
            elif awaiting_file == 'excel':
                transactions = await parser.parse_excel(file_path)
            elif awaiting_file == 'csv':
                transactions = await parser.parse_csv(file_path)
            else:
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
        text += "🔍 **Попередній перегляд:**\n\n"
        
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
        
        text += "📋 **Дії:**\n"
        text += "• Редагуйте транзакції перед додаванням\n"
        text += "• Виключіть непотрібні операції\n"
        text += "• Перевірте категорії та суми"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Додати всі", callback_data="import_all_transactions"),
                InlineKeyboardButton("✏️ Редагувати", callback_data="edit_transactions")
            ],
            [
                InlineKeyboardButton("🗑️ Виключити дублікати", callback_data="remove_duplicates"),
                InlineKeyboardButton("📅 Налаштувати період", callback_data="set_import_period")
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
        logger.error(f"Error in show_transactions_preview: {str(e)}")
        await message.edit_text("Помилка при відображенні попереднього перегляду.")