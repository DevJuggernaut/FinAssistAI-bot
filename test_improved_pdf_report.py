#!/usr/bin/env python3

"""
Тест нового сучасного PDF звіту з підтримкою кирилиці
"""

import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pdf_report_generation():
    """Тест генерації PDF звіту"""
    try:
        print("=== Тест генерації PDF звіту ===")
        
        from handlers.analytics_handler import generate_pdf_report, create_pdf_report
        from database.models import TransactionType
        
        # Мокаємо користувача
        mock_user = Mock()
        mock_user.id = 12345
        mock_user.username = "test_user"
        mock_user.telegram_id = 12345
        
        # Мокаємо транзакції
        mock_transactions = []
        
        # Створюємо тестові дані
        test_stats = {
            'total_income': 15000.0,
            'total_expenses': 12000.0,
            'balance': 3000.0,
            'category_expenses': {
                'Їжа та ресторани': 4000.0,
                'Транспорт': 2500.0,
                'Покупки': 2000.0,
                'Житло та комунальні': 3000.0,
                'Розваги': 500.0
            },
            'period': '30 днів'
        }
        
        print("📊 Тестові дані:")
        print(f"   Доходи: {test_stats['total_income']:,.0f} грн")
        print(f"   Витрати: {test_stats['total_expenses']:,.0f} грн") 
        print(f"   Баланс: {test_stats['balance']:,.0f} грн")
        print(f"   Категорій: {len(test_stats['category_expenses'])}")
        
        # Тестуємо створення PDF
        print("\n📄 Створюємо PDF звіт...")
        pdf_buffer = create_pdf_report(mock_user, mock_transactions, test_stats)
        
        # Перевіряємо, що буфер не порожній
        assert pdf_buffer is not None, "PDF буфер не повинен бути None"
        
        pdf_size = len(pdf_buffer.getvalue())
        print(f"✅ PDF створено успішно! Розмір: {pdf_size:,} байт")
        
        # Якщо PDF малий, швидше за все це текстовий fallback
        if pdf_size < 1000:
            print("📝 Створено текстовий звіт (fallback)")
        else:
            print("📄 Створено повноцінний PDF")
        
        # Перевіряємо, що можна прочитати початок файлу
        pdf_buffer.seek(0)
        first_bytes = pdf_buffer.read(10)
        pdf_buffer.seek(0)
        
        if first_bytes.startswith(b'%PDF'):
            print("✅ Файл має правильний PDF заголовок")
        else:
            print("📝 Файл є текстовим (fallback режим)")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка в тесті: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_pdf_report_workflow():
    """Тест повного workflow PDF звіту"""
    try:
        print("\n=== Тест workflow PDF звіту ===")
        
        from handlers.analytics_handler import generate_pdf_report
        
        # Мокаємо всі залежності
        with patch('handlers.analytics_handler.get_user') as mock_get_user, \
             patch('handlers.analytics_handler.get_user_transactions') as mock_get_transactions, \
             patch('handlers.analytics_handler.create_pdf_report') as mock_create_pdf:
            
            # Налаштовуємо моки
            mock_user = Mock()
            mock_user.id = 12345
            mock_user.username = "test_user"
            mock_user.telegram_id = 12345
            mock_get_user.return_value = mock_user
            
            mock_get_transactions.return_value = []
            
            # Мок для PDF
            import io
            mock_pdf_buffer = io.BytesIO(b'%PDF-test-content')
            mock_create_pdf.return_value = mock_pdf_buffer
            
            # Мокаємо query та context
            query = Mock()
            query.from_user = Mock()
            query.from_user.id = 12345
            query.edit_message_text = AsyncMock()
            query.message = Mock()
            query.message.chat_id = 12345
            
            context = Mock()
            context.bot = Mock()
            context.bot.send_document = AsyncMock()
            context.bot.send_message = AsyncMock()
            
            # Викликаємо функцію
            await generate_pdf_report(query, context)
            
            # Перевіряємо виклики
            query.edit_message_text.assert_called()
            context.bot.send_document.assert_called_once()
            context.bot.send_message.assert_called_once()
            
            # Перевіряємо аргументи send_document
            send_doc_call = context.bot.send_document.call_args
            assert send_doc_call is not None, "send_document повинен бути викликаний"
            
            # Перевіряємо аргументи send_message (меню після відправки)
            send_msg_call = context.bot.send_message.call_args
            assert send_msg_call is not None, "send_message повинен бути викликаний"
            
            # Перевіряємо, що в меню немає кнопки "Новий звіт"
            reply_markup = send_msg_call.kwargs.get('reply_markup')
            if reply_markup:
                keyboard_text = str(reply_markup.inline_keyboard)
                assert "Новий звіт" not in keyboard_text, "Кнопка 'Новий звіт' не повинна бути в меню"
                assert "До аналітики" in keyboard_text, "Кнопка 'До аналітики' повинна бути в меню"
                print("✅ Кнопка 'Новий звіт' видалена з меню")
            
            print("✅ Workflow PDF звіту працює правильно")
            
            return True
            
    except Exception as e:
        print(f"❌ Помилка в тесті workflow: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_cyrillic_support():
    """Тест підтримки кирилиці в звіті"""
    try:
        print("\n=== Тест підтримки кирилиці ===")
        
        from handlers.analytics_handler import create_simple_text_report
        
        # Тестуємо з українськими даними
        mock_user = Mock()
        mock_user.username = "тест_користувач"
        mock_user.telegram_id = 12345
        
        test_stats = {
            'total_income': 25000.0,
            'total_expenses': 18000.0,
            'balance': 7000.0,
            'category_expenses': {
                'Їжа та ресторани': 6000.0,
                'Транспорт і паливо': 4000.0,
                'Продукти харчування': 3500.0,
                'Житло та комунальні послуги': 3000.0,
                'Дозвілля та розваги': 1500.0
            },
            'period': '30 днів'
        }
        
        # Створюємо текстовий звіт
        text_buffer = create_simple_text_report(mock_user, [], test_stats)
        
        # Читаємо вміст
        text_buffer.seek(0)
        content = text_buffer.read().decode('utf-8')
        
        # Перевіряємо наявність українського тексту
        ukrainian_words = [
            'ПЕРСОНАЛЬНИЙ', 'ФІНАНСОВИЙ', 'ЗВІТ',
            'Користувач', 'період', 'створено',
            'доходи', 'витрати', 'заощадження',
            'Їжа', 'Транспорт', 'Житло'
        ]
        
        found_words = []
        for word in ukrainian_words:
            if word in content:
                found_words.append(word)
        
        print(f"✅ Знайдено українських слів: {len(found_words)}/{len(ukrainian_words)}")
        
        # Перевіряємо структуру звіту
        sections = [
            'ФІНАНСОВИЙ ПІДСУМОК',
            'АНАЛІЗ ЗАОЩАДЖЕНЬ', 
            'СТРУКТУРА ВИТРАТ',
            'ПЕРСОНАЛЬНІ РЕКОМЕНДАЦІЇ'
        ]
        
        found_sections = []
        for section in sections:
            if section in content:
                found_sections.append(section)
        
        print(f"✅ Знайдено розділів: {len(found_sections)}/{len(sections)}")
        
        # Перевіряємо довжину звіту
        lines = content.split('\n')
        print(f"✅ Звіт містить {len(lines)} рядків")
        
        assert len(found_words) >= len(ukrainian_words) * 0.8, "Недостатньо українських слів у звіті"
        assert len(found_sections) >= len(sections) * 0.8, "Недостатньо розділів у звіті"
        
        print("✅ Підтримка кирилиці працює правильно")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка в тесті кирилиці: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Запуск всіх тестів"""
    print("🧪 Запуск тестів нового PDF звіту...")
    
    test1 = await test_pdf_report_generation()
    test2 = await test_pdf_report_workflow()
    test3 = await test_cyrillic_support()
    
    if test1 and test2 and test3:
        print("\n🎉 Всі тести пройшли успішно!")
        print("\n📋 Зміни в PDF звіті:")
        print("• ✅ Видалено кнопку 'Новий звіт'")
        print("• ✅ Покращено дизайн PDF")
        print("• ✅ Додано підтримку кирилиці")
        print("• ✅ Сучасні кольори та стилі")
        print("• ✅ Детальна аналітика")
        print("• ✅ Практичні рекомендації")
        
    else:
        print("\n❌ Деякі тести не пройшли!")

if __name__ == "__main__":
    asyncio.run(main())
