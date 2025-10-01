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
        """
        Анализирует текст сценария, извлекает url и список требуемых элементов.
        Использует LLM для парсинга сценария.
        """
        prompt = (
            "Ты — помощник по автоматизации тестирования. "
            "На вход тебе дается тестовый сценарий. "
            "Определи url страницы входа и какие требуются элементы для создания авто-теста "
            "(например: поле ввода логина, поле ввода пароля, кнопка войти и т.д.). "
            "Верни ТОЛЬКО JSON без дополнительного текста в формате: "
            '{"url": "string", "required_elements": [{"name": "string", "description": "string"}]}.\n\n'
            f"Тестовый сценарий:\n{test_scenario}\n"
            "Ответ только в формате JSON:"
        )
        # Для отладки: выводим промпт в консоль
        print("=== PROMPT TO MODEL (analyze_scenario) ===")
        print(prompt)
        print("=== END PROMPT ===")
        output = self.llm(prompt, max_tokens=512, stop=["\n\n"])
        # Для отладки: выводим результат работы модели в консоль
        print("=== MODEL OUTPUT (analyze_scenario) ===")
        rez = self._clean_generated_code(output['choices'][0]['text'])
        print(rez)
        print("=== END MODEL OUTPUT ===")
        # Пытаемся найти JSON в ответе модели
        match = re.search(r'\{.*\}', output['choices'][0]['text'], re.DOTALL)
        if match:
            try:
                scenario_info = json.loads(match.group(0))
                return scenario_info
            except Exception:
                pass
        # Если не удалось получить корректный JSON — выбрасываем ошибку
        raise ValueError("Не удалось получить корректный JSON из ответа Llama")

    def collect_page_elements(self, url):
        """
        Собирает информацию о всех видимых элементах на странице.
        Возвращает список словарей с основной информацией.
        """
        self.driver.get(url)
        elements_info = []
        # Список тегов, которые нас интересуют для поиска элементов
        tags = ['input', 'button', 'a', 'select', 'textarea', 'div', 'span']
        for tag in tags:
            try:
                found = self.driver.find_elements(By.TAG_NAME, tag)
                for el in found:
                    if not el.is_displayed():
                        continue  # Пропускаем невидимые элементы
                    info = {
                        "tag": tag,
                        "text": el.text.strip(),
                        "id": el.get_attribute("id"),
                        "name": el.get_attribute("name"),
                        # "class": el.get_attribute("class"),
                        # "type": el.get_attribute("type"),
                        # "placeholder": el.get_attribute("placeholder"),
                        #"value": el.get_attribute("value"),
                        # "aria_label": el.get_attribute("aria-label"),
                        # "data_test": el.get_attribute("data-test"),
                        # "outer_html": el.get_attribute("outerHTML")[:500]
                    }
                    elements_info.append(info)
            except Exception:
                continue  # Игнорируем ошибки для отдельных тегов
        return elements_info

    def generate_locators(self, scenario_elements, page_elements):
        """
        Генерирует локаторы для требуемых элементов, используя LLM.
        Возвращает список элементов с локаторами.
        """
        prompt = (
            "Ты — эксперт по Selenium. "
            "Тебе дан список требуемых элементов для автотеста из сценария и список html элементов, найденных на странице (оба в виде JSON). "
            "Для каждого требуемого элемента из сценария найди наиболее подходящий элемент на html странице и сформируй лучший Selenium локатор для него (приоритет отдавай ID если на странице он уникален). "
            "Верни ТОЛЬКО JSON без дополнительного текста, в формате: \n"
            '[\n'
            '{\n'
            '    "required_element": {\n'
            '    "name": "...",\n'
            '    "description": "..."\n'
            '    },\n'
            '    "locator": {\n'
            '    "type": "By.ID|By.cssSelector|By.name|By.xpath|",\n'
            '    "value": "...",\n'
            '    "reasoning": "..."\n'
            '    }\n'
            '}\n'
            ']\n'
            f"Список требуемых элементов (JSON):\n{json.dumps(scenario_elements, ensure_ascii=False)}\n"
            f"Список элементов на странице (JSON):\n{json.dumps(page_elements[:20], ensure_ascii=False)}\n"
        )
        output = self.llm(prompt, max_tokens=2048, stop=["\n\n"])
        # Для отладки: выводим входные и выходные данные модели
        print("=== MODEL INPUT (generate_locators) ===")
        print(prompt)
        print("=== END MODEL INPUT ===")

        print("=== MODEL OUTPUT (generate_locators) ===")
        locators = self._clean_generated_code(output['choices'][0]['text'])
        print(locators)
        print("=== END MODEL OUTPUT ===")
        # Возвращаем результат (можно добавить парсинг JSON при необходимости)
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
Открыть страницу https://www.saucedemo.com, 
заполнить поле пользователь значением standard_user, 
заполнить поле пароль значением secret_sauce, 
нажать кнопку входа, 
проверить что вход выполнен успешно,
добавить в корзину товар,
убедиться что товар добавлен в корзину.
"""

    finder = LocalAILocatorFinder(GGUF_MODEL_PATH)
    try:
        result = finder.run(TEST_SCENARIO)
        print(result) #json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        finder.close()
