<img src="lingua.png" alt="Логотип" align="right" width="200"/>

# Lingua — Твой Discord помощник

Централизация чаще всего зло, поэтому теперь этот бот — полностью open-source.

## 📌 Возможности
- Отвечает на вопросы с помощью AI.
- Поддержка OpenAI / OpenRouter.
- Минималистичный, без лишних зависимостей.

## 🚀 Установка

1. **Клонируйте репозиторий**
   ```bash
   git clone git@github.com:atarwn/Lingua.git
   cd Lingua
   ```
   
2. **Создайте и активируйте виртуальное окружение**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Для bash/zsh
   ```

   _Для других оболочек:_
   ```bash
   source .venv/bin/activate.fish  # Fish
   source .venv/bin/activate.csh   # CSH/TCSH
   source .venv/bin/activate.bat   # Windows CMD
   source .venv/bin/activate.ps1   # PowerShell
   ```

3. **Установите зависимости**
   ```bash
   pip install -r req.txt
   ```

4. **Заполните файл `.env`**
   ```ini
   BOT_TOKEN = MTqVsuPerSeCREtbOtToken
   OPENAI_KEY = sk-supersecretopenaitoken
   API_URL = https://openrouter.ai/api/v1
   ```

   > *Примечание:* Ключи здесь невалидные, замените их на свои.

5. **Запустите бота**
   ```bash
   python app.py
   ```

## 🤝 Участие в проекте

Хотите помочь? Отлично!
- Присылайте PR с исправлениями или фичами.
- Оставляйте [issues](https://github.com/atarwn/Lingua/issues).
- Пишите предложения.

## 📝 Лицензия

Проект распространяется под [Qwaderton License](LICENSE).
