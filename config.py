import os
from dotenv import load_dotenv

load_dotenv()

# Telegram credentials
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# OpenAI credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Other settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
