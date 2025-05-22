import os
import logging
from openai import OpenAI
from datetime import datetime, timedelta
from database.config import OPENAI_API_KEY
from database.db_operations import get_monthly_stats, get_transactions, save_financial_advice

logger = logging.getLogger(__name__)

# Ініціалізація клієнта OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

class FinancialAdvisor:
    """Клас для генерації фінансових рекомендацій на основі OpenAI"""
    
    def __init__(self, user_id):
        self.user_id = user_id
    
    def _generate_user_financial_profile(self):
        """Створення профілю користувача на основі його фінансових даних"""
        try:
            # Отримуємо статистику за поточний місяць
            current_stats = get_monthly_stats(self.user_id)
            
            # Отримуємо статистику за попередній місяць
            now = datetime.utcnow()
            prev_month = now.month - 1 if now.month > 1 else 12
            prev_year = now.year if now.month > 1 else now.year - 1
            prev_stats = get_monthly_stats(self.user_id, prev_year, prev_month)
            
            # Отримуємо останні транзакції
            recent_transactions = get_transactions(self.user_id, limit=30)
            
            # Формуємо транзакції у читабельному вигляді
            transaction_texts = []
            for tx in recent_transactions:
                tx_type = "Витрата" if tx.type == "expense" else "Дохід"
                tx_text = f"{tx_type}: {tx.amount} грн - {tx.description} ({tx.transaction_date.strftime('%d.%m.%Y')})"
                transaction_texts.append(tx_text)
            
            # Створюємо профіль
            profile = {
                "current_month": {
                    "expenses": current_stats["expenses"],
                    "income": current_stats["income"],
                    "balance": current_stats["balance"],
                    "top_expense_categories": [f"{cat[0]} ({cat[2]} грн)" for cat in current_stats["top_categories"]]
                },
                "previous_month": {
                    "expenses": prev_stats["expenses"],
                    "income": prev_stats["income"],
                    "balance": prev_stats["balance"]
                },
                "recent_transactions": transaction_texts[:20],  # Обмежуємо 20 транзакціями
                "month_name": now.strftime("%B"),
                "spending_patterns": self._analyze_spending_patterns(recent_transactions),
                "savings_potential": self._calculate_savings_potential(current_stats)
            }
            
            # Додаємо порівняння з попереднім місяцем
            if prev_stats["expenses"] > 0:
                expense_change_pct = ((current_stats["expenses"] - prev_stats["expenses"]) / prev_stats["expenses"]) * 100
                profile["expense_change_pct"] = expense_change_pct
            
            if prev_stats["income"] > 0:
                income_change_pct = ((current_stats["income"] - prev_stats["income"]) / prev_stats["income"]) * 100
                profile["income_change_pct"] = income_change_pct
            
            return profile
            
        except Exception as e:
            logger.error(f"Помилка при створенні фінансового профілю: {e}")
            # Повертаємо базовий профіль у випадку помилки
            return {
                "current_month": {
                    "expenses": 0,
                    "income": 0,
                    "balance": 0,
                    "top_expense_categories": []
                },
                "previous_month": {
                    "expenses": 0,
                    "income": 0,
                    "balance": 0
                },
                "recent_transactions": [],
                "month_name": datetime.utcnow().strftime("%B")
            }
    
    def _analyze_spending_patterns(self, transactions):
        """Аналіз патернів витрат користувача"""
        if not transactions:
            return {}
            
        # Групування за категоріями та днями тижня
        weekday_spending = {i: 0 for i in range(7)}  # 0=понеділок, 6=неділя
        recurring_merchants = {}
        
        for tx in transactions:
            if tx.type != "expense":
                continue
                
            # Аналіз за днями тижня
            weekday = tx.transaction_date.weekday()
            weekday_spending[weekday] += tx.amount
            
            # Виявлення повторюваних витрат
            if tx.description:
                merchant = tx.description.lower().split()[0]  # Спрощене визначення мерчанта
                if merchant in recurring_merchants:
                    recurring_merchants[merchant] += 1
                else:
                    recurring_merchants[merchant] = 1
        
        # Знаходимо день з найбільшими витратами
        max_spending_day = max(weekday_spending.items(), key=lambda x: x[1])
        weekday_names = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]
        
        # Знаходимо найчастіші місця витрат
        frequent_merchants = sorted(recurring_merchants.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "high_spending_day": weekday_names[max_spending_day[0]],
            "high_spending_day_amount": max_spending_day[1],
            "frequent_merchants": [{"name": m[0], "count": m[1]} for m in frequent_merchants if m[1] > 1]
        }
    
    def _calculate_savings_potential(self, stats):
        """Розрахунок потенціалу заощаджень"""
        if not stats or stats["income"] == 0:
            return 0
            
        # Простий розрахунок - скільки відсотків доходу витрачається
        expense_ratio = stats["expenses"] / stats["income"] if stats["income"] > 0 else 1
        
        # Потенціальні заощадження (вважаємо, що оптимальне значення - витрачати не більше 70% доходу)
        if expense_ratio > 0.7:
            savings_potential = stats["expenses"] - (stats["income"] * 0.7)
            return savings_potential
        else:
            return 0
    
    def generate_financial_advice(self, advice_type="general"):
        """Генерація фінансових порад на основі даних користувача та OpenAI"""
        try:
            profile = self._generate_user_financial_profile()
            
            # Формуємо запит до OpenAI в залежності від типу поради
            if advice_type == "savings":
                prompt_template = """
                Ви - професійний фінансовий консультант. На основі наведених даних, будь ласка, 
                надайте конкретні поради щодо того, як користувач може збільшити свої заощадження.
                
                Дані про фінанси користувача за поточний місяць ({month_name}):
                - Витрати: {current_expenses} грн
                - Доходи: {current_income} грн
                - Баланс: {current_balance} грн
                - Найбільші категорії витрат: {top_categories}
                
                Додаткові дані про користувача:
                - День з найбільшими витратами: {high_spending_day}
                - Часті місця витрат: {frequent_merchants}
                - Потенціал заощаджень: {savings_potential} грн
                
                Надайте 3-5 конкретних, персоналізованих порад щодо заощаджень, базуючись на цих даних.
                Зосередьтесь на категоріях з найбільшими витратами та можливостях оптимізації щоденних трат.
                Поради мають бути практичні та реалістичні.
                """
            elif advice_type == "investment":
                prompt_template = """
                Ви - професійний фінансовий консультант. На основі наведених даних, будь ласка, 
                надайте базові поради щодо інвестицій для початківців.
                
                Дані про фінанси користувача:
                - Щомісячні витрати: {current_expenses} грн
                - Щомісячні доходи: {current_income} грн
                - Поточний баланс: {current_balance} грн
                
                Надайте 3-5 порад щодо базових інвестиційних стратегій, які підходять для початківців з такими фінансовими показниками.
                Враховуйте український фінансовий ринок. Поради мають бути доступні для розуміння, без складної фінансової термінології.
                """
            elif advice_type == "budget":
                prompt_template = """
                Ви - професійний фінансовий консультант. На основі наведених даних, будь ласка, 
                надайте конкретні поради щодо планування бюджету.
                
                Дані про фінанси користувача за поточний місяць ({month_name}):
                - Витрати: {current_expenses} грн
                - Доходи: {current_income} грн
                - Категорії з найбільшими витратами: {top_categories}
                - Порівняно з попереднім місяцем, витрати {expense_change}
                
                Останні транзакції:
                {recent_transactions}
                
                Надайте 3-5 конкретних порад щодо кращого планування бюджету, враховуючи патерни витрат користувача.
                Зосередьтеся на тому, як оптимізувати витрати в найбільших категоріях та створити ефективний план бюджету.
                """
            else:  # "general"
                prompt_template = """
                Ви - професійний фінансовий консультант. На основі наведених даних, будь ласка, 
                надайте загальні фінансові поради для покращення фінансового стану користувача.
                
                Дані про фінанси користувача за поточний місяць ({month_name}):
                - Витрати: {current_expenses} грн
                - Доходи: {current_income} грн
                - Баланс: {current_balance} грн
                - Найбільші категорії витрат: {top_categories}
                
                Надайте 3-5 практичних, персоналізованих фінансових порад, які допоможуть користувачу 
                покращити його фінансовий стан. Поради мають бути конкретні та корисні.
                """
            
            # Підготовка даних для шаблону
            prompt_data = {
                "current_expenses": profile["current_month"]["expenses"],
                "current_income": profile["current_month"]["income"],
                "current_balance": profile["current_month"]["balance"],
                "month_name": profile["month_name"],
                "top_categories": ", ".join(profile["current_month"]["top_expense_categories"][:3]),
                "expense_change": f"зросли на {profile.get('expense_change_pct', 0):.1f}%" if profile.get('expense_change_pct', 0) > 0 else f"зменшились на {abs(profile.get('expense_change_pct', 0)):.1f}%",
                "recent_transactions": "\n".join(profile["recent_transactions"][:5]),
                "high_spending_day": profile.get("spending_patterns", {}).get("high_spending_day", "невідомо"),
                "frequent_merchants": ", ".join([m["name"] for m in profile.get("spending_patterns", {}).get("frequent_merchants", [])]),
                "savings_potential": profile.get("savings_potential", 0)
            }
            
            # Формуємо фінальний промпт
            prompt = prompt_template.format(**prompt_data)
            
            # Виклик OpenAI API з можливістю використання різних моделей
            try:
                # Спочатку спробуємо використати GPT-4
                response = client.chat.completions.create(
                    model="gpt-4o",  # Використовуємо GPT-4o - останню версію GPT-4
                    messages=[
                        {"role": "system", "content": "Ви - професійний фінансовий консультант, який надає персоналізовані поради українською мовою. Використовуйте сучасні фінансові методики, будьте конкретними та пропонуйте дієві поради."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,  # Баланс між креативністю і точністю
                    max_tokens=800   # Обмеження для короткої, але змістовної відповіді
                )
            except Exception as model_error:
                logger.warning(f"Помилка використання GPT-4o: {model_error}. Використовуємо резервну модель GPT-3.5-Turbo.")
                # Якщо GPT-4 не доступний, використовуємо GPT-3.5-Turbo
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Ви - професійний фінансовий консультант, який надає персоналізовані поради українською мовою."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=600
                )
            
            # Отримуємо текст поради
            advice_text = response.choices[0].message.content.strip()
            
            # Зберігаємо пораду в базу даних
            save_financial_advice(self.user_id, advice_text, advice_type)
            
            return advice_text
            
        except Exception as e:
            logger.error(f"Помилка при генерації фінансової поради: {e}")
            return "На жаль, не вдалося згенерувати фінансову пораду. Спробуйте пізніше або зверніться до команди підтримки."
    
    def analyze_investment_opportunities(self):
        """Аналіз потенційних інвестиційних можливостей на основі фінансових даних користувача"""
        try:
            profile = self._generate_user_financial_profile()
            
            # Розраховуємо доступну для інвестицій суму
            monthly_income = profile["current_month"]["income"]
            monthly_expenses = profile["current_month"]["expenses"]
            available_for_investment = max(0, monthly_income - monthly_expenses * 1.1)  # 10% буфер
            
            # Формуємо запит до OpenAI для інвестиційних рекомендацій
            prompt = f"""
            Ви - професійний фінансовий радник з інвестицій. На основі наведених даних, запропонуйте 
            персоналізовану інвестиційну стратегію для українського користувача.
            
            Дані про фінанси користувача:
            - Щомісячний дохід: {profile["current_month"]["income"]} грн
            - Щомісячні витрати: {profile["current_month"]["expenses"]} грн
            - Приблизна сума, доступна для інвестицій: {available_for_investment:.2f} грн/місяць
            - Поточний баланс: {profile["current_month"]["balance"]} грн
            - Фінансові звички: витрачає найбільше на {', '.join(profile["current_month"]["top_expense_categories"][:2])}
            
            Надайте детальну інвестиційну стратегію, яка включає:
            1. Розподіл коштів між різними типами інвестицій (з урахуванням можливостей в Україні)
            2. Конкретні інструменти для початківця (ОВДП, депозити, ETF, тощо)
            3. Часовий горизонт та очікувану дохідність
            4. 2-3 поради щодо вивчення інвестування для початківця
            
            Зробіть рекомендації реалістичними, з урахуванням поточного економічного стану в Україні.
            """
            
            # Виклик OpenAI API
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Ви - професійний інвестиційний радник, який надає персоналізовані поради українською мовою з урахуванням особливостей фінансового ринку України."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
            except Exception as model_error:
                logger.warning(f"Помилка використання GPT-4o: {model_error}. Використовуємо резервну модель.")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Ви - професійний інвестиційний радник, який надає персоналізовані поради українською мовою."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=800
                )
            
            investment_advice = response.choices[0].message.content.strip()
            
            # Зберігаємо пораду в базі даних
            save_financial_advice(self.user_id, investment_advice, "investment")
            
            return investment_advice
            
        except Exception as e:
            logger.error(f"Помилка при аналізі інвестиційних можливостей: {e}")
            return "На жаль, не вдалося проаналізувати інвестиційні можливості. Спробуйте пізніше або зверніться до команди підтримки."

def answer_financial_question(self, question):
        """Відповідь на фінансове запитання користувача з використанням OpenAI"""
        try:
            profile = self._generate_user_financial_profile()
            
            # Формуємо запит до OpenAI
            prompt = f"""
            Ви - професійний фінансовий консультант. На основі наведених даних та запитання користувача, 
            дайте коротку, інформативну відповідь.
            
            Дані про фінанси користувача за поточний місяць ({profile["month_name"]}):
            - Витрати: {profile["current_month"]["expenses"]} грн
            - Доходи: {profile["current_month"]["income"]} грн
            - Баланс: {profile["current_month"]["balance"]} грн
            - Найбільші категорії витрат: {', '.join(profile["current_month"]["top_expense_categories"][:3])}
            
            Запитання користувача: {question}
            
            Дайте чітку, корисну відповідь українською мовою, базуючись на даних користувача та загальних 
            знаннях про особисті фінанси.
            """
            
            # Виклик OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {"role": "system", "content": "Ви - професійний фінансовий консультант, який дає персоналізовані відповіді українською мовою."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Отримуємо текст відповіді
            answer_text = response.choices[0].message.content.strip()
            
            return answer_text
            
        except Exception as e:
            logger.error(f"Помилка при відповіді на фінансове запитання: {e}")
            return "На жаль, не вдалося відповісти на ваше запитання. Спробуйте переформулювати або зверніться до команди підтримки."

# Функції для використання у інших модулях
def get_financial_advice(user_id, advice_type="general"):
    """Отримання фінансової поради для користувача"""
    advisor = FinancialAdvisor(user_id)
    return advisor.generate_financial_advice(advice_type)

def answer_user_question(user_id, question):
    """Відповідь на фінансове питання користувача"""
    advisor = FinancialAdvisor(user_id)
    return advisor.answer_financial_question(question)

def get_investment_analysis(user_id):
    """Аналіз інвестиційних можливостей для користувача"""
    advisor = FinancialAdvisor(user_id)
    return advisor.analyze_investment_opportunities()
