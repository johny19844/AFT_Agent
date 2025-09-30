import os
import json
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions

from config import Config
from ai_client import UniversalAIClient

class SimpleAITestGenerator:
    def __init__(self):
        self.config = Config()
        self.ai_client = UniversalAIClient()
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Настраивает браузер для Windows"""
        print("🔧 Настраиваю браузер для Windows...")
        
        try:
            if self.config.BROWSER == "chrome":
                self._setup_chrome_windows()
            else:
                self._setup_chrome_windows()  # По умолчанию Chrome для Windows
                
            print("✅ Браузер настроен успешно!")
            
        except Exception as e:
            print(f"❌ Ошибка настройки браузера: {e}")
            print("🔄 Пробую альтернативный метод...")
            self._setup_driver_fallback()
    
    def _setup_chrome_windows(self):
        """Настраивает Chrome для Windows"""
        options = ChromeOptions()
        
        if self.config.HEADLESS:
            options.add_argument("--headless")
        
        # Оптимизация для Windows
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-gpu-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Отключаем логи и уведомления
        options.add_argument("--log-level=3")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        
        # Автоматическая установка драйвера через webdriver-manager
        service = ChromeService(
            ChromeDriverManager().install(),
            service_args=['--disable-build-check', '--silent']
        )
        
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Скрываем автоматизацию
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.driver.implicitly_wait(self.config.ELEMENT_TIMEOUT)
    
    def _setup_driver_fallback(self):
        """Резервный метод настройки браузера для Windows"""
        try:
            options = ChromeOptions()
            if self.config.HEADLESS:
                options.add_argument("--headless")
            
            # Пробуем без webdriver-manager
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(self.config.ELEMENT_TIMEOUT)
            print("✅ Браузер настроен в резервном режиме")
        except Exception as e:
            print(f"❌ Критическая ошибка: Не удалось настроить браузер: {e}")
            print("💡 Убедитесь что Chrome установлен и обновлен")
            raise
    
    def check_chrome_installation(self):
        """Проверяет установлен ли Chrome на Windows"""
        try:
            # Проверяем через реестр Windows
            if self.config.IS_WINDOWS:
                import winreg
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                       r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
                    winreg.CloseKey(key)
                    return True
                except:
                    # Проверяем в Program Files
                    chrome_paths = [
                        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                    ]
                    return any(os.path.exists(path) for path in chrome_paths)
            return True
        except:
            return True  # Предполагаем что установлен
    
    def analyze_page_simple(self):
        """Анализирует страницу"""
        print("🔍 Анализирую страницу...")
        
        elements_data = []
        element_types = [
            ("input", "Поля ввода"), 
            ("button", "Кнопки"), 
            ("a", "Ссылки"),
            ("form", "Формы")
        ]
        
        for tag, description in element_types:
            try:
                elements = self.driver.find_elements(By.TAG_NAME, tag)
                print(f"   Найдено {len(elements)} элементов {tag}")
                
                for element in elements[:10]:  # Ограничиваем количество
                    try:
                        if element.is_displayed():
                            element_info = self.get_element_info(element, tag)
                            if element_info:
                                elements_data.append(element_info)
                    except:
                        continue
                        
            except Exception as e:
                print(f"   Ошибка при поиске {tag}: {e}")
        
        print(f"✅ Собрано информации о {len(elements_data)} элементах")
        return elements_data
    
    def get_element_info(self, element, tag):
        """Получает информацию об элементе"""
        try:
            info = {
                'tag': tag,
                'text': element.text.strip() if element.text else "",
                'attributes': {}
            }
            
            attributes = ['id', 'name', 'type', 'placeholder', 'class', 'value', 'href', 'action', 'for']
            for attr in attributes:
                try:
                    value = element.get_attribute(attr)
                    if value and value.strip():
                        info['attributes'][attr] = value.strip()
                except:
                    continue
            
            # Пропускаем элементы без полезной информации
            if not info['text'] and not info['attributes']:
                return None
                
            return info
            
        except:
            return None
    
    def ask_ai_for_locators(self, element_description, page_elements):
        """Спрашивает AI где найти элемент с правильными типами локаторов"""
        
        limited_elements = page_elements[:15]
        
        prompt = f"""
        Найди лучшие локаторы для элемента: "{element_description}"
        
        Элементы на странице:
        {json.dumps(limited_elements, ensure_ascii=False, indent=2)}
        
        ВАЖНО: Используй ТОЛЬКО следующие типы локаторов:
        - "ID" для атрибута id
        - "CSS" для CSS селекторов  
        - "XPATH" для XPath выражений
        - "NAME" для атрибута name
        
        Формат ответа:
        {{
            "element": "описание",
            "locators": [
                {{
                    "type": "ID",  # ТОЛЬКО: ID, CSS, XPATH, NAME
                    "value": "правильное_значение", 
                    "explanation": "объяснение"
                }}
            ]
        }}
        
        Примеры правильных локаторов:
        - Для id="username": {{"type": "ID", "value": "username"}}
        - Для class="btn": {{"type": "CSS", "value": ".btn"}} 
        - Для XPath: {{"type": "XPATH", "value": "//button[text()='Login']"}}
        """
        
        try:
            print(f"   🤖 Запрашиваю AI...")
            response = self.ai_client.generate_response(
                prompt=prompt,
                system_message="Ты помогаешь с автотестами. Используй только правильные типы локаторов: ID, CSS, XPATH, NAME. Возвращай валидный JSON.",
                max_tokens=800
            )
            
            # Очищаем ответ
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()
            
            result = json.loads(response)
            
            # Проверяем и исправляем локаторы
            valid_locators = []
            for locator in result.get('locators', []):
                locator_type = locator.get('type', '').upper()
                if locator_type in ['ID', 'CSS', 'XPATH', 'NAME']:
                    valid_locators.append(locator)
                else:
                    print(f"   ⚠️  Исправляю некорректный тип локатора: {locator_type}")
                    # Автоматически исправляем
                    if 'id' in locator.get('value', '').lower():
                        locator['type'] = 'ID'
                        valid_locators.append(locator)
                    else:
                        locator['type'] = 'CSS'
                        valid_locators.append(locator)
            
            result['locators'] = valid_locators
            print(f"   ✅ AI нашел {len(valid_locators)} валидных локаторов")
            return result
            
        except json.JSONDecodeError as e:
            print(f"   ❌ Ошибка парсинга JSON: {e}")
            return {"error": "Invalid JSON", "raw_response": response}
        except Exception as e:
            print(f"   ❌ Ошибка AI: {e}")
            return {"error": str(e)}

    def generate_simple_test(self, test_scenario, start_url):
        """Генерирует простой тест"""
        
        print(f"🚀 Начинаю генерацию теста")
        print(f"   Сценарий: {test_scenario}")
        print(f"   URL: {start_url}")
        
        try:
            # Открываем страницу
            print("🌐 Открываю страницу...")
            self.driver.get(start_url)
            
            # Ждем загрузки
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)
            
            # Анализируем страницу
            page_elements = self.analyze_page_simple()
            
            # Определяем какие элементы нужны для теста
            test_elements = self.identify_test_elements(test_scenario)
            print(f"🎯 Буду искать: {', '.join(test_elements)}")
            
            # Ищем локаторы для каждого элемента
            locators_map = {}
            for element_desc in test_elements:
                print(f"🔎 Ищу локатор для: '{element_desc}'")
                ai_result = self.ask_ai_for_locators(element_desc, page_elements)
                
                if "error" not in ai_result:
                    locators_map[element_desc] = ai_result
                else:
                    print(f"   ❌ Не удалось найти локатор: {ai_result.get('error')}")
            
            # Генерируем код теста
            test_code = self.create_test_code(test_scenario, start_url, locators_map)
            return test_code
            
        except Exception as e:
            print(f"❌ Ошибка при анализе: {e}")
            return self.create_fallback_test(test_scenario, start_url)
    
    def create_fallback_test(self, test_scenario, start_url):
        """Создает базовый тест при ошибке"""
        return f'''# Базовый тест для Windows
# Сценарий: {test_scenario}
# URL: {start_url}

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_windows_fallback():
    """Базовый тест для Windows (требует доработки)"""
    
    print("🚀 Запуск теста для Windows...")
    
    # Настройка Chrome для Windows
    driver = webdriver.Chrome()
    
    try:
        # Открываем страницу
        driver.get("{start_url}")
        time.sleep(5)
        
        print("⚠️  Этот тест требует ручной доработки локаторов")
        print("💡 Откройте DevTools (F12) чтобы найти селекторы элементов")
        
        # Базовая проверка
        assert "404" not in driver.title, "Страница не найдена"
        print("✅ Страница загружена")
        
    except Exception as e:
        print(f"❌ Ошибка: {{e}}")
    finally:
        driver.quit()
        print("🔚 Тест завершен")

if __name__ == "__main__":
    test_windows_fallback()
'''
    
    def identify_test_elements(self, test_scenario):
        """Определяет какие элементы нужны для теста"""
        scenario_lower = test_scenario.lower()
        elements = []
        
        if any(word in scenario_lower for word in ['логин', 'login', 'вход']):
            elements.extend(["поле для логина", "поле для пароля", "кнопка входа"])
        
        if any(word in scenario_lower for word in ['поиск', 'search']):
            elements.extend(["поле поиска", "кнопка поиска"])
        
        return elements if elements else ["основная кнопка", "поле ввода"]
    
    def create_test_code(self, test_scenario, start_url, locators_map):
        """Создает код Python теста с правильным форматированием"""
        
        # Основной шаблон теста БЕЗ лишних отступов
        test_code = f'''# Авто-тест для Windows - сгенерирован AI
    # Сценарий: {test_scenario}
    # URL: {start_url}

    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time

    def test_auto_generated():
        """Авто-тест для Windows"""
        
        print("🚀 Запуск теста для Windows...")
        
        # Настройка Chrome для Windows
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        
        try:
            # Открываем страницу
            print("🌐 Открываю страницу...")
            driver.get("{start_url}")
            
            # Ждем загрузки
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)
    '''

        # Добавляем действия с правильными отступами
        actions_added = False
        for element_desc, locator_data in locators_map.items():
            if locator_data.get('locators'):
                best_locator = locator_data['locators'][0]
                
                # Исправляем тип локатора
                fixed_type = self._fix_locator_type(best_locator['type'])
                fixed_value = self._validate_locator_value(best_locator['type'], best_locator['value'])
                
                actions_added = True
                
                if "поле" in element_desc and "логин" in element_desc:
                    test_code += f'''
            # Ввод логина: {element_desc}
            print("📝 Ввожу логин...")
            try:
                login_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(({fixed_type}, "{fixed_value}"))
                )
                login_field.clear()
                login_field.send_keys("test_user")
                print("✅ Логин введен успешно")
                time.sleep(1)
            except Exception as e:
                print(f"❌ Не удалось ввести логин: {{e}}")
                raise
    '''
                elif "поле" in element_desc and "парол" in element_desc:
                    test_code += f'''
            # Ввод пароля: {element_desc}
            print("🔒 Ввожу пароль...")
            try:
                password_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(({fixed_type}, "{fixed_value}"))
                )
                password_field.clear()
                password_field.send_keys("password123")
                print("✅ Пароль введен успешно")
                time.sleep(1)
            except Exception as e:
                print(f"❌ Не удалось ввести пароль: {{e}}")
                raise
    '''
                elif "кнопка" in element_desc:
                    test_code += f'''
            # Нажатие кнопки: {element_desc}
            print("🖱️ Нажимаю кнопку...")
            try:
                button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(({fixed_type}, "{fixed_value}"))
                )
                button.click()
                print("✅ Кнопка нажата успешно")
                time.sleep(2)
            except Exception as e:
                print(f"❌ Не удалось нажать кнопку: {{e}}")
                raise
    '''

        # Если не добавили действий, добавляем базовую проверку
        if not actions_added:
            test_code += '''
            # Базовая проверка загрузки страницы
            print("🔍 Проверяю загрузку страницы...")
            assert "404" not in driver.title, "Страница не найдена"
            print("✅ Страница загружена корректно")
            time.sleep(2)
    '''

        # Завершающая часть теста
        test_code += '''
            print("🎉 Тест успешно выполнен!")
            
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            # Сохраняем скриншот при ошибке
            try:
                driver.save_screenshot("error_screenshot.png")
                print("📸 Скриншот ошибки сохранен: error_screenshot.png")
            except:
                print("⚠️ Не удалось сохранить скриншот")
            raise
            
        finally:
            try:
                driver.quit()
                print("🔚 Браузер закрыт")
            except:
                print("⚠️ Не удалось корректно закрыть браузер")

    if __name__ == "__main__":
        test_auto_generated()
    '''

        # Убираем возможные лишние пробелы в начале строк
        test_code = self._clean_code_indentation(test_code)
        return test_code

    def _clean_code_indentation(self, code):
        """Очищает код от лишних отступов в начале строк"""
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Убираем пробелы в начале пустых строк
            if line.strip() == '':
                cleaned_lines.append('')
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def validate_generated_code(self, test_code):
        """Проверяет и исправляет форматирование сгенерированного кода"""
        try:
            # Пробуем скомпилировать код чтобы проверить синтаксис
            compile(test_code, '<string>', 'exec')
            print("✅ Сгенерированный код прошел проверку синтаксиса")
            return test_code
        except SyntaxError as e:
            print(f"⚠️ Обнаружена синтаксическая ошибка: {e}")
            print("🔄 Исправляю форматирование...")
            return self._fix_code_formatting(test_code)

    def _fix_code_formatting(self, code):
        """Исправляет форматирование кода"""
        lines = code.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Убираем лишние пробелы в начале строк
            stripped_line = line.lstrip()
            
            # Восстанавливаем правильные отступы для блоков кода
            if stripped_line.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except', 'finally:', 'else:')):
                fixed_lines.append(stripped_line)
            elif stripped_line and not stripped_line.startswith('#'):
                # Добавляем стандартный отступ в 4 пробела
                fixed_lines.append('    ' + stripped_line)
            else:
                fixed_lines.append(stripped_line)
        
        fixed_code = '\n'.join(fixed_lines)
        
        # Проверяем исправленный код
        try:
            compile(fixed_code, '<string>', 'exec')
            print("✅ Форматирование исправлено успешно")
            return fixed_code
        except SyntaxError:
            print("❌ Не удалось автоматически исправить код")
            return code

    def save_test(self, test_code, filename):
        """Сохраняет тест в файл с проверкой форматирования"""
        os.makedirs(self.config.GENERATED_TESTS_DIR, exist_ok=True)
        filepath = os.path.join(self.config.GENERATED_TESTS_DIR, filename)
        
        # Проверяем и исправляем форматирование
        validated_code = self.validate_generated_code(test_code)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(validated_code)
        
        print(f"💾 Тест сохранен: {filepath}")
        
        # Показываем информацию о файле
        line_count = len(validated_code.split('\n'))
        print(f"📊 Размер: {len(validated_code)} символов, {line_count} строк")
        
        return filepath

    def close(self):
        """Закрывает браузер"""
        if self.driver:
            try:
                self.driver.quit()
                print("🔚 Браузер закрыт")
            except:
                pass

    def _fix_locator_type(self, locator_type):
        """Исправляет тип локатора для Selenium"""
        type_mapping = {
            'ID': 'By.ID',
            'CSS': 'By.CSS_SELECTOR', 
            'XPATH': 'By.XPATH',
            'NAME': 'By.NAME',
            'CLASS_NAME': 'By.CLASS_NAME',
            'TAG_NAME': 'By.TAG_NAME',
            'LINK_TEXT': 'By.LINK_TEXT',
            'PARTIAL_LINK_TEXT': 'By.PARTIAL_LINK_TEXT'
        }
        return type_mapping.get(locator_type.upper(), 'By.CSS_SELECTOR')

    def _validate_locator_value(self, locator_type, value):
        """Валидирует и исправляет значение локатора"""
        if locator_type.upper() == 'ID' and value.startswith('#'):
            return value[1:]  # Убираем # для ID
        elif locator_type.upper() == 'CSS' and not value.startswith(('.', '#', '[')):
            # Добавляем точку если это класс без точки
            if value.startswith('class='):
                return f".{value[6:]}"
        return value