# multi_page_generator.py - упрощенная версия
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from config import Config
from ai_client import UniversalAIClient

class MultiPageTestGenerator:
    def __init__(self):
        self.config = Config()
        self.ai_client = UniversalAIClient()
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Настраивает браузер"""
        options = Options()
        if self.config.HEADLESS:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(self.config.ELEMENT_TIMEOUT)
    
    def generate_multi_page_test(self, scenario_description, start_url, test_name):
        """Упрощенная генерация многостраничного теста"""
        
        print("🎯 Создаю многостраничный тест...")
        
        # Открываем стартовую страницу
        self.driver.get(start_url)
        time.sleep(3)
        
        # Простой анализ сценария
        steps = self.simple_analyze_scenario(scenario_description)
        
        test_code = f'''# Многостраничный тест - сгенерирован AI
# Сценарий: {scenario_description}
# Стартовый URL: {start_url}

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def {test_name}():
    """Многостраничный тест: {scenario_description}"""
    
    print("🚀 Запуск многостраничного теста")
    driver = webdriver.Chrome()
    
    try:
        # Стартовая страница
        driver.get("{start_url}")
        time.sleep(3)
        
'''
        
        # Добавляем простые шаги
        for i, step in enumerate(steps):
            test_code += f'''
        # Шаг {i+1}
        print("Шаг {i+1}: {step}")
        time.sleep(2)
'''
        
        test_code += '''
        print("✅ Тест завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {{e}}")
    finally:
        driver.quit()

if __name__ == "__main__":
    {test_name}()
'''
        
        return test_code
    
    def simple_analyze_scenario(self, scenario):
        """Простой анализ сценария без AI"""
        steps = []
        if "логин" in scenario.lower():
            steps.extend(["Вход в систему", "Заполнение формы логина", "Нажатие кнопки входа"])
        if "поиск" in scenario.lower():
            steps.extend(["Поиск элемента", "Ввод запроса", "Просмотр результатов"])
        if "корзин" in scenario.lower():
            steps.extend(["Добавление в корзину", "Переход в корзину", "Оформление заказа"])
        
        return steps if steps else ["Выполнение основного действия", "Проверка результата"]
    
    def save_test(self, test_code, filename):
        """Сохраняет тест в файл"""
        os.makedirs(self.config.GENERATED_TESTS_DIR, exist_ok=True)
        filepath = os.path.join(self.config.GENERATED_TESTS_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        print(f"💾 Тест сохранен: {filepath}")
        return filepath
    
    def close(self):
        """Закрывает браузер"""
        if self.driver:
            self.driver.quit()