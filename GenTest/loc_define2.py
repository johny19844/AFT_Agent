import os
import json
import re
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from llama_cpp import Llama

class LocalAILocatorFinder:
    def __init__(self, gguf_model_path):
        self.gguf_model_path = gguf_model_path
        self.llm = Llama(model_path=gguf_model_path, n_ctx=4096)
        self.driver = None
        self.all_page_elements = {}
        self.current_page = 0
        self.action_history = []
        
        # Настройка логирования
        self.setup_logging()

    def setup_logging(self):
        """Настройка логирования переходов между страницами"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'page_transitions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        """Настройка веб-драйвера"""
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        service = ChromeService()
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)

    def wait_for_element(self, by, value, timeout=10):
        """Ожидание появления элемента на странице"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.warning(f"Элемент {by}={value} не найден за {timeout} секунд")
            return None

    def wait_for_page_load(self, timeout=10):
        """Ожидание полной загрузки страницы"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            self.logger.info("Страница полностью загружена")
        except TimeoutException:
            self.logger.warning(f"Страница не загрузилась полностью за {timeout} секунд")

    def log_page_transition(self, from_page, to_page, action=None):
        """Логирование перехода между страницами"""
        transition_info = {
            "timestamp": datetime.now().isoformat(),
            "from_page": from_page,
            "to_page": to_page,
            "action": action,
            "url": self.driver.current_url
        }
        self.action_history.append(transition_info)
        self.logger.info(f"Переход: {from_page} -> {to_page} | Действие: {action} | URL: {self.driver.current_url}")

    def analyze_scenario(self, test_scenario):
        """
        Анализирует текст сценария, извлекает начальный URL и последовательность действий.
        """
        prompt = (
            "Ты — помощник по автоматизации тестирования. "
            "На вход тебе дается тестовый сценарий. "
            "Определи начальный url страницы и последовательность действий для выполнения сценария. "
            "Верни ТОЛЬКО JSON без дополнительного текста в формате: "
            '{'
            '"initial_url": "string", '
            '"actions": ['
            '  {"action": "navigate|type|click|wait", "target": "string", "value": "string (optional)", "description": "string"}'
            '], '
            '"required_elements": ['
            '  {"name": "string", "description": "string", "page": "login|main|cart|checkout"}'
            ']'
            '}.\n\n'
            f"Тестовый сценарий:\n{test_scenario}\n"
            "Ответ только в формате JSON:"
        )
        print("=== PROMPT TO MODEL (analyze_scenario) ===")
        print(prompt)
        print("=== END PROMPT ===")
        
        output = self.llm(prompt, max_tokens=1024, stop=["\n\n"])
        print("=== MODEL OUTPUT (analyze_scenario) ===")
        rez = self._clean_generated_code(output['choices'][0]['text'])
        print(rez)
        print("=== END MODEL OUTPUT ===")
        
        match = re.search(r'\{.*\}', rez, re.DOTALL)
        if match:
            try:
                scenario_info = json.loads(match.group(0))
                return scenario_info
            except Exception as e:
                self.logger.error(f"Ошибка парсинга JSON: {e}")
        
        raise ValueError("Не удалось получить корректный JSON из ответа Llama")

    def collect_page_elements(self, page_name):
        """
        Собирает информацию о всех видимых элементах на текущей странице.
        """
        self.wait_for_page_load()
        
        if page_name not in self.all_page_elements:
            self.all_page_elements[page_name] = []
            
        elements_info = []
        tags = ['input', 'button', 'a', 'select', 'textarea', 'div', 'span', 'li', 'img']
        
        for tag in tags:
            try:
                found = self.driver.find_elements(By.TAG_NAME, tag)
                for el in found:
                    if not el.is_displayed():
                        continue
                    
                    # Получаем дополнительные атрибуты для лучшей идентификации
                    attributes = {
                        "tag": tag,
                        "text": el.text.strip()[:100],  # Ограничиваем длину текста
                        "id": el.get_attribute("id"),
                        "name": el.get_attribute("name"),
                        "class": el.get_attribute("class"),
                        "type": el.get_attribute("type"),
                        "placeholder": el.get_attribute("placeholder"),
                        "value": el.get_attribute("value"),
                        "href": el.get_attribute("href"),
                        "src": el.get_attribute("src"),
                        "alt": el.get_attribute("alt"),
                        "aria_label": el.get_attribute("aria-label"),
                        "data_test": el.get_attribute("data-test"),
                        "page": page_name,
                        "url": self.driver.current_url,
                        "collected_at": datetime.now().isoformat()
                    }
                    
                    # Очищаем None значения
                    attributes = {k: v for k, v in attributes.items() if v is not None}
                    elements_info.append(attributes)
                    
            except Exception as e:
                self.logger.warning(f"Ошибка при сборе элементов тега {tag}: {e}")
                continue
                
        self.all_page_elements[page_name] = elements_info
        self.logger.info(f"Собрано {len(elements_info)} элементов со страницы {page_name}")
        return elements_info

    def execute_action(self, action_info, page_name):
        """
        Выполняет одно действие из сценария.
        """
        action_type = action_info.get("action", "")
        target = action_info.get("target", "")
        value = action_info.get("value", "")
        description = action_info.get("description", "")
        
        self.logger.info(f"Выполнение действия: {action_type} -> {target} | Значение: {value}")
        
        try:
            if action_type == "navigate":
                self.driver.get(target)
                self.wait_for_page_load()
                self.log_page_transition(page_name, "new_page", f"Переход по URL: {target}")
                return "new_page"
                
            elif action_type == "click":
                # Ищем элемент для клика по различным стратегиям
                element = self.find_element_by_description(target)
                if element:
                    element.click()
                    self.wait_for_page_load()
                    new_page_name = f"page_after_click_{len(self.all_page_elements)}"
                    self.log_page_transition(page_name, new_page_name, f"Клик: {description}")
                    return new_page_name
                else:
                    self.logger.error(f"Не удалось найти элемент для клика: {target}")
                    
            elif action_type == "type":
                element = self.find_element_by_description(target)
                if element:
                    element.clear()
                    element.send_keys(value)
                    self.logger.info(f"Введено значение: {value} в поле: {target}")
                    return page_name  # Остаемся на той же странице
                else:
                    self.logger.error(f"Не удалось найти элемент для ввода: {target}")
                    
            elif action_type == "wait":
                time.sleep(int(value) if value else 2)
                self.logger.info(f"Ожидание {value} секунд")
                return page_name
                
        except Exception as e:
            self.logger.error(f"Ошибка при выполнении действия {action_type}: {e}")
            
        return page_name

    def find_element_by_description(self, description):
        """
        Находит элемент на странице по описанию из сценария.
        Использует LLM для определения лучшего локатора.
        """
        current_elements = self.collect_page_elements("temp")
        
        prompt = (
            "Ты — эксперт по Selenium. "
            "Найди наиболее подходящий HTML элемент на странице по описанию. "
            "Верни ТОЛЬКО JSON в формате: "
            '{"locator_type": "id|name|xpath|css|class|text", "locator_value": "string"}'
            f"Описание элемента: {description}\n"
            f"Доступные элементы на странице (JSON):\n{json.dumps(current_elements[:30], ensure_ascii=False)}\n"
            "Ответ только в формате JSON:"
        )
        
        try:
            output = self.llm(prompt, max_tokens=512, stop=["\n\n"])
            cleaned_output = self._clean_generated_code(output['choices'][0]['text'])
            
            match = re.search(r'\{.*\}', cleaned_output, re.DOTALL)
            if match:
                locator_info = json.loads(match.group(0))
                locator_type = locator_info.get("locator_type", "")
                locator_value = locator_info.get("locator_value", "")
                
                return self.find_element_by_locator(locator_type, locator_value)
                
        except Exception as e:
            self.logger.error(f"Ошибка при поиске элемента по описанию '{description}': {e}")
            
        return None

    def find_element_by_locator(self, locator_type, locator_value):
        """
        Находит элемент по типу локатора и значению.
        """
        if not locator_value:
            return None
            
        try:
            if locator_type == "id":
                return self.wait_for_element(By.ID, locator_value)
            elif locator_type == "name":
                return self.wait_for_element(By.NAME, locator_value)
            elif locator_type == "xpath":
                return self.wait_for_element(By.XPATH, locator_value)
            elif locator_type == "css":
                return self.wait_for_element(By.CSS_SELECTOR, locator_value)
            elif locator_type == "class":
                return self.wait_for_element(By.CLASS_NAME, locator_value)
            elif locator_type == "text":
                return self.wait_for_element(By.XPATH, f"//*[contains(text(), '{locator_value}')]")
            elif locator_type == "tag":
                return self.wait_for_element(By.TAG_NAME, locator_value)
        except Exception as e:
            self.logger.error(f"Ошибка поиска элемента {locator_type}={locator_value}: {e}")
            
        return None

    def execute_scenario_actions(self, scenario_info):
        """
        Выполняет все действия сценария и собирает элементы со всех страниц.
        """
        initial_url = scenario_info.get("initial_url")
        actions = scenario_info.get("actions", [])
        
        if not initial_url:
            raise ValueError("Не удалось определить начальный URL из сценария")

        # Начинаем с начальной страницы
        self.driver.get(initial_url)
        self.wait_for_page_load()
        current_page = "initial_page"
        self.collect_page_elements(current_page)
        
        self.logger.info(f"Начало выполнения сценария с URL: {initial_url}")
        
        # Выполняем все действия по порядку
        for i, action in enumerate(actions):
            self.logger.info(f"Выполнение действия {i+1}/{len(actions)}")
            new_page = self.execute_action(action, current_page)
            
            if new_page != current_page:
                # Если произошел переход на новую страницу, собираем элементы
                current_page = new_page
                self.collect_page_elements(current_page)
                
            # Небольшая пауза между действиями
            time.sleep(1)
        
        self.logger.info("Все действия сценария выполнены")
        return self.all_page_elements

    def generate_locators(self, scenario_elements, all_page_elements):
        """
        Генерирует локаторы для требуемых элементов со ВСЕХ страниц.
        """
        all_elements_flat = []
        for page_name, elements in all_page_elements.items():
            for element in elements:
                element["source_page"] = page_name
                all_elements_flat.append(element)

        prompt = (
            "Ты — эксперт по Selenium. "
            "Тебе дан список требуемых элементов для автотеста из сценария (с указанием страницы) "
            "и список html элементов, найденных на ВСЕХ страницах (в виде JSON). "
            "Для каждого требуемого элемента из сценария найди наиболее подходящий элемент "
            "на соответствующей странице и сформируй лучший Selenium локатор для него. "
            "Верни ТОЛЬКО JSON без дополнительного текста, в формате: \n"
            '[\n'
            '{\n'
            '    "required_element": {\n'
            '    "name": "...",\n'
            '    "description": "...",\n'
            '    "page": "..."\n'
            '    },\n'
            '    "locator": {\n'
            '    "type": "By.ID|By.CSS_SELECTOR|By.NAME|By.XPATH|By.CLASS_NAME|By.LINK_TEXT",\n'
            '    "value": "...",\n'
            '    "reasoning": "...",\n'
            '    "page_url": "...",\n'
            '    "page_name": "..."\n'
            '    }\n'
            '}\n'
            ']\n'
            f"Список требуемых элементов (JSON):\n{json.dumps(scenario_elements, ensure_ascii=False)}\n"
            f"Список элементов на ВСЕХ страницах (JSON):\n{json.dumps(all_elements_flat[:100], ensure_ascii=False)}\n"
        )
        
        print("=== MODEL INPUT (generate_locators) ===")
        print(prompt)
        print("=== END MODEL INPUT ===")

        output = self.llm(prompt, max_tokens=4096, stop=["\n\n"])
        
        print("=== MODEL OUTPUT (generate_locators) ===")
        locators = self._clean_generated_code(output['choices'][0]['text'])
        print(locators)
        print("=== END MODEL OUTPUT ===")
        
        return locators

    def _clean_generated_code(self, code: str) -> str:
        """
        Очищает сгенерированный код от управляющих токенов и артефактов.
        """
        if not code:
            return ""
        lines = code.split('\n')
        cleaned_lines = [
            line for line in lines
            if not any(artifact in line for artifact in ['[INST]', '<<SYS>>', '[/INST]', '<s>', '</s>'])
            and line.strip() not in ['```java', '```','```json']
        ]
        return '\n'.join(cleaned_lines).strip()

    def save_results(self, result):
        """Сохраняет результаты в файл"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "action_history": self.action_history,
            "collected_elements": self.all_page_elements,
            "generated_locators": result,
            "summary": {
                "pages_visited": len(self.all_page_elements),
                "total_elements_collected": sum(len(elements) for elements in self.all_page_elements.values()),
                "total_actions_performed": len(self.action_history)
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Результаты сохранены в файл: {filename}")
        return filename

    def run(self, test_scenario):
        """Основной метод выполнения сценария"""
        try:
            # 1. Анализируем сценарий
            scenario_info = self.analyze_scenario(test_scenario)
            
            # 2. Настраиваем драйвер
            self.setup_driver()
            
            # 3. Выполняем действия сценария и собираем элементы
            all_page_elements = self.execute_scenario_actions(scenario_info)
            
            # 4. Логируем собранную информацию
            required_elements = scenario_info.get("required_elements", [])
            self.logger.info(f"Найдено страниц: {len(all_page_elements)}")
            self.logger.info(f"Требуемых элементов: {len(required_elements)}")
            
            # 5. Генерируем локаторы
            elements_with_locators = self.generate_locators(required_elements, all_page_elements)
            
            # 6. Сохраняем результаты
            result_file = self.save_results(elements_with_locators)
            
            return {
                "locators": elements_with_locators,
                "action_history": self.action_history,
                "result_file": result_file
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при выполнении сценария: {e}")
            raise
        finally:
            self.close()

    def close(self):
        """Закрытие драйвера и завершение работы"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Веб-драйвер закрыт")
            except Exception as e:
                self.logger.error(f"Ошибка при закрытии драйвера: {e}")

# Пример использования:
if __name__ == "__main__":
    GGUF_MODEL_PATH = "C:\\Users\\apors\\AI\\AFT_Agent\\models\\DeepSeek-Coder-V2-Lite-Instruct-Q4_K_M.gguf"
    TEST_SCENARIO = """
Открыть страницу https://www.saucedemo.com, 
заполнить поле пользователь значением standard_user, 
заполнить поле пароль значением secret_sauce, 
нажать кнопку входа, 
проверить что вход выполнен успешно,
добавить в корзину товар Sauce Labs Backpack,
убедиться что товар добавлен в корзину.
"""

    finder = LocalAILocatorFinder(GGUF_MODEL_PATH)
    try:
        result = finder.run(TEST_SCENARIO)
        print("=== ФИНАЛЬНЫЙ РЕЗУЛЬТАТ ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        finder.close()