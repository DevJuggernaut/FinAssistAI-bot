import logging
from database.models import init_db, Category, Session

logger = logging.getLogger(__name__)
session = Session()

def setup_database():
    """
    Инициализирует базу данных и создает необходимые таблицы
    """
    try:
        logger.info("Инициализация базы данных...")
        init_db()
        logger.info("База данных успешно инициализирована")
        return True
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        return False

def create_default_categories():
    """
    Создает стандартные категории расходов в базе данных
    """
    try:
        default_categories = [
            # Категории расходов
            ("🏠 Жилье", "expense", "Аренда, коммунальные услуги, ремонт"),
            ("🍽️ Питание", "expense", "Продукты, рестораны, кафе"),
            ("🚗 Транспорт", "expense", "Общественный транспорт, такси, топливо"),
            ("👕 Одежда", "expense", "Одежда, обувь, аксессуары"),
            ("💊 Здоровье", "expense", "Лекарства, врачи, страховка"),
            ("📱 Связь", "expense", "Телефон, интернет, ТВ"),
            ("🎓 Образование", "expense", "Курсы, книги, тренинги"),
            ("🎭 Развлечения", "expense", "Кино, концерты, хобби"),
            ("💰 Сбережения", "expense", "Накопления, инвестиции"),
            ("🎁 Подарки", "expense", "Подарки, благотворительность"),
            ("💼 Работа", "expense", "Рабочие расходы, офисные принадлежности"),
            ("🏥 Страхование", "expense", "Все виды страхования"),
            ("📦 Покупки", "expense", "Электроника, бытовая техника"),
            ("🔄 Регулярные", "expense", "Подписки, членства"),
            ("⚡️ Другое", "expense", "Прочие расходы"),
            # Категории доходов
            ("💼 Зарплата", "income", "Основная зарплата и премии"),
            ("💰 Инвестиции", "income", "Доход от инвестиций"),
            ("🎁 Подарки", "income", "Полученные подарки и призы"),
            ("💼 Фриланс", "income", "Доход от подработки"),
            ("🏠 Аренда", "income", "Доход от сдачи в аренду"),
            ("⚡️ Другое", "income", "Прочие доходы")
        ]

        for name, type_, description in default_categories:
            # Проверяем, существует ли уже такая категория
            existing_category = session.query(Category).filter_by(name=name, type=type_).first()
            if not existing_category:
                category = Category(
                    name=name,
                    type=type_,
                    icon=name.split()[0],  # Используем эмодзи как иконку
                    is_default=True
                )
                session.add(category)
        
        session.commit()
        logger.info("Стандартные категории успешно созданы")
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании стандартных категорий: {e}")
        session.rollback()
        return False
