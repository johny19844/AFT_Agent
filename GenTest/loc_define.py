import os
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

from llama_cpp import Llama

class LocalAILocatorFinder:
    def __init__(self, gguf_model_path):
        self.gguf_model_path = gguf_model_path
        self.llm = Llama(model_path=gguf_model_path, n_ctx=4096)
        self.driver = None

    def setup_driver(self):
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        service = ChromeService()
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)

    def analyze_scenario(self, test_scenario):
        prompt = (
            "Ты — помощник по автоматизации тестирования. "
            "На вход тебе дается тестовый сценарий. "
            "Определи url страницы входа и какие требуются элементы для создания авто-теста "
            "(например: поле ввода логина, поле ввода пароля, кнопка войти и т.д.). "
            "Верни JSON вида: "
            '{"url": "...", "required_elements": [{"name": "...", "description": "..."}]}.\n\n'
            f"Тестовый сценарий:\n{test_scenario}\n"
        )
        # Для отладки: выводим промпт в консоль
        print("=== PROMPT TO MODEL (analyze_scenario) ===")
        print(prompt)
        print("=== END PROMPT ===")
        output = self.llm(prompt, max_tokens=512, stop=["\n\n"])
        # Для отладки: выводим результат работы модели в консоль
        print("=== MODEL OUTPUT (analyze_scenario) ===")
        print(output['choices'][0]['text'])
        print("=== END MODEL OUTPUT ===")
        # Попробуем найти JSON в ответе
        match = re.search(r'\{.*\}', output['choices'][0]['text'], re.DOTALL)
        if match:
            try:
                scenario_info = json.loads(match.group(0))
                return scenario_info
            except Exception:
                pass
        raise ValueError("Не удалось получить корректный JSON из ответа Llama")

    def collect_page_elements(self, url):
        """
        Собирает информацию о всех видимых элементах на странице.
        Возвращает список словарей с основной информацией.
        """
        self.driver.get(url)
        elements_info = []
        # Собираем input, button, a, form, label, select, textarea, div, span
        tags = ['input', 'button', 'a', 'form', 'label', 'select', 'textarea', 'div', 'span']
        for tag in tags:
            try:
                found = self.driver.find_elements(By.TAG_NAME, tag)
                for el in found:
                    if not el.is_displayed():
                        continue
                    info = {
                        "tag": tag,
                        "text": el.text.strip(),
                        "id": el.get_attribute("id"),
                        "name": el.get_attribute("name"),
                        # "class": el.get_attribute("class"),
                        # "type": el.get_attribute("type"),
                        # "placeholder": el.get_attribute("placeholder"),
                        "value": el.get_attribute("value"),
                        # "aria_label": el.get_attribute("aria-label"),
                        # "data_test": el.get_attribute("data-test"),
                        # "outer_html": el.get_attribute("outerHTML")[:500]
                    }
                    elements_info.append(info)
            except Exception:
                continue
        return elements_info

    def generate_locators(self, scenario_elements, page_elements):
        """
        Возвращает список элементов с локаторами за одно обращение к ИИ.
        """
        prompt = (
            "Ты — эксперт по Selenium. "
            "Тебе дан список требуемых элементов для автотеста и список элементов, найденных на странице (оба в виде JSON). "
            "Для каждого требуемого элемента найди наиболее подходящий элемент на странице и предложи лучший Selenium локатор для него. "
            "Верни JSON-массив, где для каждого требуемого элемента есть объект вида: "
            '{"element": {...}, "element_found": true/false, '
            '"locators": [{"type": "ID|CSS|XPATH|NAME", "value": "...", "confidence": 0.95, "explanation": "..."}], '
            '"reasoning": "..."}.\n\n'
            f"Список требуемых элементов (JSON):\n{json.dumps(scenario_elements, ensure_ascii=False)}\n"
            f"Список элементов на странице (JSON):\n{json.dumps(page_elements[:20], ensure_ascii=False)}\n"
        )
        output = self.llm(prompt, max_tokens=2048, stop=["\n\n"])
        # Попробуем найти JSON-массив в ответе
        match = re.search(r'\[.*\]', output['choices'][0]['text'], re.DOTALL)
        if match:
            try:
                locators_list = json.loads(match.group(0))
                # Проверяем, что это список и элементы имеют нужную структуру
                results = []
                for idx, elem in enumerate(scenario_elements):
                    locator_info = None
                    # Найти соответствующий объект по "element" или по индексу
                    if isinstance(locators_list, list) and idx < len(locators_list):
                        locator_info = locators_list[idx]
                    if locator_info and isinstance(locator_info, dict):
                        # Оставляем только первый (надежный) локатор, если есть
                        best_locator = None
                        if isinstance(locator_info.get("locators"), list) and locator_info["locators"]:
                            best_locator = locator_info["locators"][0]
                        results.append({
                            "element": elem,
                            "locator": best_locator if best_locator else {"error": "Локатор не найден"},
                            "reasoning": locator_info.get("reasoning", "")
                        })
                    else:
                        results.append({
                            "element": elem,
                            "locator": {"error": "AI не вернул корректный JSON"},
                            "reasoning": ""
                        })
                return results
            except Exception:
                pass
        # Если не удалось распарсить корректно
        results = []
        for elem in scenario_elements:
            results.append({
                "element": elem,
                "locator": {"error": "AI не вернул корректный JSON"},
                "reasoning": ""
            })
        return results

    def run(self, test_scenario):
        # 1. Анализируем сценарий
        scenario_info = self.analyze_scenario(test_scenario)
        url = scenario_info.get("url")
        required_elements = scenario_info.get("required_elements", [])
        if not url or not required_elements:
            raise ValueError("Не удалось определить url или элементы из сценария")

        # 2. Собираем элементы страницы
        self.setup_driver()
        page_elements = self.collect_page_elements(url)
        print(f"Найденная в сценарии информация: \n {json.dumps(required_elements, ensure_ascii=False, indent=2)}")
        print(f"Найденные на странице элементы:\n {json.dumps(page_elements, ensure_ascii=False, indent=2)}")
        # 3. Генерируем локаторы для требуемых элементов
        elements_with_locators = self.generate_locators(required_elements, page_elements)
        return elements_with_locators

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

# Пример использования:
if __name__ == "__main__":
    # Путь к вашей gguf модели
    GGUF_MODEL_PATH = "C:\\Users\\apors\\AI\\AFT_Agent\\models\\DeepSeek-Coder-V2-Lite-Instruct-Q4_K_M.gguf"
    TEST_SCENARIO = """
1. Открыть страницу https://demoqa.com/text-box
2. Заполнить форму данными:
Full Name: "Иван Петров"
Email: "ivan.petrov@example.com"
Current Address: "Москва, ул. Примерная, д. 1"
Permanent Address: "Санкт-Петербург, ул. Тестовая, д. 2"
3. Нажать кнопку "Submit"
4. Проверить, что данные отобразились в блоке результата
5. Убедиться, что все введенные значения корректно отображены в блоке результата
"""

    finder = LocalAILocatorFinder(GGUF_MODEL_PATH)
    try:
        result = finder.run(TEST_SCENARIO)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        finder.close()
