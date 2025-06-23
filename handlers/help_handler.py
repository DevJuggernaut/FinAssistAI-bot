"""
Модуль допомоги для бота FinAssist.
MVP версія з часто поставленими питаннями, контактами та інформацією про бота.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging

logger = logging.getLogger(__name__)

# ==================== ГОЛОВНЕ МЕНЮ ДОПОМОГИ ====================

async def show_help_menu(query, context):
    """Показує головне меню допомоги"""
    try:
        keyboard = [
            [
                InlineKeyboardButton("📋 Часті питання (FAQ)", callback_data="help_faq")
            ],
            [
                InlineKeyboardButton("📞 Контакти", callback_data="help_contacts"),
                InlineKeyboardButton("ℹ️ Про бота", callback_data="help_about")
            ],
            [
                InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")
            ]
        ]
        
        text = (
            "❓ **Допомога FinAssist**\n\n"
            "Вітаємо в розділі допомоги! Тут ви знайдете відповіді на найпоширеніші питання.\n\n"
            "📋 *Часті питання* — відповіді на основні питання\n"
            "📞 *Контакти* — як зв'язатися з підтримкою\n"
            "ℹ️ *Про бота* — інформація про можливості та версію\n\n"
            "💡 *Підказка:* Більшість питань можна знайти в FAQ"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_help_menu: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні меню допомоги",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Головне меню", callback_data="back_to_main")]
            ])
        )

# ==================== ЧАСТІ ПИТАННЯ (FAQ) ====================

async def show_faq_menu(query, context):
    """Показує меню часто поставлених питань"""
    try:
        keyboard = [
            [
                InlineKeyboardButton("💳 Як додати транзакцію?", callback_data="faq_add_transaction")
            ],
            [
                InlineKeyboardButton("📄 Як завантажити виписку?", callback_data="faq_upload_statement")
            ],
            [
                InlineKeyboardButton("🏷️ Як змінити категорію?", callback_data="faq_change_category")
            ],
            [
                InlineKeyboardButton("📤 Як експортувати дані?", callback_data="faq_export_data")
            ],
            [
                InlineKeyboardButton("🗑️ Як видалити всі дані?", callback_data="faq_clear_data")
            ],
            [
                InlineKeyboardButton("📎 Які формати підтримуються?", callback_data="faq_file_formats")
            ],
            [
                InlineKeyboardButton("🔙 Назад до допомоги", callback_data="help_menu")
            ]
        ]
        
        text = (
            "📋 **Часті питання (FAQ)**\n\n"
            "Оберіть питання, яке вас цікавить:\n\n"
            "💡 *Не знайшли відповідь?* Зверніться до розділу \"Контакти\""
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_faq_menu: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні FAQ",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="help_menu")]
            ])
        )

# ==================== ВІДПОВІДІ НА ПИТАННЯ ====================

async def show_faq_add_transaction(query, context):
    """Як додати транзакцію"""
    text = (
        "💳 **Як додати транзакцію?**\n\n"
        "**Крок 1:** Натисніть \"💳 Додати транзакцію\" в головному меню\n\n"
        "**Крок 2:** Оберіть тип операції:\n"
        "• ➖ Витрата — для покупок, оплат\n"
        "• ➕ Дохід — для зарплати, надходжень\n\n"
        "**Крок 3:** Вкажіть суму (наприклад: 1500)\n\n"
        "**Крок 4:** Оберіть категорію зі списку\n\n"
        "**Крок 5:** Додайте опис (необов'язково)\n\n"
        "**Готово!** Транзакція збережена 📊\n\n"
        "💡 *Підказка:* Можна також завантажити банківську виписку для автоматичного додавання операцій"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад до FAQ", callback_data="help_faq")]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_faq_upload_statement(query, context):
    """Як завантажити банківську виписку"""
    text = (
        "📄 **Як завантажити банківську виписку?**\n\n"
        "**Крок 1:** В меню \"💳 Додати транзакцію\" оберіть \"📄 Завантажити виписку\"\n\n"
        "**Крок 2:** Оберіть тип файлу:\n"
        "• PDF — виписка з банку у форматі PDF\n"
        "• Excel — таблиця з операціями\n"
        "• CSV — файл з даними через кому\n\n"
        "**Крок 3:** Завантажте файл відповідно до інструкцій\n\n"
        "**Крок 4:** Бот автоматично розпізнає операції\n\n"
        "**Крок 5:** Перевірте та підтвердіть імпорт\n\n"
        "⚠️ *Важливо:* Переконайтеся, що файл містить дату, суму та опис операцій"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад до FAQ", callback_data="help_faq")]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_faq_change_category(query, context):
    """Як змінити категорію операції"""
    text = (
        "🏷️ **Як змінити категорію операції?**\n\n"
        "**Варіант 1 - Для нових операцій:**\n"
        "• При додаванні транзакції просто оберіть потрібну категорію зі списку\n\n"
        "**Варіант 2 - Додати нову категорію:**\n"
        "• Перейдіть в \"⚙️ Налаштування\" → \"🏷️ Категорії\"\n"
        "• Натисніть \"➕ Додати категорію\"\n"
        "• Оберіть тип (дохід/витрата) та введіть назву\n\n"
        "**Варіант 3 - Видалити категорію:**\n"
        "• В налаштуваннях категорій оберіть \"🗑️ Видалити категорію\"\n"
        "• Виберіть категорію для видалення\n\n"
        "⚠️ *Важливо:* Системні категорії не можна видаляти"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад до FAQ", callback_data="help_faq")]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_faq_export_data(query, context):
    """Як експортувати дані"""
    text = (
        "📤 **Як експортувати мої дані?**\n\n"
        "**Крок 1:** Перейдіть в \"⚙️ Налаштування\"\n\n"
        "**Крок 2:** Оберіть \"📤 Експорт даних\"\n\n"
        "**Крок 3:** Натисніть \"📊 Експорт в CSV\"\n\n"
        "**Крок 4:** Дочекайтеся генерації файлу\n\n"
        "**Крок 5:** Завантажте файл, який бот надішле в чат\n\n"
        "**Що буде в файлі:**\n"
        "• Всі ваші транзакції\n"
        "• Дата, сума, категорія, опис\n"
        "• Формат CSV для Excel\n\n"
        "💡 *Підказка:* Файл можна відкрити в Excel або Google Sheets"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад до FAQ", callback_data="help_faq")]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_faq_clear_data(query, context):
    """Як видалити всі дані"""
    text = (
        "🗑️ **Як видалити всі дані?**\n\n"
        "**Крок 1:** Перейдіть в \"⚙️ Налаштування\"\n\n"
        "**Крок 2:** Оберіть \"🗑️ Очистити дані\"\n\n"
        "**Крок 3:** Уважно прочитайте попередження\n\n"
        "**Крок 4:** Натисніть \"🗑️ Видалити всі транзакції\"\n\n"
        "**Крок 5:** Підтвердіть дію другий раз\n\n"
        "**Що буде видалено:**\n"
        "• Всі ваші транзакції\n"
        "• Історія операцій\n\n"
        "**Що залишиться:**\n"
        "• Ваші категорії\n"
        "• Налаштування профілю\n\n"
        "⚠️ **УВАГА:** Ця дія незворотна! Зробіть експорт даних перед видаленням!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад до FAQ", callback_data="help_faq")]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_faq_file_formats(query, context):
    """Які формати файлів підтримуються"""
    text = (
        "📎 **Які формати файлів підтримуються?**\n\n"
        "**📄 PDF файли:**\n"
        "• Банківські виписки\n"
        "• Чеки та квитанції\n"
        "• Звіти з інтернет-банкінгу\n\n"
        "**📊 Excel файли (.xlsx, .xls):**\n"
        "• Таблиці з транзакціями\n"
        "• Експорт з банківських додатків\n"
        "• Ручні облікові таблиці\n\n"
        "**📋 CSV файли (.csv):**\n"
        "• Дані розділені комами\n"
        "• Експорт з фінансових сервісів\n"
        "• Прості текстові списки операцій\n\n"
        "**Вимоги до файлів:**\n"
        "• Максимальний розмір: 10 МБ\n"
        "• Повинні містити дату, суму, опис\n"
        "• Текст українською або англійською"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад до FAQ", callback_data="help_faq")]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ==================== КОНТАКТИ ====================

async def show_contacts(query, context):
    """Показує контактну інформацію"""
    try:
        text = (
            "📞 **Контакти для зв'язку**\n\n"
            "**📧 Email підтримки:**\n"
            "`finassist.support@gmail.com`\n"
            "💬 Для детальних питань, скарг та пропозицій\n"
            "⏱️ Час відповіді: 24-48 годин\n\n"
            "**💬 Telegram підтримка:**\n"
            "`@finassist_support`\n"
            "💬 Для швидких питань та технічної підтримки\n"
            "⏱️ Час відповіді: 2-6 годин (робочий час)\n\n"
            "**📝 Як написати:**\n"
            "1. Опишіть проблему детально\n"
            "2. Вкажіть, що ви робили перед помилкою\n"
            "3. Прикріпіть скріншот, якщо можливо\n\n"
            "**⏰ Робочий час підтримки:**\n"
            "Пн-Пт: 09:00 - 18:00 (Київський час)\n"
            "Сб-Нд: 10:00 - 16:00 (тільки критичні питання)"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📧 Написати email", url="mailto:finassist.support@gmail.com"),
                InlineKeyboardButton("💬 Telegram", url="https://t.me/finassist_support")
            ],
            [
                InlineKeyboardButton("🔙 Назад до допомоги", callback_data="help_menu")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_contacts: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні контактів",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="help_menu")]
            ])
        )

# ==================== ПРО БОТА ====================

async def show_about_bot(query, context):
    """Показує інформацію про бота"""
    try:
        text = (
            "ℹ️ **Про бота FinAssist**\n\n"
            "**🤖 Версія бота:** `v2.1.0 MVP`\n"
            "**📅 Дата останнього оновлення:** 26 травня 2025\n\n"
            "**🎯 Основні можливості:**\n\n"
            "**💳 Управління транзакціями:**\n"
            "• Додавання доходів та витрат\n"
            "• Імпорт банківських виписок\n"
            "• Автоматична категоризація\n\n"
            "**📊 Аналітика та звіти:**\n"
            "• Статистика по категоріях\n"
            "• Графіки та діаграми\n"
            "• Порівняння періодів\n\n"
            "**💰 Управління бюджетом:**\n"
            "• Планування місячного бюджету\n"
            "• Відстеження витрат\n"
            "• Фінансові поради\n\n"
            "**⚙️ Налаштування:**\n"
            "• Категорії\n"
            "• Вибір валюти\n"
            "• Експорт та очищення даних\n\n"
            "**🔒 Безпека:**\n"
            "• Всі дані зберігаються локально\n"
            "• Шифрування персональної інформації\n"
            "• Відповідність GDPR"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📋 Що нового в версії", callback_data="about_changelog"),
                InlineKeyboardButton("🛡️ Конфіденційність", callback_data="about_privacy")
            ],
            [
                InlineKeyboardButton("🔙 Назад до допомоги", callback_data="help_menu")
            ]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_about_bot: {str(e)}")
        await query.edit_message_text(
            "❌ Помилка при завантаженні інформації",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="help_menu")]
            ])
        )

async def show_changelog(query, context):
    """Показує список змін в поточній версії"""
    text = (
        "📋 **Що нового в версії v2.1.0**\n\n"
        "**✨ Нові функції:**\n\n"
        "**⚙️ MVP Налаштування:**\n"
        "• Категорії (додавання/видалення)\n"
        "• Налаштування основної валюти\n"
        "• Експорт даних в CSV формат\n"
        "• Очищення всіх транзакцій\n\n"
        "**❓ Система допомоги:**\n"
        "• Часті питання (FAQ)\n"
        "• Контакти підтримки\n"
        "• Детальна інформація про бота\n\n"
        "**🔧 Покращення:**\n"
        "• Оптимізоване головне меню\n"
        "• Швидша навігація між розділами\n"
        "• Кращі повідомлення про помилки\n"
        "• Підвищена стабільність роботи\n\n"
        "**📅 Попередні версії:**\n"
        "• v2.0.0 - Система бюджетування\n"
        "• v1.9.0 - Розширена аналітика\n"
        "• v1.8.0 - Імпорт банківських виписок"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад до \"Про бота\"", callback_data="help_about")]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_privacy_policy(query, context):
    """Показує політику конфіденційності"""
    text = (
        "🛡️ **Політика конфіденційності**\n\n"
        "**🔒 Збір даних:**\n"
        "• Зберігаємо тільки фінансові операції, які ви додаєте\n"
        "• Telegram ID для ідентифікації\n"
        "• Налаштування профілю (валюта, категорії)\n\n"
        "**📊 Використання даних:**\n"
        "• Тільки для показу вашої статистики\n"
        "• Не передаємо третім особам\n"
        "• Не використовуємо для реклами\n\n"
        "**🔐 Безпека:**\n"
        "• Всі дані зберігаються в захищеній базі\n"
        "• Регулярні резервні копії\n"
        "• Шифрування чутливої інформації\n\n"
        "**✋ Ваші права:**\n"
        "• Експорт всіх ваших даних\n"
        "• Повне видалення профілю\n"
        "• Зміна налаштувань конфіденційності\n\n"
        "**📞 Питання з приватності:**\n"
        "Напишіть на: `privacy@finassist.support`"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад до \"Про бота\"", callback_data="help_about")]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
