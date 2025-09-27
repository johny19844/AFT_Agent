# Улучшенный агент автоматизации тестирования

## Описание

Этот агент автоматически отслеживает изменения в репозитории сценариев `johny19844/scenario` и генерирует соответствующие автотесты в репозитории `johny19844/AFT`.

## Новые возможности

### 🔄 Умное отслеживание изменений
- Отслеживает изменения файлов по SHA-хешу и дате модификации
- Обрабатывает только действительно измененные файлы
- Поддерживает рекурсивное сканирование поддиректорий

### 📝 Улучшенное логирование
- Детальные логи с эмодзи для лучшей читаемости
- Информативные сообщения коммитов
- Отслеживание процесса обработки файлов

### 🚀 Оптимизированная работа
- Проверка на дублирование кода перед обновлением
- Улучшенная обработка ошибок
- Автоматическая очистка временных файлов

## Установка и настройка

### 1. Установка зависимостей

```bash
# Активируйте виртуальное окружение
.venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

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

### 3. Настройка GitHub токена

1. Перейдите в GitHub → Settings → Developer settings → Personal access tokens
2. Создайте новый токен с правами:
   - `repo` (полный доступ к репозиториям)
   - `workflow` (для работы с GitHub Actions)
3. Скопируйте токен в файл `.env`

## Использование

### Запуск агента

```bash
python agent_v0.1.py
```

### Тестирование конфигурации

```bash
python test_agent_improved.py
```

## Как это работает

1. **Сканирование**: Агент каждые 5 минут сканирует репозиторий `johny19844/scenario`
2. **Обнаружение изменений**: Сравнивает SHA-хеши и даты модификации файлов
3. **Генерация тестов**: Использует GGUF модель для генерации Java тестов
4. **Обновление AFT**: Загружает сгенерированные тесты в `johny19844/AFT`

## Структура репозиториев

### Репозиторий сценариев (`johny19844/scenario`)
```
scenario/
├── login_test.txt
├── registration_test.txt
└── checkout_test.txt
```

### Репозиторий автотестов (`johny19844/AFT`)
```
AFT/
└── src/
    └── test/
        └── java/
            └── tests/
                ├── LoginTestTest.java
                ├── RegistrationTestTest.java
                └── CheckoutTestTest.java
```

## Логирование

Агент выводит подробные логи:

```
🔄 Обнаружены измененные файлы: ['login_test.txt']
📝 Обработка файла: login_test.txt
✅ Успешно обработан: login_test.txt
✅ Обновлен файл: src/test/java/tests/LoginTestTest.java
📝 Коммит: Auto-update test: LoginTestTest.java
```

## Устранение неполадок

### Ошибка "Repository not found"
- Проверьте правильность имени репозитория
- Убедитесь, что у вас есть доступ к репозиторию
- Проверьте GitHub токен

### Ошибка "Model loading failed"
- Убедитесь, что файл модели существует: `./models/yandex-gpt.gguf`
- Проверьте права доступа к файлу

### Ошибка "GitHub connection failed"
- Проверьте правильность GitHub токена
- Убедитесь, что токен имеет необходимые права

## Требования

- Python 3.8+
- GitHub токен с правами на репозитории
- GGUF модель (yandex-gpt.gguf)
- Доступ к интернету для работы с GitHub API
