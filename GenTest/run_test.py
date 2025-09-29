from test_generator import SimpleAITestGenerator
from multi_page_generator import MultiPageTestGenerator
import os
import sys

def check_environment():
    """Проверяет окружение и зависимости"""
    print("🔍 Проверяю окружение...")
    
    # Проверяем Python версию
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        return False
    
    # Проверяем установленные пакеты
    try:
        import selenium
        import llama_cpp
        print("✅ Все зависимости установлены")
    except ImportError as e:
        print(f"❌ Не установлены зависимости: {e}")
        print("📦 Установите: pip install -r requirements.txt")
        return False
    
    return True

def check_local_model():
    """Проверяет наличие локальной модели"""
    from config import Config
    
    config = Config()
    if config.AI_PROVIDER == "local":
        if not os.path.exists(config.LOCAL_MODEL_PATH):
            print(f"❌ Локальная модель не найдена: {config.LOCAL_MODEL_PATH}")
            print("\n📥 Чтобы скачать модель выполните:")
            print("mkdir models")
            print("wget -O models/codellama-7b.q4_0.gguf https://huggingface.co/TheBloke/CodeLlama-7B-GGUF/resolve/main/codellama-7b.q4_0.gguf")
            print("\nИли укажите путь к существующей модели в .env файле")
            return False
        else:
            print(f"✅ Локальная модель найдена: {config.LOCAL_MODEL_PATH}")
            return True
    else:
        # Проверяем OpenAI ключ
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == 'your-api-key-here':
            print("❌ Не настроен OpenAI API ключ")
            print("🔑 Добавьте OPENAI_API_KEY в .env файл")
            return False
        else:
            print("✅ OpenAI API ключ настроен")
            return True

def show_welcome():
    """Показывает приветственное сообщение"""
    print("🎯 AI Генератор авто-тестов")
    print("=" * 50)
    print("🤖 Поддержка: OpenAI GPT ИЛИ локальные GGUF модели")
    print("🌐 Автоматический анализ веб-страниц")
    print("💻 Генерация готовых Selenium тестов")
    print("=" * 50)

def select_test_type():
    """Выбор типа теста"""
    print("\n📋 Выберите тип теста:")
    print("1. 🟢 Простой тест (одна страница)")
    print("2. 🔵 Многостраничный тест (несколько страниц)")
    print("3. ⚙️  Настройки системы")
    print("4. ❌ Выход")
    
    while True:
        choice = input("\nВаш выбор (1-4): ").strip()
        if choice in ['1', '2', '3', '4']:
            return choice
        else:
            print("❌ Неверный выбор. Введите 1, 2, 3 или 4")

def run_simple_test():
    """Запускает генерацию простого теста"""
    print("\n🟢 РЕЖИМ: Простой тест (одна страница)")
    print("-" * 40)
    
    generator = SimpleAITestGenerator()
    
    try:
        print("\n📝 Введите данные для теста:")
        url = input("URL сайта: ").strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        scenario = input("Описание теста: ").strip()
        if not scenario:
            scenario = "тест основных элементов страницы"
        
        filename = input("Имя файла для теста (например: test_login.py): ").strip()
        if not filename:
            filename = "generated_test.py"
        if not filename.endswith('.py'):
            filename += '.py'
        
        print(f"\n🔄 Генерирую тест...")
        print(f"🌐 Сайт: {url}")
        print(f"🎯 Сценарий: {scenario}")
        print(f"💾 Файл: {filename}")
        print("⏳ Это может занять несколько минут...")
        
        # Генерируем тест
        test_code = generator.generate_simple_test(scenario, url)
        
        # Сохраняем тест
        saved_path = generator.save_test(test_code, filename)
        
        print(f"\n✅ Тест успешно создан!")
        print(f"📁 Файл: {saved_path}")
        print(f"📊 Размер: {len(test_code)} символов")
        
        # Спрашиваем хочет ли пользователь запустить тест
        run_test = input("\n🚀 Запустить тест сейчас? (y/n): ").strip().lower()
        if run_test == 'y':
            print("\n🔧 Запускаю тест...")
            print("-" * 40)
            try:
                exec(compile(test_code, saved_path, 'exec'))
                print("-" * 40)
                print("🎉 Тест выполнен успешно!")
            except Exception as e:
                print(f"❌ Ошибка выполнения теста: {e}")
                print("💡 Вы можете отредактировать сгенерированный код и запустить снова")
        
        # Предлагаем открыть файл
        open_file = input("\n📂 Открыть файл с тестом? (y/n): ").strip().lower()
        if open_file == 'y':
            try:
                if os.name == 'nt':  # Windows
                    os.system(f'notepad "{saved_path}"')
                else:  # Linux/Mac
                    os.system(f'xdg-open "{saved_path}"')
            except:
                print("❌ Не удалось открыть файл")
        
    except Exception as e:
        print(f"❌ Ошибка при генерации теста: {e}")
        print("💡 Проверьте URL и подключение к интернету")
    finally:
        generator.close()

def run_multi_page_test():
    """Запускает генерацию многостраничного теста"""
    print("\n🔵 РЕЖИМ: Многостраничный тест")
    print("-" * 40)
    
    generator = MultiPageTestGenerator()
    
    try:
        print("\n📝 Введите данные для теста:")
        url = input("Стартовый URL: ").strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        print("\n📋 Примеры многостраничных сценариев:")
        print("• 'зарегистрироваться, войти, добавить товар в корзину, оформить заказ'")
        print("• 'найти товар через поиск, отфильтровать, посмотреть детали, добавить в избранное'")
        print("• 'заполнить форму, отправить, проверить подтверждение'")
        
        scenario = input("\nОпишите ваш сценарий: ").strip()
        if not scenario:
            scenario = "протестировать основные функции сайта"
        
        filename = input("Имя файла для теста: ").strip()
        if not filename:
            filename = "multi_page_test.py"
        if not filename.endswith('.py'):
            filename += '.py'
        
        # Генерируем имя функции из имени файла
        test_function_name = filename.replace('.py', '').replace(' ', '_')
        
        print(f"\n🔄 Генерирую многостраничный тест...")
        print(f"🌐 Старт: {url}")
        print(f"📋 Сценарий: {scenario}")
        print(f"💾 Файл: {filename}")
        print("⏳ Это может занять несколько минут...")
        
        # Генерируем тест
        test_code = generator.generate_multi_page_test(scenario, url, test_function_name)
        
        # Сохраняем тест
        saved_path = generator.save_test(test_code, filename)
        
        print(f"\n✅ Многостраничный тест успешно создан!")
        print(f"📁 Файл: {saved_path}")
        print(f"📊 Размер: {len(test_code)} символов")
        print(f"🔢 Шагов: {test_code.count('# Шаг')}")
        
        # Спрашиваем хочет ли пользователь запустить тест
        run_test = input("\n🚀 Запустить тест сейчас? (y/n): ").strip().lower()
        if run_test == 'y':
            print("\n🔧 Запускаю многостраничный тест...")
            print("-" * 40)
            try:
                exec(compile(test_code, saved_path, 'exec'))
                print("-" * 40)
                print("🎉 Многостраничный тест выполнен успешно!")
            except Exception as e:
                print(f"❌ Ошибка выполнения теста: {e}")
                print("💡 Сложные сценарии могут требовать ручной доработки")
        
    except Exception as e:
        print(f"❌ Ошибка при генерации теста: {e}")
        print("💡 Проверьте URL и описание сценария")
    finally:
        generator.close()

def show_settings():
    """Показывает настройки системы"""
    from config import Config
    
    config = Config()
    
    print("\n⚙️  НАСТРОЙКИ СИСТЕМЫ")
    print("-" * 40)
    print(f"🤖 AI провайдер: {config.AI_PROVIDER}")
    
    if config.AI_PROVIDER == "local":
        print(f"📁 Локальная модель: {config.LOCAL_MODEL_PATH}")
        if os.path.exists(config.LOCAL_MODEL_PATH):
            file_size = os.path.getsize(config.LOCAL_MODEL_PATH) / (1024**3)  # GB
            print(f"📊 Размер модели: {file_size:.2f} GB")
        else:
            print("❌ Модель не найдена")
    else:
        print(f"🌐 OpenAI модель: {config.OPENAI_MODEL}")
    
    print(f"🌐 Браузер: {config.BROWSER}")
    print(f"👻 Headless режим: {config.HEADLESS}")
    print(f"⏱️ Таймаут страницы: {config.PAGE_LOAD_TIMEOUT} сек")
    print(f"📁 Папка тестов: {config.GENERATED_TESTS_DIR}")
    
    print("\n📋 Чтобы изменить настройки, отредактируйте:")
    print("1. Файл .env - основные настройки")
    print("2. Файл config.py - расширенные настройки")
    
    input("\nНажмите Enter чтобы продолжить...")

def show_examples():
    """Показывает примеры использования"""
    print("\n📚 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ")
    print("-" * 40)
    
    print("\n🟢 ПРОСТЫЕ ТЕСТЫ:")
    print("URL: https://demoqa.com/login")
    print("Сценарий: 'тест логина пользователя'")
    print("→ Создаст тест входа в систему")
    
    print("\nURL: https://www.saucedemo.com")
    print("Сценарий: 'поиск товаров'") 
    print("→ Создаст тест поиска и фильтрации")
    
    print("\n🔵 МНОГОСТРАНИЧНЫЕ ТЕСТЫ:")
    print("URL: https://demoblaze.com")
    print("Сценарий: 'зарегистрироваться, войти, выбрать ноутбук, добавить в корзину'")
    print("→ Создаст полный e-commerce тест")
    
    print("\nURL: https://demoqa.com/automation-practice-form")
    print("Сценарий: 'заполнить форму регистрации по шагам'")
    print("→ Создаст тест сложной формы")
    
    print("\n💡 СОВЕТЫ:")
    print("• Используйте демо-сайты для тестирования системы")
    print("• Начинайте с простых сценариев")
    print("• Проверяйте сгенерированный код перед использованием")
    
    input("\nНажмите Enter чтобы продолжить...")

def main():
    """Главная функция"""
    
    # Показываем приветствие
    show_welcome()
    
    # Проверяем окружение
    if not check_environment():
        return
    
    # Проверяем модель/ключ
    if not check_local_model():
        return
    
    # Главный цикл
    while True:
        try:
            choice = select_test_type()
            
            if choice == '1':
                run_simple_test()
            elif choice == '2':
                run_multi_page_test()
            elif choice == '3':
                show_settings()
            elif choice == '4':
                print("\n👋 До свидания!")
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 Прервано пользователем. До свидания!")
            break
        except Exception as e:
            print(f"\n❌ Неожиданная ошибка: {e}")
            print("💡 Попробуйте еще раз или проверьте настройки")
        
        # Пауза между операциями
        input("\nНажмите Enter чтобы продолжить...")

if __name__ == "__main__":
    main()