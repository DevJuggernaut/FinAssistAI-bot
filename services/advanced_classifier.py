import numpy as np
import os
import pickle
import logging
from datetime import datetime
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from database.models import Session, Transaction, Category, User

logger = logging.getLogger(__name__)

# Шляхи до моделей
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'ml_models')
EXPENSE_MODEL_PATH = os.path.join(MODELS_DIR, 'advanced_expense_classifier.pkl')
INCOME_MODEL_PATH = os.path.join(MODELS_DIR, 'advanced_income_classifier.pkl')
VECTORIZER_PATH = os.path.join(MODELS_DIR, 'tfidf_vectorizer.pkl')

# Створюємо директорію для моделей
os.makedirs(MODELS_DIR, exist_ok=True)

class AdvancedTransactionClassifier:
    """Просунутий класифікатор транзакцій з використанням TF-IDF та RandomForest"""
    
    def __init__(self):
        self.expense_classifier = None
        self.income_classifier = None
        self.vectorizer = None
        self.load_or_train_models()
    
    def preprocess_text(self, text):
        """Попередня обробка тексту для класифікації"""
        if not text:
            return ""
            
        # Приводимо до нижнього регістру
        text = text.lower()
        
        # Видаляємо спеціальні символи, залишаючи букви та цифри
        text = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in text)
        
        # Видаляємо подвійні пробіли
        while '  ' in text:
            text = text.replace('  ', ' ')
            
        return text.strip()
    
    def load_or_train_models(self):
        """Завантаження існуючих моделей або навчання нових"""
        models_exist = (
            os.path.exists(EXPENSE_MODEL_PATH) and 
            os.path.exists(INCOME_MODEL_PATH) and 
            os.path.exists(VECTORIZER_PATH)
        )
        
        if models_exist:
            try:
                self.load_models()
                logger.info("Завантажено існуючі моделі класифікації транзакцій")
                return
            except Exception as e:
                logger.error(f"Помилка при завантаженні моделей: {e}")
        
        logger.info("Тренуємо нові моделі класифікації транзакцій...")
        self.train_models()
    
    def load_models(self):
        """Завантаження збережених моделей"""
        with open(EXPENSE_MODEL_PATH, 'rb') as f:
            self.expense_classifier = pickle.load(f)
            
        with open(INCOME_MODEL_PATH, 'rb') as f:
            self.income_classifier = pickle.load(f)
            
        with open(VECTORIZER_PATH, 'rb') as f:
            self.vectorizer = pickle.load(f)
    
    def train_models(self):
        """Навчання нових моделей з використанням даних з бази"""
        # Отримуємо дані з бази
        expense_data = self._get_training_data('expense')
        income_data = self._get_training_data('income')
        
        # Якщо даних недостатньо, використовуємо базові дані
        if len(expense_data) < 20:
            expense_data.extend(self._get_default_expense_data())
            
        if len(income_data) < 10:
            income_data.extend(self._get_default_income_data())
        
        # Створюємо один векторизатор для всіх даних
        all_descriptions = [desc for desc, _ in expense_data + income_data]
        self.vectorizer = TfidfVectorizer(
            analyzer='word',
            ngram_range=(1, 2),  # Використовуємо уніграми та біграми
            max_features=5000,
            min_df=2
        )
        self.vectorizer.fit(all_descriptions)
        
        # Тренуємо модель для витрат
        if expense_data:
            self._train_model('expense', expense_data)
            
        # Тренуємо модель для доходів
        if income_data:
            self._train_model('income', income_data)
    
    def _get_training_data(self, transaction_type):
        """Отримання даних для навчання з бази даних"""
        session = Session()
        data = []
        
        try:
            # Отримуємо транзакції з описами та категоріями
            transactions = session.query(
                Transaction.description,
                Category.name
            ).join(
                Category,
                Transaction.category_id == Category.id
            ).filter(
                Transaction.type == transaction_type,
                Transaction.description != None,
                Transaction.description != ""
            ).all()
            
            # Обробляємо кожну транзакцію
            for description, category in transactions:
                processed_desc = self.preprocess_text(description)
                if processed_desc:  # Додаємо тільки непорожні описи
                    data.append((processed_desc, category))
            
            return data
            
        except Exception as e:
            logger.error(f"Помилка при отриманні даних для навчання: {e}")
            return []
        finally:
            session.close()
    
    def _train_model(self, transaction_type, data):
        """Навчання моделі для конкретного типу транзакцій"""
        try:
            # Розділяємо дані на описи та категорії
            descriptions = [desc for desc, _ in data]
            categories = [cat for _, cat in data]
            
            # Векторизуємо тексти
            X = self.vectorizer.transform(descriptions)
            y = np.array(categories)
            
            # Розділяємо на тренувальні та тестові дані
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Створюємо та навчаємо модель Random Forest
            classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            classifier.fit(X_train, y_train)
            
            # Оцінюємо точність моделі
            y_pred = classifier.predict(X_test)
            logger.info(f"Результати класифікації для {transaction_type}:")
            logger.info(classification_report(y_test, y_pred))
            
            # Зберігаємо модель
            model_path = EXPENSE_MODEL_PATH if transaction_type == 'expense' else INCOME_MODEL_PATH
            with open(model_path, 'wb') as f:
                pickle.dump(classifier, f)
            
            # Зберігаємо векторизатор
            with open(VECTORIZER_PATH, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            
            # Встановлюємо модель
            if transaction_type == 'expense':
                self.expense_classifier = classifier
            else:
                self.income_classifier = classifier
                
            logger.info(f"Модель для {transaction_type} успішно навчена та збережена")
            
        except Exception as e:
            logger.error(f"Помилка при навчанні моделі для {transaction_type}: {e}")
    
    def _get_default_expense_data(self):
        """Базові дані для класифікації витрат"""
        return [
            ("супермаркет продукти харчі їжа сільпо атб новус варус фора ашан metro", "Продукти"),
            ("хліб молоко сир масло йогурт кефір ковбаса м'ясо риба овочі фрукти", "Продукти"),
            ("обід вечеря кафе ресторан піца суші кава чай", "Кафе і ресторани"),
            ("макдональдс мак пузата хата сушия кфс domino's pizza celentano vapiano", "Кафе і ресторани"),
            ("таксі убер уклон болт автобус метро поїзд транспорт маршрутка", "Транспорт"),
            ("бензин заправка окко вог сокар амік авіас", "Транспорт"),
            ("кіно театр концерт розваги клуб виставка зоопарк цирк музей атракціон", "Розваги"),
            ("квиток абонемент боулінг більярд караоке парк ігри", "Розваги"),
            ("одяг взуття магазин шоппінг покупки подарунки техніка електроніка", "Покупки"),
            ("комуналка газ світло вода опалення інтернет оренда квартира прибирання ремонт", "Комунальні послуги"),
            ("ліки аптека лікар стоматолог клініка медицина лікування медичний огляд", "Здоров'я"),
            ("навчання курси університет школа книги тренінг освіта", "Освіта"),
            ("благодійність", "Інше"),
            ("подарунок", "Інше"),
            ("переказ", "Інше")
        ]
    
    def _get_default_income_data(self):
        """Базові дані для класифікації доходів"""
        return [
            ("зарплата аванс премія бонус робота", "Зарплата"),
            ("фріланс підробка проект замовлення гонорар", "Фріланс"),
            ("подарунок свято день народження", "Подарунки"),
            ("відсотки дивіденди акції інвестиції депозит", "Інвестиції"),
            ("продаж повернення кешбек рефбек", "Інше")
        ]
    
    def classify(self, description, transaction_type):
        """Класифікація транзакції на основі опису"""
        if not description:
            return "Інше"
            
        processed_text = self.preprocess_text(description)
        if not processed_text:
            return "Інше"
            
        try:
            # Векторизуємо текст
            features = self.vectorizer.transform([processed_text])
            
            # Визначаємо, яку модель використовувати
            if transaction_type == 'expense':
                if self.expense_classifier is None:
                    return "Інше"
                return self.expense_classifier.predict(features)[0]
            else:  # income
                if self.income_classifier is None:
                    return "Інше"
                return self.income_classifier.predict(features)[0]
        except Exception as e:
            logger.error(f"Помилка при класифікації транзакції: {e}")
            return "Інше"
    
    def get_confidence_scores(self, description, transaction_type):
        """Отримання рівнів впевненості для всіх категорій"""
        if not description:
            return {}
            
        processed_text = self.preprocess_text(description)
        if not processed_text:
            return {}
            
        try:
            # Векторизуємо текст
            features = self.vectorizer.transform([processed_text])
            
            # Визначаємо, яку модель використовувати
            if transaction_type == 'expense':
                if self.expense_classifier is None:
                    return {}
                probs = self.expense_classifier.predict_proba(features)[0]
                classes = self.expense_classifier.classes_
            else:  # income
                if self.income_classifier is None:
                    return {}
                probs = self.income_classifier.predict_proba(features)[0]
                classes = self.income_classifier.classes_
            
            # Створюємо словник категорія -> впевненість
            return {cls: float(prob) for cls, prob in zip(classes, probs)}
        except Exception as e:
            logger.error(f"Помилка при отриманні рівнів впевненості: {e}")
            return {}

# Глобальний екземпляр класифікатора
_advanced_classifier = None

def get_advanced_classifier():
    """Отримання або створення екземпляра класифікатора"""
    global _advanced_classifier
    if _advanced_classifier is None:
        _advanced_classifier = AdvancedTransactionClassifier()
    return _advanced_classifier

def advanced_classify_transaction(description, transaction_type):
    """Класифікація транзакції з використанням просунутого класифікатора"""
    classifier = get_advanced_classifier()
    return classifier.classify(description, transaction_type)

def get_advanced_category_suggestions(description, transaction_type):
    """Отримання пропозицій категорій з рівнями впевненості"""
    classifier = get_advanced_classifier()
    return classifier.get_confidence_scores(description, transaction_type)

def retrain_model(transaction_type=None):
    """Повторне навчання моделей з оновленими даними"""
    classifier = get_advanced_classifier()
    
    if transaction_type:
        data = classifier._get_training_data(transaction_type)
        if data:
            classifier._train_model(transaction_type, data)
    else:
        # Якщо тип не вказано, перенавчаємо обидві моделі
        classifier.train_models()
    
    return True
