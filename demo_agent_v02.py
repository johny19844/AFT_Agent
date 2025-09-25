#!/usr/bin/env python3
"""
Демонстрационный скрипт для агента v0.2
Показывает работу агента в реальном времени
"""

import os
import sys
import time
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def demo_agent():
    """Демонстрация работы агента"""
    print("🚀 Демонстрация агента автоматизации тестирования v0.2")
    print("=" * 60)
    
    try:
        import agent_v02
        
        # Получаем токен
        github_token = os.getenv('GITHUB_TOKEN', 'your_github_token_here')
        if github_token == 'your_github_token_here':
            print("❌ GitHub токен не установлен!")
            print("Создайте файл .env и добавьте:")
            print("GITHUB_TOKEN=your_actual_token_here")
            return False
        
        print("✅ GitHub токен найден")
        
        # Создаем агента
        print("🤖 Создание агента...")
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
        print(f"📂 Мониторинг: {agent.scenario_repo_name}")
        print(f"📂 Целевой репозиторий: {agent.aft_repo_name}")
        
        # Демонстрируем одно сканирование
        print("\n🔍 Выполняем сканирование репозитория...")
        changed_files = agent.scan_scenario_repository()
        
        if changed_files:
            print(f"📊 Обнаружено {len(changed_files)} файлов для обработки:")
            for file in changed_files:
                print(f"  - {file}")
            
            print("\n🔄 Обрабатываем файлы...")
            for filename in changed_files:
                print(f"\n📝 Обработка: {filename}")
                success = agent.process_scenario(filename)
                if success:
                    print(f"✅ {filename} - успешно обработан")
                else:
                    print(f"❌ {filename} - ошибка обработки")
        else:
            print("ℹ️ Изменений не обнаружено")
        
        print("\n🎉 Демонстрация завершена!")
        print("\n📝 Для непрерывной работы запустите:")
        print("python agent_v02.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_help():
    """Показать справку"""
    print("🚀 Агент автоматизации тестирования v0.2")
    print("=" * 50)
    print()
    print("📋 Доступные команды:")
    print("  python demo_agent_v02.py        - Демонстрация работы")
    print("  python agent_v02.py             - Запуск агента")
    print("  python test_agent_v0.2.py       - Тестирование")
    print("  python test_scenario_detection.py - Тест обнаружения")
    print()
    print("📚 Документация:")
    print("  AGENT_V0.2_GUIDE.md             - Руководство")
    print("  README_IMPROVED.md              - Общая документация")
    print()
    print("🔧 Конфигурация:")
    print("  .env                             - Настройки")
    print("  requirements.txt                - Зависимости")

def main():
    """Основная функция"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        show_help()
        return True
    
    print("Выберите режим работы:")
    print("1. Демонстрация работы агента")
    print("2. Показать справку")
    print("3. Выход")
    
    try:
        choice = input("\nВведите номер (1-3): ").strip()
        
        if choice == "1":
            return demo_agent()
        elif choice == "2":
            show_help()
            return True
        elif choice == "3":
            print("👋 До свидания!")
            return True
        else:
            print("❌ Неверный выбор")
            return False
            
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
