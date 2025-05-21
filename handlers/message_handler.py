import re
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє текстові повідомлення"""
    text = update.message.text
    
    # Спробуємо розпізнати опис транзакції та суму
    transaction_pattern = r"([а-яА-ЯёЁa-zA-Z\s]+)\s+(\d+(?:\.\d+)?)\s*(грн|₴)?"
    match = re.search(transaction_pattern, text, re.IGNORECASE)
    
    if match:
        description = match.group(1).strip()
        amount = float(match.group(2))
        
        # На цьому етапі просто виводимо розпізнану інформацію
        await update.message.reply_text(
            f"📝 Розпізнано транзакцію:\n"
            f"Опис: {description}\n"
            f"Сума: {amount} грн\n\n"
            f"В майбутньому тут буде запит на підтвердження та категорію."
        )
        
    else:
        await update.message.reply_text(
            "Не вдалося розпізнати транзакцію. Будь ласка, використовуйте формат:\n"
            "'Кава 45 грн' або 'Таксі 130'"
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє фотографії (чеки)"""
    await update.message.reply_text(
        "📸 Отримав фото! Почекайте, обробляю чек...\n"
        "Ця функція буде реалізована в наступних версіях."
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє документи (виписки)"""
    document = update.message.document
    file_name = document.file_name if document.file_name else "невідомий файл"
    
    await update.message.reply_text(
        f"📄 Отримав файл: {file_name}\n"
        "Обробка банківських виписок буде доступна в наступних версіях."
    )