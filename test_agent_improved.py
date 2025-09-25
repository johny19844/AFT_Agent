#!/usr/bin/env python3
"""
Тестовый скрипт для проверки улучшенного агента
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_agent_configuration():
    """Тестирование конфигурации агента"""
    print("🔧 Тестирование конфигурации агента...")
    
    # Проверяем переменные окружения
    github_token = os.getenv('GITHUB_TOKEN', 'your_github_token_here')
    github_username = os.getenv('GITHUB_USERNAME', 'your_username')
    scenario_repo = os.getenv('SCENARIO_REPO', 'johny19844/scenario')
    aft_repo = os.getenv('AFT_REPO', 'johny19844/AFT')
    
    print(f"📝 GitHub Token: {'✅ Установлен' if github_token != 'your_github_token_here' else '❌ Не установлен'}")
    print(f"👤 GitHub Username: {github_username}")
    print(f"📂 Scenario Repo: {scenario_repo}")
    print(f"📂 AFT Repo: {aft_repo}")
    
    if github_token == 'your_github_token_here':
        print("❌ GitHub токен не установлен!")
        print("Создайте файл .env и добавьте:")
        print("GITHUB_TOKEN=your_actual_token_here")
        return False
    
    return True

def test_agent_import():
    """Тестирование импорта агента"""
    print("\n🔧 Тестирование импорта агента...")
    
    try:
        # Импортируем агента
        from agent_v0_1 import TestAutomationAgent, GGUFModelClient
        print("✅ Агент успешно импортирован")
        
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
    """Тестирование инициализации агента"""
    print("\n🔧 Тестирование инициализации агента...")
    
    try:
        from agent_v0_1 import TestAutomationAgent
        
        # Тестовые параметры
        github_token = os.getenv('GITHUB_TOKEN', 'your_github_token_here')
        if github_token == 'your_github_token_here':
            print("❌ GitHub токен не установлен, пропускаем тест инициализации")
            return False
        
        agent = TestAutomationAgent(
            github_token=github_token,
            jenkins_url="http://localhost:8080",
            jenkins_username="admin",
            jenkins_token="dummy_token",
            model_path="./models/yandex-gpt.gguf",
            github_username="johny19844",
            scenario_repo="johny19844/scenario",
            aft_repo="johny19844/AFT"
        )
        
        print("✅ Агент успешно инициализирован")
        print(f"📂 Scenario Repo: {agent.scenario_repo_name}")
        print(f"📂 AFT Repo: {agent.aft_repo_name}")
        print(f"🤖 Model Client: {type(agent.model_client).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование улучшенного агента автоматизации тестирования")
    print("=" * 60)
    
    tests = [
        ("Конфигурация", test_agent_configuration),
        ("Импорт", test_agent_import),
        ("Инициализация", test_agent_initialization)
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
        print("\n📝 Для запуска агента выполните:")
        print("python agent_v0.1.py")
        return True
    else:
        print("💥 Некоторые тесты не пройдены")
        print("\n🔧 Проверьте:")
        print("1. Установлен ли GitHub токен в .env файле")
        print("2. Существует ли модель в ./models/yandex-gpt.gguf")
        print("3. Установлены ли все зависимости")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
