# Агент автоматизации тестирования v0.2

## 🚀 Новые возможности

### ✨ Улучшенное отслеживание изменений
- **Умное отслеживание**: Отслеживает изменения файлов по SHA-хешу и дате модификации
- **Рекурсивное сканирование**: Поддерживает поддиректории в репозитории сценариев
- **Оптимизация**: Обрабатывает только действительно измененные файлы

### 📝 Улучшенное логирование
- **Эмодзи-логи**: Визуально понятные сообщения с эмодзи
- **Детальная информация**: Подробные логи процесса обработки
- **Информативные коммиты**: Сообщения коммитов с временными метками

### 🔧 Оптимизированная работа
- **Проверка дублирования**: Не обновляет файлы, если код не изменился
- **Улучшенная обработка ошибок**: Более детальная диагностика проблем
- **Автоматическая очистка**: Очистка временных файлов после обработки

## 📁 Структура файлов

```
AFT_Agent/
├── agent_v0.1.py          # Оригинальная версия (без изменений)
├── agent_v0.2.py          # Новая улучшенная версия
├── test_agent_v0.2.py     # Тесты для v0.2
├── requirements.txt       # Зависимости
├── .env                   # Конфигурация (создать)
├── models/
│   └── yandex-gpt.gguf   # Модель GGUF
└── README_IMPROVED.md     # Документация
```

## 🛠️ Установка и настройка

### 1. Активация виртуального окружения

```bash
.venv\Scripts\activate
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Создание конфигурации

Создайте файл `.env`:

```env
# GitHub Configuration
GITHUB_TOKEN=your_github_token_here
GITHUB_USERNAME=johny19844

# Jenkins Configuration (optional)
JENKINS_URL=http://localhost:8080
JENKINS_USERNAME=admin
JENKINS_TOKEN=your_jenkins_token

# Model Configuration
MODEL_PATH=./models/yandex-gpt.gguf

# Repository Configuration
SCENARIO_REPO=johny19844/scenario
AFT_REPO=johny19844/AFT
```

## 🧪 Тестирование

### Запуск тестов

```bash
python test_agent_v0.2.py
```

### Ожидаемый вывод

```
🚀 Тестирование агента автоматизации тестирования v0.2
============================================================

📋 Тест: Конфигурация
----------------------------------------
✅ Конфигурация - ПРОЙДЕН

📋 Тест: Импорт
----------------------------------------
✅ Импорт - ПРОЙДЕН

📋 Тест: Инициализация
----------------------------------------
✅ Инициализация - ПРОЙДЕН

📋 Тест: Загрузка модели
----------------------------------------
✅ Загрузка модели - ПРОЙДЕН

============================================================
📊 Результаты: 4/4 тестов пройдено
🎉 Все тесты пройдены успешно!
```

## 🚀 Запуск агента

### Основной запуск

```bash
python agent_v0.2.py
```

### Ожидаемый вывод

```
2024-01-15 10:30:00 - INFO - 🚀 Starting Test Automation Agent v0.2
2024-01-15 10:30:00 - INFO - 📂 Monitoring: johny19844/scenario
2024-01-15 10:30:00 - INFO - 📂 Target: johny19844/AFT
2024-01-15 10:30:00 - INFO - ⏰ Scan interval: 300 seconds
2024-01-15 10:30:00 - INFO - 🔗 Connected to GitHub as: johny19844
2024-01-15 10:30:00 - INFO - 🤖 Loading GGUF model...
2024-01-15 10:30:01 - INFO - ✅ GGUF model successfully loaded!
2024-01-15 10:30:01 - INFO - 🔍 Scanning repository: johny19844/scenario
2024-01-15 10:30:02 - INFO - 📊 Found 0 changed files: []
2024-01-15 10:30:02 - INFO - ℹ️ No changes detected
2024-01-15 10:30:02 - INFO - ⏳ Waiting 300 seconds until next scan...
```

## 🔄 Как это работает

### 1. Сканирование репозитория
- Агент каждые 5 минут сканирует `johny19844/scenario`
- Проверяет SHA-хеши и даты модификации файлов
- Обнаруживает только действительно измененные файлы

### 2. Обработка изменений
- Скачивает измененные файлы сценариев
- Генерирует Java тесты с помощью GGUF модели
- Валидирует сгенерированный код

### 3. Обновление AFT репозитория
- Загружает тесты в `johny19844/AFT`
- Создает информативные коммиты
- Пропускает обновления, если код не изменился

## 📊 Мониторинг

### Логи изменений файлов

```
2024-01-15 10:35:00 - INFO - 🔍 Scanning repository: johny19844/scenario
2024-01-15 10:35:01 - INFO - 📝 File changed: login_test.txt
2024-01-15 10:35:01 - INFO - 📊 Found 1 changed files: ['login_test.txt']
2024-01-15 10:35:01 - INFO - 🔄 Processing 1 changed files: ['login_test.txt']
2024-01-15 10:35:01 - INFO - 📝 Processing file: login_test.txt
```

### Логи генерации тестов

```
2024-01-15 10:35:02 - INFO - ⬇️ Downloading scenario file: login_test.txt
2024-01-15 10:35:03 - INFO - ✅ File downloaded successfully: login_test.txt
2024-01-15 10:35:03 - INFO - 🤖 Generating Java test code for: login_test
2024-01-15 10:35:05 - INFO - ✅ Generated valid code for login_testTest
```

### Логи обновления AFT

```
2024-01-15 10:35:06 - INFO - 📤 Pushing to AFT repository: LoginTestTest.java
2024-01-15 10:35:07 - INFO - ✅ Updated file: src/test/java/tests/LoginTestTest.java
2024-01-15 10:35:07 - INFO - 📝 Commit: Auto-update test: LoginTestTest.java
```

## 🔧 Устранение неполадок

### Ошибка "Repository not found"
```
❌ Repository johny19844/scenario not found!
Please check:
1. Repository exists
2. You have access to it
3. Format is 'username/repository-name'
```

**Решение**: Проверьте правильность имени репозитория и права доступа

### Ошибка "Model loading failed"
```
❌ Failed to load model: [Errno 2] No such file or directory: './models/yandex-gpt.gguf'
```

**Решение**: Убедитесь, что файл модели существует в указанном пути

### Ошибка "GitHub connection failed"
```
❌ GitHub connection failed: 401 {'message': 'Bad credentials', 'documentation_url': 'https://docs.github.com/rest'}
```

**Решение**: Проверьте правильность GitHub токена в файле `.env`

## 📈 Преимущества v0.2

1. **Производительность**: Обрабатывает только измененные файлы
2. **Надежность**: Улучшенная обработка ошибок и валидация
3. **Мониторинг**: Детальные логи для отслеживания работы
4. **Оптимизация**: Пропускает ненужные обновления
5. **Совместимость**: Сохраняет оригинальную версию v0.1

## 🔄 Миграция с v0.1

1. **Сохранение**: Оригинальный `agent_v0.1.py` остается без изменений
2. **Тестирование**: Используйте `test_agent_v0.2.py` для проверки
3. **Запуск**: Замените `agent_v0.1.py` на `agent_v0.2.py` в команде запуска
4. **Конфигурация**: Используйте тот же файл `.env`

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи агента
2. Запустите тесты: `python test_agent_v0.2.py`
3. Проверьте конфигурацию в `.env`
4. Убедитесь в доступности репозиториев
