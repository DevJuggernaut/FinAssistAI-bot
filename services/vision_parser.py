import os
import logging
import base64
from openai import OpenAI
from PIL import Image
import io
from datetime import datetime
import json
import re

from database.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Ініціалізація клієнта OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

class VisionReceiptParser:
    """
    Клас для розпізнавання чеків з використанням GPT-4 Vision
    """
    
    def __init__(self):
        self.client = client
    
    def _encode_image(self, image_path):
        """Кодує зображення для API"""
        try:
            # Відкриття і оптимізація зображення
            with Image.open(image_path) as img:
                # Змінюємо розмір зображення, якщо воно завелике
                max_size = 4000  # Максимальний розмір для GPT-4 Vision
                if img.width > max_size or img.height > max_size:
                    ratio = min(max_size/img.width, max_size/img.height)
                    new_width = int(img.width * ratio)
                    new_height = int(img.height * ratio)
                    img = img.resize((new_width, new_height))
                
                # Перетворюємо в RGB, якщо потрібно (для PNG з прозорістю)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                
                # Зберігаємо в буфер з оптимізованою якістю
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85, optimize=True)
                buffer.seek(0)
                
                # Кодуємо у base64
                encoded_string = base64.b64encode(buffer.getvalue()).decode("utf-8")
                return encoded_string
        except Exception as e:
            logger.error(f"Помилка при кодуванні зображення: {e}")
            return None
    
    def parse_receipt(self, image_path):
        """
        Розпізнає чек з фотографії за допомогою GPT-4 Vision
        
        Args:
            image_path (str): Шлях до зображення чека
            
        Returns:
            dict: Структуровані дані з чека або None у разі помилки
        """
        try:
            # Перевіряємо існування файлу
            if not os.path.exists(image_path):
                logger.error(f"Файл не існує: {image_path}")
                return None
            
            # Кодуємо зображення
            encoded_image = self._encode_image(image_path)
            if not encoded_image:
                return None
                
            # Формуємо запит до GPT-4 Vision
            prompt = """
            Проаналізуйте зображення чека та витягніть з нього наступну інформацію у форматі JSON:
            {
                "store_name": "Назва магазину/закладу",
                "date": "Дата покупки у форматі YYYY-MM-DD",
                "time": "Час покупки у форматі HH:MM (якщо вказано)",
                "total_amount": числове значення загальної суми,
                "currency": "Валюта (UAH за замовчуванням)",
                "items": [
                    {
                        "name": "Назва товару/послуги",
                        "quantity": числова кількість (якщо вказано),
                        "price": числова ціна,
                        "amount": числова сума (кількість * ціна)
                    },
                    ...
                ],
                "payment_method": "Спосіб оплати (якщо вказано)",
                "tax_info": "Податкова інформація (якщо вказана)"
            }
            
            Важливі правила:
            1. Якщо певної інформації немає на чеку, встановіть порожній рядок "" або null для цього поля.
            2. Для числових полів використовуйте числа без лапок. Наприклад: "total_amount": 250.50
            3. Будьте точні при читанні загальної суми. Шукайте слова "СУМА", "ВСЬОГО", "TOTAL", "ИТОГО", "СУМА ДО СПЛАТИ", "БЕЗГОТІВКОВА" тощо.
            4. Для списку товарів (items) витягніть скільки можливо позицій, але не вигадуйте.
            5. Особлива увага до чеків MIDA/МІДА - вони мають характерний формат з АРТ.№ та іншими маркерами.
            6. Для MIDA шукайте товари за шаблоном: АРТ.№ [номер] [кількість]/[назва товару] [ціна]
            7. Формат відповіді: лише чистий JSON, БЕЗ додаткового тексту.
            """
            
            # Виклик API
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                        ]
                    }
                ],
                max_tokens=1500
            )
            
            # Отримуємо відповідь у вигляді тексту
            result_text = response.choices[0].message.content.strip()
            
            # Видаляємо все, що не є JSON (можливо, GPT додав пояснення)
            json_pattern = r'\{[\s\S]*\}'
            json_match = re.search(json_pattern, result_text)
            
            if json_match:
                result_text = json_match.group(0)
            
            # Перетворюємо текст на JSON
            result_json = json.loads(result_text)
            
            # Обробляємо дату
            if result_json.get("date"):
                try:
                    result_json["date"] = datetime.strptime(result_json["date"], "%Y-%m-%d")
                except ValueError:
                    # Якщо не вдалося розпізнати дату, використовуємо поточну
                    logger.warning("Не вдалося розпізнати дату, використовуємо поточну")
                    result_json["date"] = datetime.now()
            else:
                result_json["date"] = datetime.now()
            
            # Забезпечуємо, що total_amount є числом
            if isinstance(result_json.get("total_amount"), str):
                try:
                    result_json["total_amount"] = float(result_json["total_amount"].replace(',', '.'))
                except ValueError:
                    result_json["total_amount"] = 0.0
            
            return result_json
            
        except Exception as e:
            logger.error(f"Помилка при розпізнаванні чека з GPT-4 Vision: {e}")
            return None
    
    def parse_bank_statement(self, pdf_path):
        """
        У цій версії заглушка для парсингу банківських виписок
        В повній реалізації потрібно використовувати інші бібліотеки для роботи з PDF
        і можливо API для розпізнавання тексту, таке як Azure Form Recognizer або подібне
        """
        logger.warning("Парсинг банківських виписок через Vision API не реалізований")
        return None
