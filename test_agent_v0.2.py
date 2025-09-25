#!/usr/bin/env python3
"""
Тестовый скрипт для агента v0.2
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_agent_configuration():
    """Тестирование конфигурации агента v0.2"""
    print("🔧 Тестирование конфигурации агента v0.2...")
    
    # Проверяем переменные окружения
    github_token = os.getenv('GITHUB_TOKEN', 'your_github_token_here')
    github_username = os.getenv('GITHUB_USERNAME', 'johny19844')
    scenario_repo = os.getenv('SCENARIO_REPO', 'johny19844/scenario')
    aft_repo = os.getenv('AFT_REPO', 'johny19844/AFT')
    model_path = os.getenv('MODEL_PATH', './models/yandex-gpt.gguf')
    
    print(f"📝 GitHub Token: {'✅ Установлен' if github_token != 'your_github_token_here' else '❌ Не установлен'}")
    print(f"👤 GitHub Username: {github_username}")
    print(f"📂 Scenario Repo: {scenario_repo}")
    print(f"📂 AFT Repo: {aft_repo}")
    print(f"🤖 Model Path: {model_path}")
    print(f"📁 Model Exists: {'✅ Да' if os.path.exists(model_path) else '❌ Нет'}")
    
    if github_token == 'your_github_token_here':
        print("❌ GitHub токен не установлен!")
        print("Создайте файл .env и добавьте:")
        print("GITHUB_TOKEN=your_actual_token_here")
        return False
    
    if not os.path.exists(model_path):
        print(f"❌ Модель не найдена: {model_path}")
        return False
    
    return True

def test_agent_import():
    """Тестирование импорта агента v0.2"""
    print("\n🔧 Тестирование импорта агента v0.2...")
    
    try:
        # Импортируем агента v0.2
        import sys
        sys.path.append('.')
        import agent_v02
        print("✅ Агент v0.2 успешно импортирован")
        
        # Проверяем наличие модели
        model_path = "./models/yandex-gpt.gguf"
        if os.path.exists(model_path):
            print(f"✅ Модель найдена: {model_path}")
        else:
            print(f"❌ Модель не найдена: {model_path}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_agent_initialization():
    """Тестирование инициализации агента v0.2"""
    print("\n🔧 Тестирование инициализации агента v0.2...")
    
    try:
        import agent_v02
        
        # Тестовые параметры
        github_token = os.getenv('GITHUB_TOKEN', 'your_github_token_here')
        if github_token == 'your_github_token_here':
            print("❌ GitHub токен не установлен, пропускаем тест инициализации")
            return False
        
        agent = agent_v02.TestAutomationAgent(
            github_token=github_token,
            jenkins_url="http://localhost:8080",
            jenkins_username="admin",
            jenkins_token="dummy_token",
            model_path="./models/yandex-gpt.gguf",
            github_username="johny19844",
            scenario_repo="johny19844/scenario",
            aft_repo="johny19844/AFT"
        )
        
        print("✅ Агент v0.2 успешно инициализирован")
        print(f"📂 Scenario Repo: {agent.scenario_repo_name}")
        print(f"📂 AFT Repo: {agent.aft_repo_name}")
        print(f"🤖 Model Client: {type(agent.model_client).__name__}")
        print(f"📊 File Tracking: {len(agent.file_tracking)} files tracked")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False

def test_model_loading():
    """Тестирование загрузки модели"""
    print("\n🔧 Тестирование загрузки модели...")
    
    try:
        import agent_v02
        
        model_client = agent_v02.GGUFModelClient("./models/yandex-gpt.gguf")
        
        if model_client.load_model():
            print("✅ Модель успешно загружена")
            
            # Тестируем генерацию
            test_prompt = "Напиши простой Java тест для проверки веб-страницы"
            result = model_client.generate_text(test_prompt, max_tokens=100)
            
            if result:
                print("✅ Генерация текста работает")
                print(f"📝 Результат (первые 200 символов): {result[:200]}...")
            else:
                print("⚠️ Генерация текста не работает")
            
            return True
        else:
            print("❌ Не удалось загрузить модель")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании модели: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование агента автоматизации тестирования v0.2")
    print("=" * 60)
    
    tests = [
        ("Конфигурация", test_agent_configuration),
        ("Импорт", test_agent_import),
        ("Инициализация", test_agent_initialization),
        ("Загрузка модели", test_model_loading)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Тест: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                print(f"✅ {test_name} - ПРОЙДЕН")
                passed += 1
            else:
                print(f"❌ {test_name} - НЕ ПРОЙДЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        print("\n📝 Для запуска агента v0.2 выполните:")
        print("python agent_v0.2.py")
        print("\n📚 Документация:")
        print("README_IMPROVED.md")
        return True
    else:
        print("💥 Некоторые тесты не пройдены")
        print("\n🔧 Проверьте:")
        print("1. Установлен ли GitHub токен в .env файле")
        print("2. Существует ли модель в ./models/yandex-gpt.gguf")
        print("3. Установлены ли все зависимости")
        print("4. Правильно ли настроены репозитории")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
