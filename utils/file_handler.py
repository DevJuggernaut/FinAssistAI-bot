import os
import uuid
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Создаем директории для хранения данных
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
RECEIPTS_DIR = os.path.join(UPLOADS_DIR, 'receipts')
STATEMENTS_DIR = os.path.join(UPLOADS_DIR, 'statements')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')

# Создаем директории, если они не существуют
os.makedirs(RECEIPTS_DIR, exist_ok=True)
os.makedirs(STATEMENTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_unique_filename(original_filename=None, prefix=None):
    """
    Генерирует уникальное имя файла на основе времени и случайного UUID.
    
    Args:
        original_filename (str, optional): Исходное имя файла для сохранения расширения.
        prefix (str, optional): Префикс для имени файла.
    
    Returns:
        str: Уникальное имя файла
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    
    if prefix:
        filename = f"{prefix}_{timestamp}_{unique_id}"
    else:
        filename = f"{timestamp}_{unique_id}"
    
    if original_filename:
        ext = os.path.splitext(original_filename)[1]
        return f"{filename}{ext}"
    
    return filename

async def save_receipt_image(photo_file, user_id):
    """
    Сохраняет изображение чека.
    
    Args:
        photo_file: Объект фото из Telegram.
        user_id (int): ID пользователя.
    
    Returns:
        str: Путь к сохраненному файлу
    """
    try:
        # Создаем папку для пользователя, если ее нет
        user_dir = os.path.join(RECEIPTS_DIR, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Генерируем имя файла и путь
        filename = generate_unique_filename(prefix="receipt", original_filename="receipt.jpg")
        file_path = os.path.join(user_dir, filename)
        
        # Скачиваем и сохраняем файл
        await photo_file.download_to_drive(file_path)
        logger.info(f"Сохранено изображение чека: {file_path}")
        
        return file_path
    except Exception as e:
        logger.error(f"Ошибка при сохранении изображения чека: {e}")
        return None

async def save_bank_statement(document_file, user_id, original_filename):
    """
    Сохраняет файл банковской выписки.
    
    Args:
        document_file: Объект документа из Telegram.
        user_id (int): ID пользователя.
        original_filename (str): Исходное имя файла.
    
    Returns:
        str: Путь к сохраненному файлу
    """
    try:
        # Создаем папку для пользователя, если ее нет
        user_dir = os.path.join(STATEMENTS_DIR, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Генерируем имя файла и путь
        filename = generate_unique_filename(original_filename=original_filename, prefix="statement")
        file_path = os.path.join(user_dir, filename)
        
        # Скачиваем и сохраняем файл
        await document_file.download_to_drive(file_path)
        logger.info(f"Сохранен файл выписки: {file_path}")
        
        return file_path
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла выписки: {e}")
        return None

def cleanup_old_files(days=30):
    """
    Удаляет старые файлы из директорий uploads и reports.
    
    Args:
        days (int): Количество дней, после которых файлы считаются устаревшими.
    """
    try:
        now = datetime.now()
        cutoff = now.timestamp() - (days * 24 * 60 * 60)
        
        # Функция для проверки директории
        def check_directory(directory):
            if not os.path.exists(directory):
                return
                
            for item in os.listdir(directory):
                path = os.path.join(directory, item)
                
                # Если это папка, проверяем вложенные файлы
                if os.path.isdir(path):
                    check_directory(path)
                    
                    # Проверяем, пуста ли папка после удаления файлов
                    if not os.listdir(path):
                        try:
                            os.rmdir(path)
                            logger.info(f"Удалена пустая директория: {path}")
                        except Exception as e:
                            logger.error(f"Ошибка при удалении директории {path}: {e}")
                
                # Если это файл, проверяем его дату
                elif os.path.isfile(path):
                    file_mod_time = os.path.getmtime(path)
                    if file_mod_time < cutoff:
                        try:
                            os.remove(path)
                            logger.info(f"Удален устаревший файл: {path}")
                        except Exception as e:
                            logger.error(f"Ошибка при удалении файла {path}: {e}")
        
        # Проверяем директории
        check_directory(UPLOADS_DIR)
        check_directory(REPORTS_DIR)
        
        logger.info("Очистка устаревших файлов завершена")
    except Exception as e:
        logger.error(f"Ошибка при очистке устаревших файлов: {e}")
