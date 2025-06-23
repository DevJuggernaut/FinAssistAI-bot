# Встановлення Tesseract OCR для розпізнавання чеків

## macOS

```bash
# Встановлення через Homebrew
brew install tesseract

# Встановлення української мови
brew install tesseract-lang
```

## Ubuntu/Debian

```bash
# Встановлення Tesseract
sudo apt-get update
sudo apt-get install tesseract-ocr

# Встановлення української мови
sudo apt-get install tesseract-ocr-ukr
```

## Windows

1. Завантажити з https://github.com/UB-Mannheim/tesseract/wiki
2. Встановити згідно інструкцій
3. Додати до PATH системи

## Перевірка встановлення

```bash
tesseract --version
tesseract --list-langs
```

Повинно показувати `ukr` та `eng` в списку мов.

## Тестування

```bash
# Тестування на фото чеку
python test_mida_receipt.py /шлях/до/фото/чеку.jpg
```

## Додаткові пакети Python

```bash
pip install pytesseract pillow
```

## Поради для кращого розпізнавання:

1. Фотографуйте чек при хорошому освітленні
2. Тримайте телефон рівно над чеком
3. Переконайтеся, що весь чек поміщається в кадр
4. Уникайте тіней та відблисків
5. Чек повинен бути розправлений (без складок)
