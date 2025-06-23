import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import joblib
import logging
from typing import List, Dict, Tuple
import os

logger = logging.getLogger(__name__)

class TransactionCategorizer:
    def __init__(self, model_path: str = 'models/transaction_categorizer.joblib'):
        self.model_path = model_path
        self.model = None
        self.vectorizer = None
        self.categories = None
        self._load_or_create_model()

    def _load_or_create_model(self):
        """Load existing model or create a new one"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                logger.info("Loaded existing categorization model")
            else:
                self._create_new_model()
                logger.info("Created new categorization model")
        except Exception as e:
            logger.error(f"Error loading/creating model: {str(e)}")
            self._create_new_model()

    def _create_new_model(self):
        """Create a new model with default categories"""
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.model = Pipeline([
            ('vectorizer', self.vectorizer),
            ('classifier', MultinomialNB())
        ])
        self.categories = []

    def train(self, transactions: List[Dict], categories: List[str]):
        """
        Train the model with new transaction data
        """
        try:
            # Prepare training data
            descriptions = [t['description'] for t in transactions]
            labels = [t['category'] for t in transactions]
            
            # Update categories
            self.categories = list(set(categories))
            
            # Train the model
            self.model.fit(descriptions, labels)
            
            # Save the model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            
            logger.info("Model trained and saved successfully")
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise

    def predict_category(self, description: str) -> Tuple[str, float]:
        """
        Predict category for a transaction description
        Returns tuple of (category, confidence)
        """
        try:
            if not self.model:
                raise ValueError("Model not initialized")
            
            # Get prediction probabilities
            probs = self.model.predict_proba([description])[0]
            predicted_idx = np.argmax(probs)
            confidence = probs[predicted_idx]
            
            return self.categories[predicted_idx], confidence
        except Exception as e:
            logger.error(f"Error predicting category: {str(e)}")
            return "uncategorized", 0.0

    def evaluate_model(self, test_transactions: List[Dict]) -> Dict:
        """
        Evaluate model performance on test data
        """
        try:
            descriptions = [t['description'] for t in test_transactions]
            true_labels = [t['category'] for t in test_transactions]
            
            # Get predictions
            predictions = self.model.predict(descriptions)
            
            # Calculate accuracy
            accuracy = np.mean(predictions == true_labels)
            
            return {
                'accuracy': accuracy,
                'total_samples': len(test_transactions)
            }
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            raise

    def update_model(self, new_transactions: List[Dict]):
        """
        Update model with new transactions
        """
        try:
            # Prepare new data
            descriptions = [t['description'] for t in new_transactions]
            labels = [t['category'] for t in new_transactions]
            
            # Update categories
            self.categories = list(set(self.categories + labels))
            
            # Update model
            self.model.fit(descriptions, labels)
            
            # Save updated model
            joblib.dump(self.model, self.model_path)
            
            logger.info("Model updated successfully")
        except Exception as e:
            logger.error(f"Error updating model: {str(e)}")
            raise

    def categorize_transaction(self, description: str, amount: float, transaction_type: str) -> Dict:
        """
        Categorize transaction and return category with icon and name
        """
        try:
            # Базові правила категоризації за ключовими словами
            description_lower = description.lower()
            
            # Словник категорій з іконками для витрат
            expense_categories = {
                'продукти': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'їжа': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'атб': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'сільпо': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'новус': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'metro': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'ашан': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                
                'транспорт': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'проїзд': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'метро': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'автобус': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'таксі': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'uber': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'bolt': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'бензин': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'паливо': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                
                'ресторан': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'кафе': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'обід': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'сніданок': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'вечеря': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                
                'розваги': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'кіно': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'театр': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'концерт': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                
                'здоровя': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'аптека': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'лікар': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'ліки': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                
                'одяг': {'id': 6, 'name': 'Одяг і взуття', 'icon': '👕'},
                'взуття': {'id': 6, 'name': 'Одяг і взуття', 'icon': '👕'},
                'магазин': {'id': 6, 'name': 'Одяг і взуття', 'icon': '👕'},
                
                'комунальні': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'квартплата': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'світло': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'газ': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'вода': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'опалення': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
            }
            
            # Словник категорій з іконками для доходів
            income_categories = {
                'зарплата': {'id': 101, 'name': 'Зарплата', 'icon': '💰'},
                'фриланс': {'id': 102, 'name': 'Фриланс', 'icon': '💻'},
                'бонус': {'id': 103, 'name': 'Бонус', 'icon': '🎁'},
                'інвестиції': {'id': 104, 'name': 'Інвестиції', 'icon': '📈'},
                'продаж': {'id': 105, 'name': 'Продаж', 'icon': '💵'},
                'подарунок': {'id': 106, 'name': 'Подарунки', 'icon': '🎁'},
            }
            
            # Вибираємо словник на основі типу транзакції
            categories_dict = expense_categories if transaction_type == 'expense' else income_categories
            
            # Шукаємо відповідну категорію
            for keyword, category in categories_dict.items():
                if keyword in description_lower:
                    return category
            
            # Якщо не знайшли відповідну категорію, повертаємо загальну
            if transaction_type == 'expense':
                return {'id': 999, 'name': 'Інше', 'icon': '📦'}
            else:
                return {'id': 199, 'name': 'Інший дохід', 'icon': '💰'}
            
        except Exception as e:
            logger.error(f"Error in categorize_transaction: {e}")
            # Повертаємо дефолтну категорію у випадку помилки
            if transaction_type == 'expense':
                return {'id': 999, 'name': 'Інше', 'icon': '📦'}
            else:
                return {'id': 199, 'name': 'Інший дохід', 'icon': '💰'}

# Create an instance for import
transaction_categorizer = TransactionCategorizer()