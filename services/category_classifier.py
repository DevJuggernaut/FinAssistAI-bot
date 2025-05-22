import re
import logging
from typing import Dict, List, Tuple
import json
import os
from pathlib import Path
import pickle
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

# Константи для типів транзакцій
TYPE_EXPENSE = 'expense'
TYPE_INCOME = 'income'

# Константи для шляхів до моделей
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
EXPENSE_MODEL_PATH = os.path.join(MODEL_DIR, 'expense_classifier.pkl')
INCOME_MODEL_PATH = os.path.join(MODEL_DIR, 'income_classifier.pkl')

# Створюємо директорію для моделей, якщо вона не існує
os.makedirs(MODEL_DIR, exist_ok=True)

# Базові навчальні дані для класифікації витрат
DEFAULT_EXPENSE_TRAINING_DATA = [
    ("супермаркет продукти харчі їжа сільпо атб новус варус фора ашан metro", "Продукти"),
    ("кафе ресторан піца суші кава чай mcdonalds kfc пузата хата", "Кафе і ресторани"),
    ("таксі uber uklon bolt автобус метро поїзд транспорт маршрутка", "Транспорт"),
    ("кіно театр концерт розваги клуб виставка зоопарк цирк музей атракціон", "Розваги"),
    ("одяг взуття магазин шоппінг покупки подарунки техніка електроніка", "Покупки"),
    ("комуналка газ світло вода опалення інтернет оренда квартира прибирання ремонт", "Комунальні послуги"),
    ("ліки аптека лікар стоматолог клініка медицина лікування медичний огляд", "Здоров'я"),
    ("навчання курси університет школа книги тренінг освіта", "Освіта"),
    ("непередбачені витрати благодійність інше", "Інше")
]

# Базові навчальні дані для класифікації доходів
DEFAULT_INCOME_TRAINING_DATA = [
    ("зарплата аванс премія бонус робота", "Зарплата"),
    ("фріланс підробка проект замовлення гонорар", "Фріланс"),
    ("подарунок свято день народження", "Подарунки"),
    ("відсотки дивіденди акції інвестиції депозит", "Інвестиції"),
    ("продаж повернення кешбек рефбек", "Інше")
]

class TransactionClassifier:
    """Класифікатор фінансових транзакцій на основі ML"""
    
    def __init__(self):
        self.expense_classifier = None
        self.income_classifier = None
        self.load_or_train_models()
    
    def load_or_train_models(self):
        """Завантаження існуючих моделей або навчання нових"""
        # Спробуємо завантажити модель для витрат
        if os.path.exists(EXPENSE_MODEL_PATH):
            try:
                with open(EXPENSE_MODEL_PATH, 'rb') as f:
                    self.expense_classifier = pickle.load(f)
                logger.info("Завантажено існуючу модель для класифікації витрат")
            except Exception as e:
                logger.error(f"Помилка при завантаженні моделі для витрат: {e}")
                self.expense_classifier = None
        
        # Спробуємо завантажити модель для доходів
        if os.path.exists(INCOME_MODEL_PATH):
            try:
                with open(INCOME_MODEL_PATH, 'rb') as f:
                    self.income_classifier = pickle.load(f)
                logger.info("Завантажено існуючу модель для класифікації доходів")
            except Exception as e:
                logger.error(f"Помилка при завантаженні моделі для доходів: {e}")
                self.income_classifier = None
        
        # Якщо моделей немає, навчаємо нові
        if self.expense_classifier is None:
            logger.info("Навчаємо нову модель для класифікації витрат")
            self.train_expense_classifier(DEFAULT_EXPENSE_TRAINING_DATA)
        
        if self.income_classifier is None:
            logger.info("Навчаємо нову модель для класифікації доходів")
            self.train_income_classifier(DEFAULT_INCOME_TRAINING_DATA)
    
    def preprocess_text(self, text):
        """Підготовка тексту для класифікації"""
        if not text:
            return ""
        
        # Переводимо в нижній регістр
        text = text.lower()
        
        # Видаляємо спеціальні символи
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Видаляємо зайві пробіли
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def train_expense_classifier(self, training_data):
        """Навчання моделі для класифікації витрат"""
        texts = [self.preprocess_text(text) for text, _ in training_data]
        labels = [label for _, label in training_data]
        
        # Створюємо і навчаємо модель
        self.expense_classifier = Pipeline([
            ('vectorizer', CountVectorizer(analyzer='word', ngram_range=(1, 2))),
            ('classifier', MultinomialNB())
        ])
        
        self.expense_classifier.fit(texts, labels)
        
        # Зберігаємо модель
        with open(EXPENSE_MODEL_PATH, 'wb') as f:
            pickle.dump(self.expense_classifier, f)
    
    def train_income_classifier(self, training_data):
        """Навчання моделі для класифікації доходів"""
        texts = [self.preprocess_text(text) for text, _ in training_data]
        labels = [label for _, label in training_data]
        
        # Створюємо і навчаємо модель
        self.income_classifier = Pipeline([
            ('vectorizer', CountVectorizer(analyzer='word', ngram_range=(1, 2))),
            ('classifier', MultinomialNB())
        ])
        
        self.income_classifier.fit(texts, labels)
        
        # Зберігаємо модель
        with open(INCOME_MODEL_PATH, 'wb') as f:
            pickle.dump(self.income_classifier, f)
    
    def update_models_with_new_data(self, new_expense_data=None, new_income_data=None):
        """Оновлення моделей з новими даними"""
        if new_expense_data and len(new_expense_data) > 0:
            # Об'єднуємо базові дані з новими
            combined_data = DEFAULT_EXPENSE_TRAINING_DATA + new_expense_data
            self.train_expense_classifier(combined_data)
            logger.info(f"Модель для витрат оновлено з {len(new_expense_data)} новими записами")
        
        if new_income_data and len(new_income_data) > 0:
            # Об'єднуємо базові дані з новими
            combined_data = DEFAULT_INCOME_TRAINING_DATA + new_income_data
            self.train_income_classifier(combined_data)
            logger.info(f"Модель для доходів оновлено з {len(new_income_data)} новими записами")
    
    def classify(self, description, transaction_type):
        """Класифікація транзакції на основі опису та типу"""
        processed_text = self.preprocess_text(description)
        
        if not processed_text:
            return "Інше" if transaction_type == TYPE_EXPENSE else "Інше"
        
        try:
            if transaction_type == TYPE_EXPENSE:
                return self.expense_classifier.predict([processed_text])[0]
            else:
                return self.income_classifier.predict([processed_text])[0]
        except Exception as e:
            logger.error(f"Помилка при класифікації транзакції: {e}")
            return "Інше" if transaction_type == TYPE_EXPENSE else "Інше"
    
    def get_category_probabilities(self, description, transaction_type):
        """Отримання ймовірностей для всіх категорій"""
        processed_text = self.preprocess_text(description)
        
        if not processed_text:
            return {}
        
        try:
            if transaction_type == TYPE_EXPENSE:
                probs = self.expense_classifier.predict_proba([processed_text])[0]
                classes = self.expense_classifier.classes_
            else:
                probs = self.income_classifier.predict_proba([processed_text])[0]
                classes = self.income_classifier.classes_
            
            return {cls: float(prob) for cls, prob in zip(classes, probs)}
        except Exception as e:
            logger.error(f"Помилка при отриманні ймовірностей категорій: {e}")
            return {}


# Створюємо глобальний екземпляр класифікатора
_classifier = None

def get_classifier():
    """Отримання глобального екземпляра класифікатора"""
    global _classifier
    if _classifier is None:
        _classifier = TransactionClassifier()
    return _classifier

def classify_transaction(description, transaction_type):
    """Функція для класифікації транзакції"""
    classifier = get_classifier()
    return classifier.classify(description, transaction_type)

def get_category_suggestions(description, transaction_type):
    """Функція для отримання пропозицій категорій з ймовірностями"""
    classifier = get_classifier()
    return classifier.get_category_probabilities(description, transaction_type)
