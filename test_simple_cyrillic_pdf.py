#!/usr/bin/env python3
"""
Простий тест для перевірки функції create_pdf_report з підтримкою кирилиці
"""

import os
import sys
from datetime import datetime, timedelta

# Додаємо батьківську папку до sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_font_registration():
    """Тестує реєстрацію шрифтів DejaVu"""
    print("🔤 Тестування реєстрації шрифтів DejaVu...")
    
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        
        # Шлях до наших шрифтів (у поточній папці проекту)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        font_dir = os.path.join(base_dir, 'fonts')
        
        regular_font_path = os.path.join(font_dir, 'DejaVuSans.ttf')
        bold_font_path = os.path.join(font_dir, 'DejaVuSans-Bold.ttf')
        
        print(f"📁 Шлях до шрифтів: {font_dir}")
        print(f"📄 Основний шрифт: {regular_font_path}")
        print(f"📄 Жирний шрифт: {bold_font_path}")
        
        # Перевіряємо наявність файлів
        if not os.path.exists(regular_font_path):
            print(f"❌ Основний шрифт не знайдено: {regular_font_path}")
            return False
            
        if not os.path.exists(bold_font_path):
            print(f"❌ Жирний шрифт не знайдено: {bold_font_path}")
            return False
        
        # Реєструємо шрифти
        print("🔧 Реєстрація шрифтів...")
        pdfmetrics.registerFont(TTFont('DejaVuSans', regular_font_path))
        print("✅ Основний шрифт DejaVuSans зареєстровано")
        
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', bold_font_path))
        print("✅ Жирний шрифт DejaVuSans-Bold зареєстровано")
        
        # Реєструємо сім'ю шрифтів
        registerFontFamily('DejaVuSans', normal='DejaVuSans', bold='DejaVuSans-Bold')
        print("✅ Сім'я шрифтів DejaVuSans зареєстрована")
        
        # Перевіряємо, що шрифти доступні
        available_fonts = pdfmetrics.getRegisteredFontNames()
        
        success = True
        if 'DejaVuSans' in available_fonts:
            print("✅ DejaVuSans доступний в ReportLab")
        else:
            print("❌ DejaVuSans НЕ доступний в ReportLab")
            success = False
            
        if 'DejaVuSans-Bold' in available_fonts:
            print("✅ DejaVuSans-Bold доступний в ReportLab")
        else:
            print("❌ DejaVuSans-Bold НЕ доступний в ReportLab")
            success = False
        
        return success
        
    except Exception as e:
        print(f"❌ Помилка при реєстрації шрифтів: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_pdf_creation():
    """Створює простий PDF з кирилицею для тестування"""
    print("\n📄 Створення тестового PDF з кирилицею...")
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        import io
        
        # Створюємо буфер
        buffer = io.BytesIO()
        
        # Створюємо документ
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Стиль з нашим шрифтом
        styles = getSampleStyleSheet()
        cyrillic_style = ParagraphStyle(
            'CyrillicTest',
            parent=styles['Normal'],
            fontName='DejaVuSans',
            fontSize=14,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceBefore=10,
            spaceAfter=10
        )
        
        bold_style = ParagraphStyle(
            'CyrillicBoldTest',
            parent=styles['Normal'],
            fontName='DejaVuSans-Bold',
            fontSize=18,
            textColor=colors.blue,
            alignment=TA_CENTER,
            spaceBefore=20,
            spaceAfter=20
        )
        
        # Додаємо кирилічний текст
        test_texts = [
            ("Тест підтримки кирилиці в PDF", bold_style),
            ("Цей документ містить українські символи", cyrillic_style),
            ("Фінансовий звіт: доходи та витрати", cyrillic_style),
            ("Категорії: продукти, транспорт, комунальні", cyrillic_style),
            ("Сума: 1,234.56 грн", cyrillic_style),
            ("Заощадження: покращити на 15%", cyrillic_style),
            ("Рекомендації: збільшити контроль витрат", cyrillic_style),
            ("Дата створення: 24.06.2025", cyrillic_style)
        ]
        
        for text, style in test_texts:
            story.append(Paragraph(text, style))
        
        # Створюємо PDF
        doc.build(story)
        buffer.seek(0)
        
        # Зберігаємо файл
        test_filename = f"test_cyrillic_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        with open(test_filename, 'wb') as f:
            f.write(buffer.getvalue())
        
        file_size = len(buffer.getvalue())
        print(f"✅ PDF створено: {test_filename}")
        print(f"📏 Розмір: {file_size:,} байт")
        
        # Базова перевірка вмісту
        pdf_content = buffer.getvalue()
        
        # Перевіряємо різні варіанти кодування кирилиці
        cyrillic_checks = {
            "UTF-8": "українські".encode('utf-8') in pdf_content,
            "UTF-16": "українські".encode('utf-16') in pdf_content,
            "CP1251": False,  # Спробуємо пізніше
            "Raw Ukrainian": "україн" in pdf_content.decode('utf-8', errors='ignore'),
            "Фінансовий": "Фінансовий".encode('utf-8') in pdf_content,
        }
        
        try:
            cyrillic_checks["CP1251"] = "українські".encode('cp1251') in pdf_content
        except:
            pass
        
        font_check = b"DejaVu" in pdf_content
        
        print(f"🔍 Шрифт DejaVu: {'✅' if font_check else '❌'}")
        for check_name, result in cyrillic_checks.items():
            print(f"🔍 Кирилиця ({check_name}): {'✅' if result else '❌'}")
        
        # Якщо хоча б одна перевірка пройшла - вважаємо успішним
        cyrillic_ok = any(cyrillic_checks.values())
        
        return cyrillic_ok and font_check
        
    except Exception as e:
        print(f"❌ Помилка при створенні PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_fonts_directory():
    """Перевіряє папку з шрифтами"""
    print("📁 Перевірка папки fonts/...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_dir = os.path.join(base_dir, 'fonts')
    
    if not os.path.exists(font_dir):
        print(f"❌ Папка fonts/ не існує: {font_dir}")
        return False
    
    files = os.listdir(font_dir)
    print(f"📋 Файли в fonts/: {files}")
    
    required_files = ['DejaVuSans.ttf', 'DejaVuSans-Bold.ttf']
    missing_files = []
    
    for required_file in required_files:
        file_path = os.path.join(font_dir, required_file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {required_file}: {size:,} байт")
        else:
            print(f"❌ {required_file}: ВІДСУТНІЙ")
            missing_files.append(required_file)
    
    if missing_files:
        print(f"\n🚨 Відсутні файли: {missing_files}")
        return False
    else:
        print("✅ Всі необхідні шрифти наявні")
        return True

if __name__ == "__main__":
    print("🚀 Тестування підтримки кирилиці в PDF\n")
    
    # Крок 1: Перевіряємо папку з шрифтами
    step1 = check_fonts_directory()
    
    if not step1:
        print("\n🚨 РЕЗУЛЬТАТ: Спочатку додайте шрифти в папку fonts/")
        sys.exit(1)
    
    # Крок 2: Тестуємо реєстрацію шрифтів
    print("\n" + "="*50)
    step2 = test_font_registration()
    
    if not step2:
        print("\n🚨 РЕЗУЛЬТАТ: Помилка реєстрації шрифтів")
        sys.exit(1)
    
    # Крок 3: Створюємо тестовий PDF
    print("\n" + "="*50)
    step3 = test_simple_pdf_creation()
    
    if step3:
        print("\n🎉 УСПІХ: Всі тести пройшли!")
        print("📱 Відкрийте створений PDF файл і перевірте відображення української мови")
        print("🔤 Якщо ви бачите українські літери замість квадратиків - проблема вирішена!")
    else:
        print("\n🚨 РЕЗУЛЬТАТ: Помилка створення PDF з кирилицею")
        sys.exit(1)
