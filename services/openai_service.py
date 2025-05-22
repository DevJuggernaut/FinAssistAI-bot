from openai import OpenAI
import logging
from typing import List, Dict, Optional
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = """You are a financial advisor AI assistant. Your role is to provide personalized 
        financial advice based on the user's transaction history and financial goals. Be specific, actionable, 
        and consider the user's financial situation when making recommendations."""

    def generate_financial_advice(self, 
                                transactions: List[Dict],
                                user_goals: Optional[List[str]] = None,
                                time_period: str = "monthly") -> Dict:
        """
        Generate personalized financial advice based on transaction history
        """
        try:
            # Prepare transaction summary
            transaction_summary = self._prepare_transaction_summary(transactions, time_period)
            
            # Create prompt for OpenAI
            prompt = self._create_advice_prompt(transaction_summary, user_goals)
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse and structure the advice
            advice = self._parse_advice_response(response.choices[0].message.content)
            
            return advice
        except Exception as e:
            logger.error(f"Error generating financial advice: {str(e)}")
            raise

    def _prepare_transaction_summary(self, transactions: List[Dict], time_period: str) -> Dict:
        """Prepare a summary of transactions for analysis"""
        summary = {
            "total_income": 0,
            "total_expenses": 0,
            "category_totals": {},
            "largest_expenses": [],
            "recurring_expenses": [],
            "savings_rate": 0
        }
        
        # Calculate totals
        for transaction in transactions:
            amount = float(transaction['amount'])
            category = transaction.get('category', 'uncategorized')
            
            if transaction['type'] == 'income':
                summary['total_income'] += amount
            else:
                summary['total_expenses'] += amount
                summary['category_totals'][category] = summary['category_totals'].get(category, 0) + amount
        
        # Calculate savings rate
        if summary['total_income'] > 0:
            summary['savings_rate'] = (summary['total_income'] - summary['total_expenses']) / summary['total_income']
        
        # Sort categories by amount
        summary['category_totals'] = dict(sorted(
            summary['category_totals'].items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        return summary

    def _create_advice_prompt(self, summary: Dict, user_goals: Optional[List[str]]) -> str:
        """Create a prompt for the OpenAI model"""
        prompt = f"""Based on the following financial summary, provide personalized financial advice:

Financial Summary:
- Total Income: ${summary['total_income']:.2f}
- Total Expenses: ${summary['total_expenses']:.2f}
- Savings Rate: {summary['savings_rate']*100:.1f}%
- Top Expense Categories:
{json.dumps(summary['category_totals'], indent=2)}

"""
        if user_goals:
            prompt += f"\nUser's Financial Goals:\n{json.dumps(user_goals, indent=2)}\n"
        
        prompt += """
Please provide:
1. A brief analysis of the current financial situation
2. 3-5 specific, actionable recommendations
3. Potential areas for improvement
4. Short-term and long-term financial planning suggestions

Format the response as a JSON object with the following structure:
{
    "analysis": "Brief analysis of the current situation",
    "recommendations": ["List of specific recommendations"],
    "improvement_areas": ["List of areas for improvement"],
    "short_term_plan": "Short-term planning suggestions",
    "long_term_plan": "Long-term planning suggestions"
}"""
        
        return prompt

    def _parse_advice_response(self, response: str) -> Dict:
        """Parse and structure the advice response"""
        try:
            # Try to parse as JSON
            advice = json.loads(response)
        except json.JSONDecodeError:
            # If JSON parsing fails, create a structured response
            advice = {
                "analysis": response,
                "recommendations": [],
                "improvement_areas": [],
                "short_term_plan": "",
                "long_term_plan": ""
            }
        
        return advice

    def generate_budget_recommendations(self, 
                                     transactions: List[Dict],
                                     current_budget: Dict) -> Dict:
        """
        Generate budget recommendations based on spending patterns
        """
        try:
            # Prepare spending analysis
            spending_analysis = self._analyze_spending_patterns(transactions)
            
            # Create prompt for budget recommendations
            prompt = self._create_budget_prompt(spending_analysis, current_budget)
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse and structure the recommendations
            recommendations = self._parse_budget_response(response.choices[0].message.content)
            
            return recommendations
        except Exception as e:
            logger.error(f"Error generating budget recommendations: {str(e)}")
            raise

    def _analyze_spending_patterns(self, transactions: List[Dict]) -> Dict:
        """Analyze spending patterns from transactions"""
        analysis = {
            "category_spending": {},
            "monthly_trends": {},
            "unusual_expenses": [],
            "recurring_expenses": {}
        }
        
        # Analyze category spending
        for transaction in transactions:
            category = transaction.get('category', 'uncategorized')
            amount = float(transaction['amount'])
            date = datetime.fromisoformat(transaction['date'])
            month_key = date.strftime('%Y-%m')
            
            # Update category totals
            if category not in analysis['category_spending']:
                analysis['category_spending'][category] = 0
            analysis['category_spending'][category] += amount
            
            # Update monthly trends
            if month_key not in analysis['monthly_trends']:
                analysis['monthly_trends'][month_key] = 0
            analysis['monthly_trends'][month_key] += amount
        
        return analysis

    def _create_budget_prompt(self, analysis: Dict, current_budget: Dict) -> str:
        """Create a prompt for budget recommendations"""
        prompt = f"""Based on the following spending analysis and current budget, provide budget recommendations:

Spending Analysis:
{json.dumps(analysis, indent=2)}

Current Budget:
{json.dumps(current_budget, indent=2)}

Please provide:
1. Analysis of current spending patterns
2. Recommended budget adjustments
3. Category-specific recommendations
4. Tips for staying within budget

Format the response as a JSON object with the following structure:
{{
    "analysis": "Analysis of spending patterns",
    "recommendations": ["List of budget recommendations"],
    "category_adjustments": {{"category": "adjustment"}},
    "tips": ["List of budget management tips"]
}}"""
        
        return prompt

    def _parse_budget_response(self, response: str) -> Dict:
        """Parse and structure the budget recommendations"""
        try:
            # Try to parse as JSON
            recommendations = json.loads(response)
        except json.JSONDecodeError:
            # If JSON parsing fails, create a structured response
            recommendations = {
                "analysis": response,
                "recommendations": [],
                "category_adjustments": {},
                "tips": []
            }
        
        return recommendations 