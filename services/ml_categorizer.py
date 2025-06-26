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
                'silpo': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'новус': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'novus': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'metro': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'метро': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'ашан': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'auchan': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'фора': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'fora': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'варус': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'varus': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'таврія': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'tavria': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'епіцентр': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'epicentr': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'zakaz': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'глово': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'glovo': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'wolt': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                'bolt food': {'id': 1, 'name': 'Продукти', 'icon': '🛒'},
                
                'транспорт': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'проїзд': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'автобус': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'таксі': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'taxi': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'uber': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'bolt': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'uklon': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'бензин': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'паливо': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'заправка': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'wog': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'okko': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'shell': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'eko': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                'авр': {'id': 2, 'name': 'Транспорт', 'icon': '🚗'},
                
                'ресторан': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'кафе': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'cafe': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'обід': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'сніданок': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'вечеря': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'макдональдс': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'mcdonalds': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'kfc': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'burger': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'піца': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'pizza': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'dominos': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                'челентано': {'id': 3, 'name': 'Кафе і ресторани', 'icon': '🍽️'},
                
                'розваги': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'кіно': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'cinema': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'театр': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'концерт': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'steam': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'netflix': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'spotify': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'youtube': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'playstation': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'xbox': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'sweet.tv': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                'oll.tv': {'id': 4, 'name': 'Розваги', 'icon': '🎯'},
                
                'здоровя': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'аптека': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'pharmacy': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'лікар': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'ліки': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'медицина': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'клініка': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'лікарня': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'бажаємо': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'спорт': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'фітнес': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'fitness': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                'тренажерн': {'id': 5, 'name': "Здоров'я", 'icon': '💊'},
                
                'одяг': {'id': 6, 'name': 'Одяг і взуття', 'icon': '👕'},
                'взуття': {'id': 6, 'name': 'Одяг і взуття', 'icon': '👕'},
                'магазин': {'id': 6, 'name': 'Одяг і взуття', 'icon': '👕'},
                'zara': {'id': 6, 'name': 'Одяг і взуття', 'icon': '👕'},
                'h&m': {'id': 6, 'name': 'Одяг і взуття', 'icon': '👕'},
                'bershka': {'id': 6, 'name': 'Одяг і взуття', 'icon': '👕'},
                'pull&bear': {'id': 6, 'name': 'Одяг і взуття', 'icon': '👕'},
                'inditex': {'id': 6, 'name': 'Одяг і взуття', 'icon': '👕'},
                'lcwaikiki': {'id': 6, 'name': 'Одяг і взуття', 'icon': '👕'},
                'cropp': {'id': 6, 'name': 'Одяг і взуття', 'icon': '👕'},
                'reserved': {'id': 6, 'name': 'Одяг і взуття', 'icon': '👕'},
                
                'комунальні': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'квартплата': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'світло': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'газ': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'вода': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'опалення': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'київстар': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'kyivstar': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'vodafone': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'водафон': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'lifecell': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'лайфселл': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'інтернет': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'internet': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'триолан': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'triolan': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'ланет': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                'lanet': {'id': 7, 'name': 'Комунальні послуги', 'icon': '🏠'},
                
                # Техніка та електроніка
                'техніка': {'id': 8, 'name': 'Техніка', 'icon': '📱'},
                'розетка': {'id': 8, 'name': 'Техніка', 'icon': '📱'},
                'rozetka': {'id': 8, 'name': 'Техніка', 'icon': '📱'},
                'comfy': {'id': 8, 'name': 'Техніка', 'icon': '📱'},
                'фокстрот': {'id': 8, 'name': 'Техніка', 'icon': '📱'},
                'foxtrot': {'id': 8, 'name': 'Техніка', 'icon': '📱'},
                'eldorado': {'id': 8, 'name': 'Техніка', 'icon': '📱'},
                'цитрус': {'id': 8, 'name': 'Техніка', 'icon': '📱'},
                'citrus': {'id': 8, 'name': 'Техніка', 'icon': '📱'},
                'apple': {'id': 8, 'name': 'Техніка', 'icon': '📱'},
                'google': {'id': 8, 'name': 'Техніка', 'icon': '📱'},
                'microsoft': {'id': 8, 'name': 'Техніка', 'icon': '📱'},
            }
            
            # Словник категорій з іконками для доходів
            income_categories = {
                'зарплата': {'id': 101, 'name': 'Зарплата', 'icon': '💰'},
                'заробітна': {'id': 101, 'name': 'Зарплата', 'icon': '💰'},
                'salary': {'id': 101, 'name': 'Зарплата', 'icon': '💰'},
                'оклад': {'id': 101, 'name': 'Зарплата', 'icon': '💰'},
                'фриланс': {'id': 102, 'name': 'Фриланс', 'icon': '💻'},
                'freelance': {'id': 102, 'name': 'Фриланс', 'icon': '💻'},
                'фоп': {'id': 102, 'name': 'Фриланс', 'icon': '💻'},
                'проект': {'id': 102, 'name': 'Фриланс', 'icon': '💻'},
                'на картку': {'id': 102, 'name': 'Фриланс', 'icon': '💻'},
                'переказ': {'id': 102, 'name': 'Фриланс', 'icon': '💻'},
                'transfer': {'id': 102, 'name': 'Фриланс', 'icon': '💻'},
                'payment': {'id': 102, 'name': 'Фриланс', 'icon': '💻'},
                'зарахування': {'id': 102, 'name': 'Фриланс', 'icon': '💻'},
                'поповнення': {'id': 102, 'name': 'Фриланс', 'icon': '💻'},
                'бонус': {'id': 103, 'name': 'Бонус', 'icon': '🎁'},
                'bonus': {'id': 103, 'name': 'Бонус', 'icon': '🎁'},
                'премія': {'id': 103, 'name': 'Бонус', 'icon': '🎁'},
                'cashback': {'id': 103, 'name': 'Бонус', 'icon': '🎁'},
                'кешбек': {'id': 103, 'name': 'Бонус', 'icon': '🎁'},
                'кешбэк': {'id': 103, 'name': 'Бонус', 'icon': '🎁'},
                'інвестиції': {'id': 104, 'name': 'Інвестиції', 'icon': '📈'},
                'investment': {'id': 104, 'name': 'Інвестиції', 'icon': '📈'},
                'дивіденди': {'id': 104, 'name': 'Інвестиції', 'icon': '📈'},
                'відсотки': {'id': 104, 'name': 'Інвестиції', 'icon': '📈'},
                'проценти': {'id': 104, 'name': 'Інвестиції', 'icon': '📈'},
                'interest': {'id': 104, 'name': 'Інвестиції', 'icon': '📈'},
                'продаж': {'id': 105, 'name': 'Продаж', 'icon': '💵'},
                'sale': {'id': 105, 'name': 'Продаж', 'icon': '💵'},
                'реалізація': {'id': 105, 'name': 'Продаж', 'icon': '💵'},
                'подарунок': {'id': 106, 'name': 'Подарунки', 'icon': '🎁'},
                'gift': {'id': 106, 'name': 'Подарунки', 'icon': '🎁'},
                'дарунок': {'id': 106, 'name': 'Подарунки', 'icon': '🎁'},
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

    def get_best_category_for_user(self, description: str, amount: float, transaction_type: str, user_categories: List[Dict]) -> Dict:
        """
        Get best matching category for user based on description and learned patterns
        """
        try:
            if not user_categories:
                return None
            
            description_lower = description.lower().strip()
            
            # Спеціальні правила для конкретних назв та патернів
            special_rules = {
                # Транспорт
                'uklon': 'транспорт',
                'uber': 'транспорт', 
                'bolt': 'транспорт',
                'таксі': 'транспорт',
                'taxi': 'транспорт',
                'метро': 'транспорт',
                'проїзд': 'транспорт',
                
                # Продукти
                'атб': 'продукт',
                'сільпо': 'продукт',
                'silpo': 'продукт',
                'новус': 'продукт',
                'novus': 'продукт',
                'ашан': 'продукт',
                'metro': 'продукт',
                'фора': 'продукт',
                'varus': 'продукт',
                'варус': 'продукт',
                'zakaz': 'продукт',
                'glovo': 'продукт',
                'wolt': 'продукт',
                
                # Техніка та цифрові послуги
                'apple': 'техніка',
                'google': 'техніка',
                'microsoft': 'техніка',
                'steam': 'розваг',
                'netflix': 'розваг',
                'spotify': 'розваг',
                'youtube': 'розваг',
                'playstation': 'розваг',
                'xbox': 'розваг',
                
                # Ресторани
                'макдональдс': 'кафе',
                'mcdonalds': 'кафе',
                'kfc': 'кафе',
                'burger': 'кафе',
                'піца': 'кафе',
                'pizza': 'кафе',
                'ресторан': 'кафе',
                'кафе': 'кафе',
                
                # Доставка
                'нова пошта': 'доставка',
                'nova poshta': 'доставка',
                'укрпошта': 'доставка',
                'meest': 'доставка',
                'делівері': 'доставка',
                'delivery': 'доставка',
                
                # Зарплата та доходи (для income)
                'зарплата': 'зарплат',
                'заробітна': 'зарплат', 
                'salary': 'зарплат',
                'фоп': 'фриланс',
                'фриланс': 'фриланс',
                'freelance': 'фриланс',
                'проект': 'фриланс',
                'на картку': 'фриланс',  # зміна тут
                'переказ': 'фриланс',    # зміна тут
                'transfer': 'фриланс',   # зміна тут
                'степанов': 'фриланс',   # додаємо конкретне ім'я
                'мельник': 'фриланс',    # додаємо конкретне ім'я
                'сім23': 'фриланс',      # додаємо конкретну назву
            }
            
            # Шукаємо категорію за спеціальними правилами
            best_match = None
            best_score = 0
            
            for phrase, category_keyword in special_rules.items():
                if phrase in description_lower:
                    # Шукаємо відповідну категорію користувача
                    for category in user_categories:
                        category_name_lower = category['name'].lower()
                        
                        # Перевіряємо чи містить назва категорії ключове слово
                        if category_keyword in category_name_lower:
                            score = len(phrase) * 2  # Довші фрази мають вищий пріоритет
                            if score > best_score:
                                best_score = score
                                best_match = category
            
            if best_match:
                return best_match
            
            # Якщо спеціальні правила не спрацювали, використовуємо загальну логіку
            category_scores = {}
            
            for category in user_categories:
                category_id = category['id']
                category_name_lower = category['name'].lower()
                category_scores[category_id] = 0
                
                # Високий бал за точний збіг з назвою категорії
                category_words = category_name_lower.split()
                for word in category_words:
                    if len(word) > 2 and word in description_lower:
                        category_scores[category_id] += 5
                
                # Часткове співпадіння
                if any(word in description_lower for word in category_words if len(word) > 3):
                    category_scores[category_id] += 3
                
                # Семантичні співпадіння
                semantic_keywords = {
                    'продукт': ['їжа', 'food', 'meal', 'супермаркет', 'магазин', 'market'],
                    'транспорт': ['поїздка', 'дорога', 'trip', 'ride', 'travel'],
                    'кафе': ['їжа', 'meal', 'обід', 'вечеря', 'сніданок', 'dinner', 'lunch'],
                    'розваг': ['entertainment', 'fun', 'гра', 'фільм', 'movie', 'music'],
                    'здоров': ['health', 'medical', 'doctor', 'medicine'],
                    'одяг': ['clothes', 'fashion', 'style', 'wear'],
                    'комунальн': ['utility', 'bill', 'payment', 'service'],
                    'житло': ['house', 'home', 'rent', 'оренда'],
                    'освіт': ['education', 'learn', 'study', 'book', 'course'],
                    'зарплат': ['work', 'job', 'employ', 'робота'],
                    'фриланс': ['project', 'contract', 'work', 'dev'],
                }
                
                for keyword, synonyms in semantic_keywords.items():
                    if keyword in category_name_lower:
                        for synonym in synonyms:
                            if synonym in description_lower:
                                category_scores[category_id] += 2
            
            # Повертаємо категорію з найвищим балом
            if category_scores:
                best_category_id = max(category_scores.items(), key=lambda x: x[1])
                if best_category_id[1] > 0:  # Тільки якщо є хоча б якийсь збіг
                    return next((cat for cat in user_categories if cat['id'] == best_category_id[0]), None)
            
            # Якщо нічого не знайшли, повертаємо першу категорію типу "Інше"
            other_category = next((cat for cat in user_categories if 'інше' in cat['name'].lower()), None)
            return other_category or user_categories[0] if user_categories else None
            
        except Exception as e:
            logger.error(f"Error getting best category for user: {e}")
            # В разі помилки повертаємо першу категорію
            return user_categories[0] if user_categories else None

    def suggest_category_for_bank_statement(self, description: str, transaction_type: str) -> Dict:
        """
        Suggest a category for bank statement import.
        Returns category info dictionary with id, name and icon (used by statement parser).
        """
        try:
            # Використовуємо існуючий метод categorize_transaction
            category_info = self.categorize_transaction(description, 0.0, transaction_type)
            
            # Повертаємо повну інформацію про категорію
            return category_info
            
        except Exception as e:
            logger.error(f"Error in suggest_category_for_bank_statement: {e}")
            # Повертаємо дефолтну категорію у випадку помилки
            if transaction_type == 'expense':
                return {'id': 999, 'name': 'Інше', 'icon': '📦'}
            else:
                return {'id': 199, 'name': 'Інший дохід', 'icon': '💰'}

# Create an instance for import
transaction_categorizer = TransactionCategorizer()