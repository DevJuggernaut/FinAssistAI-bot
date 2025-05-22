from setuptools import setup, find_packages

setup(
    name="finassist-bot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot',
        'sqlalchemy',
        'psycopg2-binary',
        'python-dotenv',
        'openai'
    ],
) 