import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple
import logging
from datetime import datetime, timedelta
import io
import base64
from pathlib import Path

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, output_dir: str = 'reports'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        # Use a default style instead of 'seaborn' which might not be available
        try:
            # Try to use seaborn-v0_8 style if available
            plt.style.use('seaborn-v0_8')
        except:
            # Fallback to default style
            plt.style.use('default')
        
    def generate_monthly_report(self, transactions: List[Dict]) -> Dict:
        """
        Generate a comprehensive monthly financial report
        """
        try:
            # Convert transactions to DataFrame
            df = pd.DataFrame(transactions)
            df['date'] = pd.to_datetime(df['date'])
            
            # Calculate basic metrics
            total_income = df[df['type'] == 'income']['amount'].sum()
            total_expenses = df[df['type'] == 'expense']['amount'].sum()
            net_savings = total_income - total_expenses
            savings_rate = (net_savings / total_income) * 100 if total_income > 0 else 0
            
            # Generate visualizations
            category_plot = self._create_category_distribution(df)
            trend_plot = self._create_spending_trend(df)
            budget_plot = self._create_budget_comparison(df)
            
            # Prepare report data
            report = {
                'summary': {
                    'total_income': total_income,
                    'total_expenses': total_expenses,
                    'net_savings': net_savings,
                    'savings_rate': savings_rate
                },
                'category_breakdown': self._get_category_breakdown(df),
                'trends': self._get_spending_trends(df),
                'visualizations': {
                    'category_distribution': category_plot,
                    'spending_trend': trend_plot,
                    'budget_comparison': budget_plot
                }
            }
            
            return report
        except Exception as e:
            logger.error(f"Error generating monthly report: {str(e)}")
            raise

    def _create_category_distribution(self, df: pd.DataFrame) -> str:
        """Create category distribution pie chart"""
        try:
            plt.figure(figsize=(10, 6))
            category_totals = df[df['type'] == 'expense'].groupby('category')['amount'].sum()
            plt.pie(category_totals, labels=category_totals.index, autopct='%1.1f%%')
            plt.title('Expense Distribution by Category')
            
            # Save plot to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
        except Exception as e:
            logger.error(f"Error creating category distribution: {str(e)}")
            return ""

    def _create_spending_trend(self, df: pd.DataFrame) -> str:
        """Create spending trend line chart"""
        try:
            plt.figure(figsize=(12, 6))
            daily_totals = df.groupby('date')['amount'].sum()
            plt.plot(daily_totals.index, daily_totals.values)
            plt.title('Daily Spending Trend')
            plt.xlabel('Date')
            plt.ylabel('Amount')
            plt.xticks(rotation=45)
            
            # Save plot to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
        except Exception as e:
            logger.error(f"Error creating spending trend: {str(e)}")
            return ""

    def _create_budget_comparison(self, df: pd.DataFrame) -> str:
        """Create budget vs actual comparison bar chart"""
        try:
            plt.figure(figsize=(12, 6))
            category_actual = df[df['type'] == 'expense'].groupby('category')['amount'].sum()
            category_budget = df.groupby('category')['budget'].first()
            
            x = np.arange(len(category_actual))
            width = 0.35
            
            plt.bar(x - width/2, category_actual, width, label='Actual')
            plt.bar(x + width/2, category_budget, width, label='Budget')
            
            plt.title('Budget vs Actual Spending by Category')
            plt.xlabel('Category')
            plt.ylabel('Amount')
            plt.xticks(x, category_actual.index, rotation=45)
            plt.legend()
            
            # Save plot to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
        except Exception as e:
            logger.error(f"Error creating budget comparison: {str(e)}")
            return ""

    def _get_category_breakdown(self, df: pd.DataFrame) -> Dict:
        """Get detailed category breakdown"""
        try:
            category_stats = df[df['type'] == 'expense'].groupby('category').agg({
                'amount': ['sum', 'mean', 'count']
            }).round(2)
            
            return {
                category: {
                    'total': stats['amount']['sum'],
                    'average': stats['amount']['mean'],
                    'count': stats['amount']['count']
                }
                for category, stats in category_stats.iterrows()
            }
        except Exception as e:
            logger.error(f"Error getting category breakdown: {str(e)}")
            return {}

    def _get_spending_trends(self, df: pd.DataFrame) -> Dict:
        """Get spending trends analysis"""
        try:
            # Daily trends
            daily_trends = df.groupby('date')['amount'].sum()
            
            # Weekly trends
            weekly_trends = df.groupby(df['date'].dt.isocalendar().week)['amount'].sum()
            
            # Monthly trends
            monthly_trends = df.groupby(df['date'].dt.month)['amount'].sum()
            
            return {
                'daily': daily_trends.to_dict(),
                'weekly': weekly_trends.to_dict(),
                'monthly': monthly_trends.to_dict()
            }
        except Exception as e:
            logger.error(f"Error getting spending trends: {str(e)}")
            return {}

    def generate_custom_report(self, 
                             transactions: List[Dict],
                             report_type: str,
                             time_period: str = 'monthly') -> Dict:
        """
        Generate a custom financial report based on specified parameters
        """
        try:
            df = pd.DataFrame(transactions)
            df['date'] = pd.to_datetime(df['date'])
            
            if report_type == 'category_analysis':
                return self._generate_category_analysis(df)
            elif report_type == 'trend_analysis':
                return self._generate_trend_analysis(df, time_period)
            elif report_type == 'budget_analysis':
                return self._generate_budget_analysis(df)
            else:
                raise ValueError(f"Unsupported report type: {report_type}")
        except Exception as e:
            logger.error(f"Error generating custom report: {str(e)}")
            raise

    def _generate_category_analysis(self, df: pd.DataFrame) -> Dict:
        """Generate detailed category analysis"""
        try:
            category_stats = df[df['type'] == 'expense'].groupby('category').agg({
                'amount': ['sum', 'mean', 'count', 'std']
            }).round(2)
            
            # Create category distribution plot
            plt.figure(figsize=(12, 6))
            sns.barplot(x=category_stats.index, y=category_stats[('amount', 'sum')])
            plt.title('Category-wise Expense Distribution')
            plt.xticks(rotation=45)
            
            # Save plot
            plot_path = self.output_dir / 'category_analysis.png'
            plt.savefig(plot_path, bbox_inches='tight')
            plt.close()
            
            return {
                'statistics': category_stats.to_dict(),
                'visualization': str(plot_path)
            }
        except Exception as e:
            logger.error(f"Error generating category analysis: {str(e)}")
            raise

    def _generate_trend_analysis(self, df: pd.DataFrame, time_period: str) -> Dict:
        """Generate trend analysis"""
        try:
            if time_period == 'daily':
                grouped = df.groupby('date')
            elif time_period == 'weekly':
                grouped = df.groupby(df['date'].dt.isocalendar().week)
            else:  # monthly
                grouped = df.groupby(df['date'].dt.month)
            
            trend_stats = grouped.agg({
                'amount': ['sum', 'mean', 'count']
            }).round(2)
            
            # Create trend plot
            plt.figure(figsize=(12, 6))
            plt.plot(trend_stats.index, trend_stats[('amount', 'sum')])
            plt.title(f'{time_period.capitalize()} Spending Trend')
            plt.xlabel(time_period.capitalize())
            plt.ylabel('Amount')
            
            # Save plot
            plot_path = self.output_dir / f'trend_analysis_{time_period}.png'
            plt.savefig(plot_path, bbox_inches='tight')
            plt.close()
            
            return {
                'statistics': trend_stats.to_dict(),
                'visualization': str(plot_path)
            }
        except Exception as e:
            logger.error(f"Error generating trend analysis: {str(e)}")
            raise

    def _generate_budget_analysis(self, df: pd.DataFrame) -> Dict:
        """Generate budget analysis"""
        try:
            budget_stats = df.groupby('category').agg({
                'amount': 'sum',
                'budget': 'first'
            }).round(2)
            
            # Calculate budget utilization
            budget_stats['utilization'] = (budget_stats['amount'] / budget_stats['budget'] * 100).round(2)
            
            # Create budget comparison plot
            plt.figure(figsize=(12, 6))
            x = np.arange(len(budget_stats))
            width = 0.35
            
            plt.bar(x - width/2, budget_stats['amount'], width, label='Actual')
            plt.bar(x + width/2, budget_stats['budget'], width, label='Budget')
            
            plt.title('Budget vs Actual Spending')
            plt.xlabel('Category')
            plt.ylabel('Amount')
            plt.xticks(x, budget_stats.index, rotation=45)
            plt.legend()
            
            # Save plot
            plot_path = self.output_dir / 'budget_analysis.png'
            plt.savefig(plot_path, bbox_inches='tight')
            plt.close()
            
            return {
                'statistics': budget_stats.to_dict(),
                'visualization': str(plot_path)
            }
        except Exception as e:
            logger.error(f"Error generating budget analysis: {str(e)}")
            raise

# Create an instance for import
analytics_service = AnalyticsService()