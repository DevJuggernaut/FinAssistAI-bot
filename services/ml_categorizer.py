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

# Create an instance for import
transaction_categorizer = TransactionCategorizer()