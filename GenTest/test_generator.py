import os
import json
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

from config import Config
from ai_client import UniversalAIClient

class SimpleAITestGenerator:
    def __init__(self):
        self.config = Config()
        self.ai_client = UniversalAIClient()
        self.driver = None
        self.setup_driver()
    
    def check_browser_installation(self):
        """Проверяет установлен ли браузер"""
        try:
            if self.config.BROWSER == "chrome":
                result = subprocess.run(['which', 'google-chrome'], capture_output=True, text=True)
                if result.returncode == 0:
                    return True
                # Проверяем chromium
                result = subprocess.run(['which', 'chromium-browser'], capture_output=True, text=True)
                return result.returncode == 0
            elif self.config.BROWSER == "firefox":
                result = subprocess.run(['which', 'firefox'], capture_output=True, text=True)
                return result.returncode == 0
        except:
            return False
    
    def setup_driver(self):
        """Настраивает браузер с улучшенной обработкой ошибок"""
        print("🔧 Настраиваю браузер...")
        
        # Проверяем установлен ли браузер
        if not self.check_browser_installation():
            print("❌ Браузер не найден. Устанавливаю зависимости...")
            self.install_browser_dependencies()
        
        try:
            if self.config.BROWSER == "chrome":
                self._setup_chrome()
            elif self.config.BROWSER == "chromium":
                self._setup_chromium()
            elif self.config.BROWSER == "firefox":
                self._setup_firefox()
            else:
                print("❌ Неизвестный браузер. Использую Chrome.")
                self._setup_chrome()
                
            print("✅ Браузер настроен успешно!")
            
        except Exception as e:
            print(f"❌ Ошибка настройки браузера: {e}")
            print("🔄 Пробую использовать Firefox...")
            self._setup_firefox_fallback()
    
    def _setup_chrome(self):
        """Настраивает Chrome"""
        options = ChromeOptions()
        if self.config.HEADLESS:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--remote-debugging-port=9222")
        
        # Автоматическая установка драйвера
        service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(self.config.ELEMENT_TIMEOUT)
    
    def _setup_chromium(self):
        """Настраивает Chromium (лучше для Linux)"""
        options = ChromeOptions()
        if self.config.HEADLESS:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Пробуем разные пути к chromium
        chromium_paths = [
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/snap/bin/chromium'
        ]
        
        for path in chromium_paths:
            if os.path.exists(path):
                options.binary_location = path
                break
        
        service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(self.config.ELEMENT_TIMEOUT)
    
    def _setup_firefox(self):
        """Настраивает Firefox (самый стабильный вариант)"""
        options = FirefoxOptions()
        if self.config.HEADLESS:
            options.add_argument("--headless")
        
        service = FirefoxService(GeckoDriverManager().install())
        self.driver = webdriver.Firefox(service=service, options=options)
        self.driver.implicitly_wait(self.config.ELEMENT_TIMEOUT)
    
    def _setup_firefox_fallback(self):
        """Резервная настройка Firefox"""
        try:
            options = FirefoxOptions()
            if self.config.HEADLESS:
                options.add_argument("--headless")
            
            # Используем системный firefox без менеджера драйверов
            self.driver = webdriver.Firefox(options=options)
            self.driver.implicitly_wait(self.config.ELEMENT_TIMEOUT)
            print("✅ Firefox настроен в резервном режиме")
        except Exception as e:
            print(f"❌ Критическая ошибка: Не удалось настроить браузер: {e}")
            raise
    
    def install_browser_dependencies(self):
        """Устанавливает необходимые зависимости для браузера"""
        if self.config.IS_LINUX:
            print("📦 Устанавливаю зависимости для Linux...")
            try:
                # Для Ubuntu/Debian
                if os.path.exists('/etc/debian_version'):
                    os.system('sudo apt update')
                    os.system('sudo apt install -y chromium-browser firefox wget')
                # Для CentOS/RHEL/Fedora
                elif os.path.exists('/etc/redhat-release'):
                    os.system('sudo dnf install -y chromium firefox wget')
                else:
                    print("⚠️  Автоматическая установка не поддерживается для вашего дистрибутива")
                    print("📚 Установите браузер вручную:")
                    print("   Ubuntu/Debian: sudo apt install chromium-browser firefox")
                    print("   CentOS/Fedora: sudo dnf install chromium firefox")
            except Exception as e:
                print(f"⚠️  Ошибка установки зависимостей: {e}")
    
    def analyze_page_simple(self):
        """Анализирует страницу"""
        print("🔍 Анализирую страницу...")
        
        elements_data = []
        element_types = [("input", "Поля ввода"), ("button", "Кнопки"), ("a", "Ссылки")]
        
        for tag, description in element_types:
            try:
                elements = self.driver.find_elements(By.TAG_NAME, tag)
                for element in elements[:5]:
                    if element.is_displayed():
                        element_info = self.get_element_info(element, tag)
                        if element_info:
                            elements_data.append(element_info)
            except Exception as e:
                print(f"Ошибка при поиске {tag}: {e}")
        
        return elements_data
    
    def get_element_info(self, element, tag):
        """Получает информацию об элементе"""
        try:
            info = {
                'tag': tag,
                'text': element.text.strip() if element.text else "",
                'attributes': {}
            }
            
            attributes = ['id', 'name', 'type', 'placeholder', 'class', 'value']
            for attr in attributes:
                value = element.get_attribute(attr)
                if value:
                    info['attributes'][attr] = value
            
            return info if info['text'] or info['attributes'] else None
        except:
            return None
    
    def ask_ai_for_locators(self, element_description, page_elements):
        """Спрашивает AI где найти элемент на странице"""
        
        prompt = f"""
        Я новичок в автоматизации тестирования. Помоги найти локаторы для элемента.
        
        Я ищу: "{element_description}"
        
        На странице есть следующие элементы:
        {json.dumps(page_elements, ensure_ascii=False, indent=2)}
        
        Дай мне 3 лучших варианта локаторов в порядке убывания надежности.
        Формат ответа - простой JSON:
        
        {{
            "element": "что я ищу",
            "locators": [
                {{
                    "type": "ID или CSS или XPATH",
                    "value": "значение локатора", 
                    "explanation": "простое объяснение почему этот локатор хорош"
                }}
            ]
        }}
        """
        
        try:
            response = self.ai_client.generate_response(
                prompt=prompt,
                system_message="Ты помогаешь новичкам создавать автотесты. Объясняй просто и понятно. Всегда возвращай валидный JSON.",
                max_tokens=1000
            )
            
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON от AI: {e}")
            print(f"Ответ AI: {response}")
            return {"error": f"Invalid JSON from AI: {e}"}
        except Exception as e:
            print(f"❌ Ошибка при обращении к AI: {e}")
            return {"error": str(e)}
    
    def generate_simple_test(self, test_scenario, start_url):
        """Генерирует простой тест"""
        
        print(f"🚀 Начинаю генерацию теста для: {test_scenario}")
        print(f"🌐 Открываю страницу: {start_url}")
        
        try:
            # Открываем страницу
            self.driver.get(start_url)
            time.sleep(3)
            
            # Анализируем страницу
            page_elements = self.analyze_page_simple()
            print(f"📄 Найдено элементов: {len(page_elements)}")
            
            # Просим AI найти локаторы
            test_elements = self.identify_test_elements(test_scenario)
            
            locators_map = {}
            for element_desc in test_elements:
                print(f"🔎 Ищу локатор для: {element_desc}")
                ai_result = self.ask_ai_for_locators(element_desc, page_elements)
                
                if "error" not in ai_result:
                    locators_map[element_desc] = ai_result
                    print(f"✅ Найдено локаторов: {len(ai_result.get('locators', []))}")
                else:
                    print(f"❌ Не удалось найти локатор для: {element_desc}")
            
            # Генерируем код теста
            test_code = self.create_test_code(test_scenario, start_url, locators_map)
            return test_code
            
        except Exception as e:
            print(f"❌ Ошибка при анализе страницы: {e}")
            # Возвращаем базовый тест даже при ошибке
            return self.create_fallback_test(test_scenario, start_url)
    
    def create_fallback_test(self, test_scenario, start_url):
        """Создает базовый тест при ошибке анализа"""
        return f'''# Базовый тест - создан при ошибке анализа
# Сценарий: {test_scenario}
# URL: {start_url}

from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def test_fallback():
    """Базовый тест (требует ручной доработки)"""
    
    driver = webdriver.Chrome()
    
    try:
        driver.get("{start_url}")
        time.sleep(5)
        
        # TODO: Добавьте локаторы вручную
        print("⚠️ Этот тест требует ручной доработки локаторов")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_fallback()
'''
    
    def identify_test_elements(self, test_scenario):
        """Определяет какие элементы нужны для теста"""
        elements = []
        
        if "логин" in test_scenario.lower() or "login" in test_scenario.lower():
            elements.extend(["поле для логина", "поле для пароля", "кнопка входа"])
        
        if "поиск" in test_scenario.lower() or "search" in test_scenario.lower():
            elements.extend(["поле поиска", "кнопка поиска"])
        
        return elements if elements else ["основная кнопка", "поле ввода"]
    
    def create_test_code(self, test_scenario, start_url, locators_map):
        """Создает код Python теста"""
        
        test_code = f'''# Авто-тест сгенерирован AI
# Сценарий: {test_scenario}
# URL: {start_url}

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_auto_generated():
    """Автоматически сгенерированный тест"""
    
    print("🚀 Запуск авто-теста...")
    
    # Настройка браузера
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    try:
        # Открываем страницу
        print("🌐 Открываю страницу...")
        driver.get("{start_url}")
        time.sleep(3)
        
'''
        
        # Добавляем действия для каждого элемента
        for element_desc, locator_data in locators_map.items():
            if locator_data.get('locators'):
                best_locator = locator_data['locators'][0]
                
                if "поле" in element_desc and "логин" in element_desc:
                    test_code += f'''
        # Ввод логина
        print("📝 Ввожу логин...")
        {best_locator['type'].lower()}_element = driver.find_element({best_locator['type'].upper()}, "{best_locator['value']}")
        {best_locator['type'].lower()}_element.clear()
        {best_locator['type'].lower()}_element.send_keys("test_user")
        time.sleep(1)
'''
                elif "поле" in element_desc and "парол" in element_desc:
                    test_code += f'''
        # Ввод пароля
        print("🔒 Ввожу пароль...")
        {best_locator['type'].lower()}_element = driver.find_element({best_locator['type'].upper()}, "{best_locator['value']}")
        {best_locator['type'].lower()}_element.clear()
        {best_locator['type'].lower()}_element.send_keys("password123")
        time.sleep(1)
'''
                elif "кнопка" in element_desc:
                    test_code += f'''
        # Нажатие кнопки
        print("🖱️ Нажимаю кнопку...")
        {best_locator['type'].lower()}_element = driver.find_element({best_locator['type'].upper()}, "{best_locator['value']}")
        {best_locator['type'].lower()}_element.click()
        time.sleep(2)
'''
        
        test_code += '''
        print("✅ Тест успешно выполнен!")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {{e}}")
        raise
    finally:
        driver.quit()
        print("🔚 Браузер закрыт")

if __name__ == "__main__":
    test_auto_generated()
'''
        
        return test_code
    
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
            print("🔚 Браузер закрыт")