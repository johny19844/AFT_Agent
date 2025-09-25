#!/usr/bin/env python3
"""
Тестовый скрипт для проверки обнаружения сценариев
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_scenario_detection():
    """Тестирование обнаружения сценариев"""
    print("🔧 Тестирование обнаружения сценариев...")
    
    try:
        import agent_v02
        
        # Получаем токен
        github_token = os.getenv('GITHUB_TOKEN', 'your_github_token_here')
        if github_token == 'your_github_token_here':
            print("❌ GitHub токен не установлен!")
            return False
        
        # Создаем агента
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
        
        print("✅ Агент создан успешно")
        
        # Тестируем сканирование репозитория
        print("🔍 Тестируем сканирование репозитория...")
        changed_files = agent.scan_scenario_repository()
        
        print(f"📊 Найдено файлов: {len(changed_files)}")
        print(f"📝 Файлы: {list(changed_files)}")
        
        if changed_files:
            print("✅ Обнаружены файлы для обработки")
            
            # Тестируем обработку первого файла
            first_file = list(changed_files)[0]
            print(f"🔄 Тестируем обработку файла: {first_file}")
            
            success = agent.process_scenario(first_file)
            if success:
                print(f"✅ Файл {first_file} успешно обработан")
            else:
                print(f"❌ Ошибка обработки файла {first_file}")
        else:
            print("ℹ️ Файлы не обнаружены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_github_connection():
    """Тестирование подключения к GitHub"""
    print("\n🔧 Тестирование подключения к GitHub...")
    
    try:
        from github import Github
        
        github_token = os.getenv('GITHUB_TOKEN', 'your_github_token_here')
        if github_token == 'your_github_token_here':
            print("❌ GitHub токен не установлен!")
            return False
        
        github_client = Github(github_token)
        user = github_client.get_user()
        print(f"✅ Подключен к GitHub как: {user.login}")
        
        # Проверяем доступ к репозиториям
        scenario_repo = github_client.get_repo("johny19844/scenario")
        print(f"✅ Доступ к репозиторию сценариев: {scenario_repo.full_name}")
        
        aft_repo = github_client.get_repo("johny19844/AFT")
        print(f"✅ Доступ к репозиторию AFT: {aft_repo.full_name}")
        
        # Получаем список файлов в репозитории сценариев
        contents = scenario_repo.get_contents("")
        txt_files = []
        
        for content in contents:
            if content.type == "file" and content.name.endswith('.txt'):
                txt_files.append(content.name)
            elif content.type == "dir":
                sub_contents = scenario_repo.get_contents(content.path)
                for sub_content in sub_contents:
                    if sub_content.type == "file" and sub_content.name.endswith('.txt'):
                        txt_files.append(sub_content.path)
        
        print(f"📝 Найдено .txt файлов: {len(txt_files)}")
        for file in txt_files:
            print(f"  - {file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к GitHub: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование обнаружения сценариев")
    print("=" * 50)
    
    tests = [
        ("Подключение к GitHub", test_github_connection),
        ("Обнаружение сценариев", test_scenario_detection)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Тест: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                print(f"✅ {test_name} - ПРОЙДЕН")
                passed += 1
            else:
                print(f"❌ {test_name} - НЕ ПРОЙДЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        return True
    else:
        print("💥 Некоторые тесты не пройдены")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
