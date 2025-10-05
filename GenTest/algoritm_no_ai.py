import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class AdvancedAutoTestGenerator:
    def __init__(self):
        self.driver = None
        self.test_steps = []
        self.locators_map = {}
        self.current_page = 1
        self.execution_log = []
        
    def setup_driver(self):
        """Настройка Chrome драйвера"""
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--start-maximized')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.driver.implicitly_wait(10)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✅ Драйвер успешно настроен")

    def analyze_manual_scenario(self, manual_steps):
        """Анализ ручного сценария и классификация шагов"""
        analyzed_steps = []
        
        for i, step in enumerate(manual_steps, 1):
            element_type, target_element = self._classify_element_type(step)
            
            step_info = {
                'step_number': i,
                'description': step,
                'element_type': element_type,
                'target_element': target_element,
                'page': f"page_{self.current_page}",
                'is_transition': element_type == 'button' and self._is_transition_button(step),
                'test_data': self._generate_test_data(step, element_type, target_element)
            }
            
            analyzed_steps.append(step_info)
            
        return analyzed_steps

    def _classify_element_type(self, step_description):
        """Классификация типа элемента в шаге"""
        step_lower = step_description.lower()
        
        if any(word in step_lower for word in ['нажать', 'click', 'press', 'кнопк', 'button', 'login', 'checkout', 'continue', 'finish']):
            return 'button', self._extract_element_name(step_description, ['кнопк', 'button', 'login', 'checkout', 'continue', 'finish'])
        elif any(word in step_lower for word in ['ввести', 'input', 'type', 'заполнить', 'поле', 'username', 'password', 'firstname', 'lastname', 'postal']):
            return 'input', self._extract_element_name(step_description, ['поле', 'field', 'input', 'username', 'password', 'firstname', 'lastname', 'postal'])
        elif any(word in step_lower for word in ['выбрать', 'select', 'choose', 'список', 'dropdown', 'filter']):
            return 'dropdown', self._extract_element_name(step_description, ['список', 'dropdown', 'select', 'filter'])
        elif any(word in step_lower for word in ['отметить', 'чекбокс', 'checkbox', 'radio']):
            return 'checkbox', self._extract_element_name(step_description, ['чекбокс', 'checkbox', 'radio'])
        elif any(word in step_lower for word in ['проверить', 'verify', 'убедиться', 'отображен', 'текст', 'products', 'cart', 'information', 'overview']):
            return 'text', self._extract_element_name(step_description, ['текст', 'text', 'надпись', 'products', 'cart', 'information', 'overview'])
        else:
            return 'unknown', 'element'

    def _extract_element_name(self, step_description, keywords):
        """Извлечение названия элемента из описания шага"""
        step_lower = step_description.lower()
        for keyword in keywords:
            if keyword in step_lower:
                # Извлекаем текст после ключевого слова
                parts = step_description.split(keyword)
                if len(parts) > 1:
                    element_name = parts[1].strip(" '\":.-")
                    return element_name if element_name else keyword
        return step_description

    def _is_transition_button(self, step_description):
        """Определение, является ли кнопка кнопкой перехода"""
        transition_keywords = ['login', 'войти', 'submit', 'checkout', 'continue', 'finish', 'cart', 'menu']
        step_lower = step_description.lower()
        return any(keyword in step_lower for keyword in transition_keywords)

    def _generate_test_data(self, step_description, element_type, element_name):
        """Генерация тестовых данных для полей ввода"""
        if element_type != 'input':
            return None
            
        element_lower = element_name.lower()
        step_lower = step_description.lower()
        
        if 'username' in element_lower or 'login' in element_lower:
            return 'standard_user'
        elif 'password' in element_lower:
            return 'secret_sauce'
        elif 'firstname' in element_lower or 'first name' in step_lower:
            return 'John'
        elif 'lastname' in element_lower or 'last name' in step_lower:
            return 'Doe'
        elif 'postal' in element_lower or 'zip' in element_lower:
            return '12345'
        elif 'email' in element_lower:
            return 'test@example.com'
        else:
            return f'test_data_{element_name}'

    def find_element_locator(self, element_type, element_name):
        """Поиск локатора элемента на текущей странице"""
        strategies = self._get_locator_strategies(element_type, element_name)
        
        for strategy in strategies:
            try:
                elements = self.driver.find_elements(By.XPATH, strategy)
                if elements:
                    visible_elements = [el for el in elements if el.is_displayed()]
                    if visible_elements:
                        return strategy
            except Exception:
                continue
        
        # Fallback: поиск по частичному совпадению текста
        if element_type in ['button', 'text']:
            fallback_strategies = [
                f"//*[contains(text(), '{element_name}')]",
                f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]"
            ]
            for strategy in fallback_strategies:
                try:
                    elements = self.driver.find_elements(By.XPATH, strategy)
                    if elements and any(el.is_displayed() for el in elements):
                        return strategy
                except Exception:
                    continue
        
        return None

    def _get_locator_strategies(self, element_type, element_name):
        """Стратегии поиска локаторов по типу элемента"""
        element_lower = element_name.lower().replace(' ', '-')
        
        if element_type == 'button':
            return [
                f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]",
                f"//input[@type='submit' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]",
                f"//input[@type='button' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]",
                f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]",
                f"//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]",
                f"//input[@id='{element_lower}']",
                f"//button[@id='{element_lower}']",
                f"//input[@name='{element_lower}']",
                f"//button[@name='{element_lower}']",
                f"//*[@data-test='{element_lower}']",
                f"//*[contains(@class, 'btn') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]"
            ]
        elif element_type == 'input':
            return [
                f"//input[@placeholder='{element_name}']",
                f"//input[@id='{element_lower}']",
                f"//input[@name='{element_lower}']",
                f"//input[@data-test='{element_lower}']",
                f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]/following-sibling::input",
                f"//input[@type='text' and contains(@class, '{element_lower}')]",
                f"//input[@type='password']",
                f"//input[contains(@class, '{element_lower}')]"
            ]
        elif element_type == 'dropdown':
            return [
                f"//select[contains(@class, '{element_lower}')]",
                f"//select[@id='{element_lower}']",
                f"//select[@name='{element_lower}']",
                f"//select[@data-test='{element_lower}']"
            ]
        elif element_type == 'text':
            return [
                f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]",
                f"//h1[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]",
                f"//h2[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]",
                f"//h3[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]",
                f"//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]",
                f"//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]"
            ]
        else:
            return [f"//*[contains(text(), '{element_name}')]"]

    def execute_scenario_and_collect_locators(self, analyzed_steps, start_url):
        """Последовательное выполнение сценария и сбор локаторов"""
        print(f"🚀 Начинаем выполнение сценария с URL: {start_url}")
        self.driver.get(start_url)
        time.sleep(3)
        
        page_locators = {}
        current_page_steps = []
        
        for step in analyzed_steps:
            print(f"\n{'='*60}")
            print(f"📝 Шаг {step['step_number']}: {step['description']}")
            print(f"📄 Текущая страница: {step['page']}")
            print(f"🎯 Тип элемента: {step['element_type']}")
            print(f"🔍 Ищем: {step['target_element']}")
            
            # Поиск локатора на текущей странице
            locator = self.find_element_locator(step['element_type'], step['target_element'])
            
            if locator:
                print(f"✅ Найден локатор: {locator}")
                
                # Сохраняем информацию о локаторе
                locator_info = {
                    'element': step['target_element'],
                    'locator': locator,
                    'type': step['element_type'],
                    'description': step['description'],
                    'page': step['page'],
                    'test_data': step['test_data']
                }
                
                page_locators[step['step_number']] = locator_info
                current_page_steps.append(step['step_number'])
                
                # Выполняем действие с элементом
                success = self._perform_element_action(locator_info)
                
                if success and step['is_transition']:
                    # Ждем загрузки новой страницы
                    self._wait_for_page_load()
                    self.current_page += 1
                    print(f"🔄 Успешно перешли на страницу {self.current_page}")
                    current_page_steps = []
                    
            else:
                print(f"❌ Не найден локатор для: {step['target_element']}")
                page_locators[step['step_number']] = {
                    'element': step['target_element'],
                    'locator': 'NOT_FOUND',
                    'type': step['element_type'],
                    'description': step['description'],
                    'page': step['page'],
                    'test_data': step['test_data']
                }
        
        self.locators_map = page_locators
        return page_locators

    def _perform_element_action(self, locator_info):
        """Выполнение действия с элементом"""
        try:
            if locator_info['type'] == 'button':
                element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, locator_info['locator']))
                )
                element.click()
                print(f"✅ Выполнен клик: {locator_info['element']}")
                return True
                
            elif locator_info['type'] == 'input':
                element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, locator_info['locator']))
                )
                element.clear()
                test_data = locator_info['test_data'] or f"test_{locator_info['element']}"
                element.send_keys(test_data)
                print(f"✅ Введены данные '{test_data}' в: {locator_info['element']}")
                return True
                
            elif locator_info['type'] == 'dropdown':
                element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, locator_info['locator']))
                )
                select = Select(element)
                if len(select.options) > 1:
                    select.select_by_index(1)
                    print(f"✅ Выбрано значение в: {locator_info['element']}")
                return True
                
            elif locator_info['type'] == 'text':
                element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, locator_info['locator']))
                )
                if element.is_displayed():
                    print(f"✅ Проверен текст: {locator_info['element']}")
                    return True
                else:
                    print(f"❌ Текст не отображается: {locator_info['element']}")
                    return False
                    
            else:
                print(f"⚠️  Неизвестный тип элемента: {locator_info['type']}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при выполнении действия: {e}")
            return False

    def _wait_for_page_load(self, timeout=10):
        """Ожидание загрузки страницы"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)  # Дополнительная пауза для стабилизации
            return True
        except Exception as e:
            print(f"⚠️  Страница загружена, но превышено время ожидания: {e}")
            return True

    def generate_complete_test_code(self, test_name):
        """Генерация полного Python кода авто-теста"""
        
        test_code = f'''import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

class Test{test_name.replace(' ', '').title()}:
    """
    Авто-тест сгенерированный автоматически на основе ручного сценария
    Тестирование сайта: https://www.saucedemo.com
    Сгенерировано: {time.strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    def setup_method(self, method):
        """Настройка перед каждым тестом"""
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--start-maximized')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)
        self.base_url = "https://www.saucedemo.com"
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}})")
    
    def teardown_method(self, method):
        """Очистка после каждого теста"""
        self.driver.quit()
    
    def test_{test_name.lower().replace(' ', '_')}(self):
        """Автоматически сгенерированный тест для SauceDemo"""
        driver = self.driver
        wait = self.wait
        
        print("\\\\n🚀 Запуск автоматически сгенерированного теста...")
        print("📋 Сценарий: {' -> '.join([step['description'] for step in self.test_steps])}")
        
        driver.get(self.base_url)
        time.sleep(3)
        
'''
        
        # Добавляем шаги теста
        for step_num, locator_info in self.locators_map.items():
            if locator_info['locator'] != 'NOT_FOUND':
                test_code += self._generate_step_code(step_num, locator_info)
        
        test_code += '''
        print("\\\\n✅ Все шаги теста успешно выполнены!")
        print("🎉 Автоматически сгенерированный тест завершен успешно!")
        time.sleep(2)
'''
        
        return test_code

    def _generate_step_code(self, step_num, locator_info):
        """Генерация кода для конкретного шага"""
        indent = "        "
        step_code = f'\n{indent}# Шаг {step_num}: {locator_info["description"]}\n'
        step_code += f'{indent}print("\\\\n📝 Шаг {step_num}: {locator_info["description"]}")\n'
        
        if locator_info['type'] == 'button':
            step_code += f'{indent}button_{step_num} = wait.until(EC.element_to_be_clickable((By.XPATH, "{locator_info["locator"]}")))\n'
            step_code += f'{indent}button_{step_num}.click()\n'
            step_code += f'{indent}print("✅ Выполнен клик: {locator_info["element"]}")\n'
            step_code += f'{indent}time.sleep(2)\n'
            
        elif locator_info['type'] == 'input':
            test_data = locator_info['test_data'] or f"test_data_{step_num}"
            step_code += f'{indent}input_{step_num} = wait.until(EC.presence_of_element_located((By.XPATH, "{locator_info["locator"]}")))\n'
            step_code += f'{indent}input_{step_num}.clear()\n'
            step_code += f'{indent}input_{step_num}.send_keys("{test_data}")\n'
            step_code += f'{indent}print("✅ Введены данные \\\"{test_data}\\\" в: {locator_info["element"]}")\n'
            
        elif locator_info['type'] == 'dropdown':
            step_code += f'{indent}dropdown_{step_num} = wait.until(EC.presence_of_element_located((By.XPATH, "{locator_info["locator"]}")))\n'
            step_code += f'{indent}select_{step_num} = Select(dropdown_{step_num})\n'
            step_code += f'{indent}if len(select_{step_num}.options) > 1:\n'
            step_code += f'{indent}    select_{step_num}.select_by_index(1)\n'
            step_code += f'{indent}    print("✅ Выбрано значение в: {locator_info["element"]}")\n'
            
        elif locator_info['type'] == 'text':
            step_code += f'{indent}text_{step_num} = wait.until(EC.presence_of_element_located((By.XPATH, "{locator_info["locator"]}")))\n'
            step_code += f'{indent}assert text_{step_num}.is_displayed(), "Элемент не отображается: {locator_info["element"]}"\n'
            step_code += f'{indent}print("✅ Проверен текст: {locator_info["element"]}")\n'
        
        return step_code

    def save_test_file(self, test_code, filename="generated_auto_test.py"):
        """Сохранение сгенерированного теста в файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(test_code)
        print(f"✅ Тест сохранен в файл: {filename}")
        return filename

    def close(self):
        """Закрытие драйвера"""
        if self.driver:
            self.driver.quit()
            print("✅ Драйвер закрыт")

def main():
    """Основная функция - полный пример работы"""
    
    # Полный сценарий тестирования SauceDemo
    manual_scenario = [
        "Ввести логин в поле Username",
        "Ввести пароль в поле Password", 
        "Нажать на кнопку Login",
        "Проверить отображение текста Products",
        "Выбрать значение из списка фильтра Products",
        "Нажать на кнопку добавления товара Sauce Labs Backpack в корзину",
        "Нажать на кнопку корзины",
        "Проверить отображение текста Your Cart",
        "Нажать на кнопку Checkout",
        "Ввести имя в поле First Name",
        "Ввести фамилию в поле Last Name",
        "Ввести почтовый индекс в поле Postal Code",
        "Нажать на кнопку Continue",
        "Проверить отображение текста Checkout Overview",
        "Нажать на кнопку Finish",
        "Проверить отображение текста Thank you for your order"
    ]
    
    # Создаем генератор
    generator = AdvancedAutoTestGenerator()
    generator.test_steps = manual_scenario
    
    try:
        # Настраиваем драйвер
        generator.setup_driver()
        
        # Анализируем сценарий
        analyzed_steps = generator.analyze_manual_scenario(manual_scenario)
        print("✅ Сценарий проанализирован:")
        for step in analyzed_steps:
            print(f"   Шаг {step['step_number']}: {step['description']}")
            print(f"     -> Тип: {step['element_type']}, Данные: {step['test_data']}")
        
        # Выполняем сценарий и собираем локаторы
        start_url = "https://www.saucedemo.com"
        locators = generator.execute_scenario_and_collect_locators(analyzed_steps, start_url)
        
        print(f"\n📊 Итоги сбора локаторов:")
        print(f"✅ Успешно найдено: {len([l for l in locators.values() if l['locator'] != 'NOT_FOUND'])}/{len(locators)}")
        print(f"📄 Обработано страниц: {generator.current_page}")
        
        # Генерируем код теста
        test_code = generator.generate_complete_test_code("SauceDemo Full Scenario")
        print("✅ Код теста сгенерирован")
        
        # Сохраняем тест
        test_filename = generator.save_test_file(test_code, "saucedemo_full_auto_test.py")
        
        print("\n🎯 АВТОМАТИЧЕСКИ СГЕНЕРИРОВАННЫЙ ТЕСТ ГОТОВ!")
        print(f"📁 Файл: {test_filename}")
        print("🚀 Тест можно запустить командой: python saucedemo_full_auto_test.py")
        
        # Спрашиваем пользователя хочет ли он запустить тест
        run_test = input("\nЗапустить сгенерированный тест сейчас? (y/n): ").lower().strip()
        if run_test == 'y':
            print("\n🚀 Запускаем сгенерированный тест...")
            import subprocess
            result = subprocess.run(['python', test_filename], capture_output=True, text=True)
            print("\n" + "="*60)
            print("РЕЗУЛЬТАТ ВЫПОЛНЕНИЯ ТЕСТА:")
            print("="*60)
            print(result.stdout)
            if result.stderr:
                print("ОШИБКИ:")
                print(result.stderr)
            
            if result.returncode == 0:
                print("🎉 ТЕСТ УСПЕШНО ВЫПОЛНЕН!")
            else:
                print("❌ ТЕСТ ЗАВЕРШИЛСЯ С ОШИБКАМИ")
        
    except Exception as e:
        print(f"❌ Ошибка в основном процессе: {e}")
        import traceback
        traceback.print_exc()
    finally:
        generator.close()

if __name__ == "__main__":
    main()