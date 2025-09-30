from ai_test_generator import AILocatorFinder
import os
import sys

def main():
    print("🎯 AI Анализ тестовых сценариев и поиск локаторов")
    print("=" * 50)
    print("📋 ШАГ 1: AI анализирует сценарий")
    print("🌐 ШАГ 2: Selenium собирает информацию о странице") 
    print("🔍 ШАГ 3: AI находит локаторы для элементов")
    print("📊 ШАГ 4: Генерация полного отчета")
    print("=" * 50)
    
    if not check_environment():
        return
    
    finder = AILocatorFinder()
    
    try:
        print("\n📝 Введите данные для анализа:")
        url = input("URL сайта: ").strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        print("\n💡 Примеры тестовых сценариев:")
        print("• 'Вход пользователя standard_user с паролем secret_sauce'")
        print("• 'Поиск товара по названию и добавление в корзину'") 
        print("• 'Регистрация нового пользователя с email и паролем'")
        print("• 'Заполнение контактной формы и отправка'")
        
        scenario = input("\nОпишите тестовый сценарий: ").strip()
        if not scenario:
            scenario = "Тестирование основных функций страницы"
        
        filename = input("Имя файла для отчета: ").strip()
        if not filename:
            filename = "full_analysis_report.md"
        if not filename.endswith('.md'):
            filename += '.md'
        
        print(f"\n🚀 Запускаю анализ...")
        print(f"🌐 URL: {url}")
        print(f"📝 Сценарий: {scenario}")
        
        # Запускаем полный анализ
        analysis_result = finder.complete_analysis(scenario, url)
        
        if analysis_result:
            # Сохраняем отчет
            saved_path = finder.save_analysis_report(analysis_result, filename)
            
            print(f"\n✅ Анализ завершен успешно!")
            print(f"📁 Полный отчет сохранен: {saved_path}")
            print(f"🎯 Найдено локаторов для {len(analysis_result['elements_with_locators'])} элементов")
            
            # Краткий вывод результатов
            print("\n📋 КРАТКИЕ РЕЗУЛЬТАТЫ:")
            for item in analysis_result['elements_with_locators']:
                element_info = item['element_info']
                locator_info = item['locator_info']
                
                if "error" not in locator_info and locator_info.get('locators'):
                    best_locator = locator_info['locators'][0]
                    print(f"   ✅ {element_info['name']}: {best_locator['type']} = '{best_locator['value']}'")
                else:
                    print(f"   ❌ {element_info['name']}: не найден")
        
        else:
            print("❌ Анализ не удался")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        finder.close()

def check_environment():
    """Проверяет окружение"""
    try:
        import selenium
        import llama_cpp
        return True
    except ImportError as e:
        print(f"❌ Не установлены зависимости: {e}")
        return False

if __name__ == "__main__":
    main()